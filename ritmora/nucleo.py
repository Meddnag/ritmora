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
# config.json: "tema" e "canal_atual" valem para o Ritmora todo; cada canal tem a sua repartição em "canais".
PADRAO_CANAL = {
    "pasta_fila": "",
    "horarios": {"youtube": "12:00", "tiktok": "19:00", "instagram": "18:00"},
    "intervalo_dias": 1,
    "modo": {"youtube": "assistido", "tiktok": "assistido", "instagram": "assistido"},
    "navegador": "",
}
CORES_CANAL = ["#3a6bff", "#ff7a3d", "#3dffa0", "#e07bff", "#5ce1ff", "#ffc857", "#ff5c8a", "#9b8cff"]
CHAVES_ANTIGAS = ("pasta_fila", "horarios", "intervalo_dias", "modo", "navegador", "token_extensao", "canal")
ARQUIVOS_CANAL = ("youtube_token.json", "canal.json", "canal_foto.jpg")


def pasta_canal(cid):
    """Pasta da repartição do canal: login do YouTube, nome e foto do canal conectado."""
    p = os.path.join(DADOS, "canais", str(cid))
    os.makedirs(p, exist_ok=True)
    return p


def _completar(c):
    for k, v in PADRAO_CANAL.items():
        if k not in c:
            c[k] = json.loads(json.dumps(v))
        elif isinstance(v, dict):
            c[k] = {**v, **c[k]}
    return c


def _migrar(cfg):
    """Ritmora de um canal só -> repartições. O canal que já existia vira o canal 1, com seus arquivos e sua chave."""
    um = {"id": 1, "nome": cfg.get("canal") or "Meu canal", "cor": CORES_CANAL[0]}
    for k in CHAVES_ANTIGAS:
        if k in cfg and k != "canal":
            um[k] = cfg[k]
    for k in CHAVES_ANTIGAS:
        cfg.pop(k, None)
    destino = pasta_canal(1)
    for nome in ARQUIVOS_CANAL:
        antigo = os.path.join(DADOS, nome)
        if os.path.exists(antigo) and not os.path.exists(os.path.join(destino, nome)):
            shutil.move(antigo, os.path.join(destino, nome))
    arq = os.path.join(destino, "canal.json")
    if os.path.exists(arq):
        try:
            d = json.load(open(arq, encoding="utf-8"))
            if d.get("foto"):
                d["foto"] = os.path.join(destino, "canal_foto.jpg")
                json.dump(d, open(arq, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass
    cfg["canais"] = [um]
    cfg["canal_atual"] = 1


def carregar_cfg():
    cfg = {"tema": "cobalto"}
    if os.path.exists(ARQ_CFG):
        try:
            cfg.update(json.load(open(ARQ_CFG, encoding="utf-8")))
        except Exception:
            pass
    if not cfg.get("canais"):
        _migrar(cfg)
        salvar_cfg(cfg)
    for c in cfg["canais"]:
        _completar(c)
    if not any(c["id"] == cfg.get("canal_atual") for c in cfg["canais"]):
        cfg["canal_atual"] = cfg["canais"][0]["id"]
    return cfg


def salvar_cfg(cfg):
    json.dump(cfg, open(ARQ_CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def canal(cfg, cid):
    """Configuração da repartição de um canal (o próprio dicionário dentro de cfg)."""
    return next((c for c in cfg["canais"] if c["id"] == cid), cfg["canais"][0])


def novo_canal(cfg, nome):
    cid = max(c["id"] for c in cfg["canais"]) + 1
    base = canal(cfg, cfg.get("canal_atual"))
    c = _completar({"id": cid, "nome": nome, "cor": CORES_CANAL[(cid - 1) % len(CORES_CANAL)],
                    "horarios": dict(base["horarios"]), "intervalo_dias": base["intervalo_dias"],
                    "navegador": base.get("navegador", "")})
    cfg["canais"].append(c)
    salvar_cfg(cfg)
    pasta_canal(cid)
    return cid


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
        if "canal" not in [r[1] for r in self.con.execute("PRAGMA table_info(posts)")]:
            self.con.execute("ALTER TABLE posts ADD COLUMN canal INTEGER DEFAULT 1")
            self.con.execute("UPDATE posts SET canal = 1 WHERE canal IS NULL")
        self.con.commit()

    # ------------------------------------------------------------ consultas
    def todos(self, filtro=None, canal=None):
        q = "SELECT * FROM posts"
        cond, args = [], []
        if filtro and filtro != "todos":
            cond.append("status = ?")
            args.append(filtro)
        if canal is not None:
            cond.append("canal = ?")
            args.append(canal)
        if cond:
            q += " WHERE " + " AND ".join(cond)
        q += " ORDER BY COALESCE(quando, criado)"
        return [dict(r) for r in self.con.execute(q, tuple(args))]

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

    def contar_canal(self, cid):
        return self.con.execute("SELECT COUNT(*) FROM posts WHERE canal = ?", (cid,)).fetchone()[0]

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


def proximo_horario(banco, rede, cc, depois=None):
    """Próximo horário livre da rede neste canal, respeitando o horário padrão e o intervalo entre posts."""
    hh, mm = map(int, cc["horarios"].get(rede, "12:00").split(":"))
    ocupados = {p["quando"][:10] for p in banco.todos(canal=cc["id"]) if p["rede"] == rede and p["quando"] and p["status"] not in ("reprovado", "erro")}
    d = (depois or datetime.now()).replace(hour=hh, minute=mm, second=0, microsecond=0)
    if d <= datetime.now():
        d += timedelta(days=1)
    while d.date().isoformat() in ocupados:
        d += timedelta(days=max(1, int(cc.get("intervalo_dias", 1))))
    return d.isoformat(timespec="minutes")


# ---------------------------------------------------------------- fila de produção
def importar_fila(banco, cc):
    """Lê <pasta_fila do canal>/<projeto>/post.json e cria um post por rede nesse canal. Importados vão para <pasta_fila>/_importados."""
    raiz = cc.get("pasta_fila") or ""
    if not raiz:
        return 0, [f"Escolha a pasta da fila de “{cc['nome']}” em Configurações."]
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
                        quando=r.get("quando") or proximo_horario(banco, rede, cc), pasta=pasta,
                        ia=d.get("ia_sugerido"), criancas=None, canal=cc["id"])
            criados += 1
        destino = os.path.join(raiz, "_importados")
        os.makedirs(destino, exist_ok=True)
        try:
            shutil.move(pasta, os.path.join(destino, nome))
            for p in banco.todos(canal=cc["id"]):
                if p["pasta"] == pasta:
                    novo = os.path.join(destino, nome)
                    banco.atualizar(p["id"], video=p["video"].replace(pasta, novo),
                                    thumb=p["thumb"].replace(pasta, novo) if p["thumb"] else None, pasta=novo)
        except Exception as e:
            avisos.append(f"{nome}: não consegui mover para _importados ({e})")
    return criados, avisos
