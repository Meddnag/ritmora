# Ritmora: núcleo (configuração, banco SQLite, importação da fila de produção e regras de aprovação).
import json, os, shutil, sqlite3, sys
from datetime import datetime, timedelta

REDES = ("youtube", "tiktok", "instagram")
NOMES_REDE = {"youtube": "YouTube", "tiktok": "TikTok", "instagram": "Instagram"}
STATUS = {
    "aguardando": ("Aguardando aprovação", "#E0A030"),
    "aprovado": ("Aprovado, na agenda", "#3A9AE0"),
    "agendado_rede": ("Agendado na rede", "#5AB0FF"),
    "na_hora": ("Na hora: confirme o envio", "#FF7A3A"),
    "publicado": ("Publicado", "#3AB84F"),
    "reprovado": ("Reprovado", "#888888"),
    "erro": ("Erro", "#E03A3A"),
}


def pasta_base():
    """Pasta do programa: ao lado do .exe (portátil) ou a raiz do projeto quando roda pelo Python."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DADOS = os.path.join(pasta_base(), "dados")
os.makedirs(DADOS, exist_ok=True)
ARQ_CFG = os.path.join(DADOS, "config.json")
PADRAO_CFG = {
    "pasta_fila": r"D:\PROJETOS IA\jogos\canal-shorts\fila",
    "horarios": {"youtube": "12:00", "tiktok": "19:00", "instagram": "18:00"},
    "intervalo_dias": 1,
    "modo": {"youtube": "assistido", "tiktok": "assistido", "instagram": "assistido"},
    "canal": "Escala de Poder",
}


def carregar_cfg():
    cfg = dict(PADRAO_CFG)
    if os.path.exists(ARQ_CFG):
        try:
            cfg.update(json.load(open(ARQ_CFG, encoding="utf-8")))
        except Exception:
            pass
    return cfg


def salvar_cfg(cfg):
    json.dump(cfg, open(ARQ_CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


class Banco:
    def __init__(self, caminho=None):
        self.con = sqlite3.connect(caminho or os.path.join(DADOS, "ritmora.db"), check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.execute("""CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto TEXT, rede TEXT, formato TEXT,
            titulo TEXT, descricao TEXT, tags TEXT,
            video TEXT, thumb TEXT,
            quando TEXT, status TEXT DEFAULT 'aguardando',
            ia INTEGER, criancas INTEGER,
            link TEXT, erro TEXT, pasta TEXT,
            criado TEXT, atualizado TEXT)""")
        self.con.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY AUTOINCREMENT, post INTEGER, quando TEXT, texto TEXT)")
        self.con.commit()

    # ------------------------------------------------------------ consultas
    def todos(self, filtro=None):
        q = "SELECT * FROM posts"
        args = ()
        if filtro and filtro != "todos":
            q += " WHERE status = ?"
            args = (filtro,)
        q += " ORDER BY COALESCE(quando, criado)"
        return [dict(r) for r in self.con.execute(q, args)]

    def um(self, pid):
        r = self.con.execute("SELECT * FROM posts WHERE id = ?", (pid,)).fetchone()
        return dict(r) if r else None

    def vencidos(self, agora=None):
        agora = (agora or datetime.now()).isoformat(timespec="minutes")
        return [dict(r) for r in self.con.execute("SELECT * FROM posts WHERE status = 'aprovado' AND quando <= ?", (agora,))]

    def historico(self, pid):
        return [dict(r) for r in self.con.execute("SELECT * FROM historico WHERE post = ? ORDER BY id DESC", (pid,))]

    # ------------------------------------------------------------ escrita
    def criar(self, **c):
        agora = datetime.now().isoformat(timespec="seconds")
        c.setdefault("status", "aguardando")
        c["criado"] = c["atualizado"] = agora
        cols = ", ".join(c)
        cur = self.con.execute(f"INSERT INTO posts ({cols}) VALUES ({', '.join('?' * len(c))})", tuple(c.values()))
        self.con.commit()
        self.anotar(cur.lastrowid, "Criado a partir da fila")
        return cur.lastrowid

    def atualizar(self, pid, nota=None, **c):
        c["atualizado"] = datetime.now().isoformat(timespec="seconds")
        self.con.execute(f"UPDATE posts SET {', '.join(k + ' = ?' for k in c)} WHERE id = ?", tuple(c.values()) + (pid,))
        self.con.commit()
        if nota:
            self.anotar(pid, nota)

    def apagar(self, pid):
        self.con.execute("DELETE FROM posts WHERE id = ?", (pid,))
        self.con.execute("DELETE FROM historico WHERE post = ?", (pid,))
        self.con.commit()

    def anotar(self, pid, texto):
        self.con.execute("INSERT INTO historico (post, quando, texto) VALUES (?, ?, ?)",
                         (pid, datetime.now().isoformat(timespec="seconds"), texto))
        self.con.commit()


# ---------------------------------------------------------------- regras
def pode_aprovar(p):
    """Devolve a lista do que falta para aprovar (vazia = pode)."""
    falta = []
    if p["ia"] is None:
        falta.append("declarar se tem conteúdo gerado por IA")
    if p["rede"] == "youtube" and p["criancas"] is None:
        falta.append("declarar se é conteúdo para crianças")
    if not p["quando"]:
        falta.append("escolher data e hora")
    if not p["video"] or not os.path.exists(p["video"]):
        falta.append("o arquivo do vídeo não foi encontrado")
    return falta


def proximo_horario(banco, rede, cfg, depois=None):
    """Próximo horário livre da rede, respeitando o horário padrão e o intervalo entre posts."""
    hh, mm = map(int, cfg["horarios"].get(rede, "12:00").split(":"))
    ocupados = {p["quando"][:10] for p in banco.todos() if p["rede"] == rede and p["quando"] and p["status"] not in ("reprovado", "erro")}
    d = (depois or datetime.now()).replace(hour=hh, minute=mm, second=0, microsecond=0)
    if d <= datetime.now():
        d += timedelta(days=1)
    while d.date().isoformat() in ocupados:
        d += timedelta(days=max(1, int(cfg.get("intervalo_dias", 1))))
    return d.isoformat(timespec="minutes")


# ---------------------------------------------------------------- fila de produção
def importar_fila(banco, cfg):
    """Lê <pasta_fila>/<projeto>/post.json e cria um post por rede. Projetos importados vão para <pasta_fila>/_importados."""
    raiz = cfg["pasta_fila"]
    if not os.path.isdir(raiz):
        return 0, [f"Pasta da fila não existe: {raiz}"]
    criados, avisos = 0, []
    for nome in sorted(os.listdir(raiz)):
        pasta = os.path.join(raiz, nome)
        arq = os.path.join(pasta, "post.json")
        if nome.startswith("_") or not os.path.isfile(arq):
            continue
        try:
            d = json.load(open(arq, encoding="utf-8"))
        except Exception as e:
            avisos.append(f"{nome}: post.json inválido ({e})")
            continue
        for rede, r in d.get("redes", {}).items():
            if rede not in REDES:
                continue
            video = os.path.join(pasta, r.get("video") or d.get("video", ""))
            thumb = r.get("thumb") or d.get("thumb")
            banco.criar(projeto=d.get("projeto", nome), rede=rede, formato=r.get("formato", d.get("formato", "short")),
                        titulo=r.get("titulo", ""), descricao=r.get("descricao") or r.get("legenda", ""),
                        tags=", ".join(r.get("tags", [])), video=video, thumb=os.path.join(pasta, thumb) if thumb else None,
                        quando=r.get("quando") or proximo_horario(banco, rede, cfg), pasta=pasta,
                        ia=d.get("ia_sugerido"), criancas=None)
            criados += 1
        destino = os.path.join(raiz, "_importados")
        os.makedirs(destino, exist_ok=True)
        try:
            shutil.move(pasta, os.path.join(destino, nome))
            for p in banco.todos():
                if p["pasta"] == pasta:
                    novo = os.path.join(destino, nome)
                    banco.atualizar(p["id"], video=p["video"].replace(pasta, novo),
                                    thumb=p["thumb"].replace(pasta, novo) if p["thumb"] else None, pasta=novo)
        except Exception as e:
            avisos.append(f"{nome}: não consegui mover para _importados ({e})")
    return criados, avisos
