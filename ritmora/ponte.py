# Ritmora: ponte local com a extensão do navegador ("Ritmora Ajudante").
# Servidor HTTP só em 127.0.0.1, protegido por chaves (tokens) que a pessoa cola na extensão.
# Cada canal tem a sua chave: a extensão de um navegador/perfil só vê e abre os posts do canal cuja chave recebeu.
# Aceita só pedidos de extensões (Origin chrome-extension://) ou sem Origin; sites comuns são recusados.
import json, os, secrets, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from . import nucleo as N
from . import redes as R

PORTA = 47321
PEDACO_MAX = 8 * 1024 * 1024
STATUS_VISIVEIS = ("na_hora", "aprovado", "erro")


def token(cfg, cid):
    """chave da extensão do canal; criada na primeira vez e guardada no config.json."""
    c = N.canal(cfg, cid)
    if not c.get("token_extensao"):
        c["token_extensao"] = secrets.token_urlsafe(18)
        N.salvar_cfg(cfg)
    return c["token_extensao"]


def nome_canal(c):
    """Nome mostrado: o do canal conectado no YouTube, se houver; senão o nome dado no Ritmora."""
    return (R.canal_salvo(N.pasta_canal(c["id"])) or {}).get("nome") or c["nome"]


def _resumo(p, ativo):
    def info(caminho):
        if caminho and os.path.isfile(caminho):
            return {"nome": os.path.basename(caminho), "tamanho": os.path.getsize(caminho)}
        return None
    return {"id": p["id"], "projeto": p["projeto"], "rede": p["rede"], "formato": p["formato"], "titulo": p["titulo"] or "",
            "descricao": p["descricao"] or "", "tags": [t.strip() for t in (p["tags"] or "").split(",") if t.strip()],
            "ia": p["ia"], "criancas": p["criancas"], "quando": p["quando"], "status": p["status"],
            "video": info(p["video"]), "thumb": info(p["thumb"]), "ativo": p["id"] == ativo}


class Ponte:
    def __init__(self, cfg, ao_publicar=None):
        self.cfg = cfg
        self.ativo = None          # post aberto agora pelo "Enviar agora"
        self.ao_publicar = ao_publicar
        self.servidor = None
        self.erro = None
        self.visto = {}            # canal -> última vez que a extensão desse canal falou com o Ritmora
        self.pedidos = {}          # canal -> páginas que a extensão desse canal deve abrir
        self.cond = threading.Condition()

    def canal_do_token(self, tok):
        for c in self.cfg["canais"]:
            if tok and c.get("token_extensao") and secrets.compare_digest(tok, c["token_extensao"]):
                return c
        return None

    def extensao_ativa(self, cid, segundos=75):
        return time.time() - self.visto.get(cid, 0) < segundos

    def abrir(self, cid, url):
        """Pede à extensão do canal para abrir a página no navegador (e perfil) onde ela está instalada."""
        with self.cond:
            self.pedidos.setdefault(cid, []).append(url)
            self.cond.notify_all()

    def _esperar_pedidos(self, cid, segundos=20):
        with self.cond:
            self.cond.wait_for(lambda: bool(self.pedidos.get(cid)), timeout=segundos)
            urls, self.pedidos[cid] = self.pedidos.get(cid, []), []
        return urls

    def iniciar(self):
        ponte = self

        class Pedido(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def _responder(self, cod, corpo=b"", tipo="application/json"):
                if isinstance(corpo, (dict, list)):
                    corpo = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
                self.send_response(cod)
                self.send_header("Content-Type", tipo)
                self.send_header("Content-Length", str(len(corpo)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(corpo)

            def _canal(self):
                """canal dono da chave do pedido, ou None (pedido recusado)."""
                origem = self.headers.get("Origin", "")
                if origem and not origem.startswith(("chrome-extension://", "moz-extension://")):
                    return None
                c = ponte.canal_do_token(self.headers.get("X-Ritmora-Token", ""))
                if c:
                    ponte.visto[c["id"]] = time.time()
                return c

            def do_GET(self):
                c = self._canal()
                if not c:
                    return self._responder(403, {"erro": "chave inválida"})
                u = urlparse(self.path)
                q = parse_qs(u.query)
                if u.path == "/comandos":
                    # espera até 20 s por uma página para abrir (a extensão volta a perguntar logo em seguida)
                    urls = ponte._esperar_pedidos(c["id"])
                    ponte.visto[c["id"]] = time.time()
                    return self._responder(200, {"abrir": urls})
                if u.path == "/estado":
                    return self._responder(200, {"ok": True, "canal": nome_canal(c), "ativo": ponte.ativo})
                db = N.Banco()
                try:
                    if u.path == "/posts":
                        rede = q.get("rede", [None])[0]
                        posts = [p for p in db.todos(canal=c["id"]) if p["status"] in STATUS_VISIVEIS and (not rede or p["rede"] == rede)]
                        posts.sort(key=lambda p: (p["id"] != ponte.ativo, p["status"] != "na_hora", p["quando"] or ""))
                        return self._responder(200, [_resumo(p, ponte.ativo) for p in posts])
                    if u.path == "/arquivo":
                        p = db.um(int(q.get("id", ["0"])[0]))
                        if not p or p["canal"] != c["id"]:
                            return self._responder(404, {"erro": "post não encontrado"})
                        qual = q.get("qual", ["video"])[0]
                        caminho = p["video"] if qual == "video" else p["thumb"]
                        if not caminho or not os.path.isfile(caminho):
                            return self._responder(404, {"erro": "arquivo não encontrado"})
                        ini = int(q.get("ini", ["0"])[0])
                        tam = min(int(q.get("tam", [str(PEDACO_MAX)])[0]), PEDACO_MAX)
                        with open(caminho, "rb") as f:
                            f.seek(ini)
                            dados = f.read(tam)
                        return self._responder(200, dados, "application/octet-stream")
                    return self._responder(404, {"erro": "rota desconhecida"})
                finally:
                    db.con.close()

            def do_POST(self):
                c = self._canal()
                if not c:
                    return self._responder(403, {"erro": "chave inválida"})
                try:
                    corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0") or 0)) or b"{}")
                except Exception:
                    return self._responder(400, {"erro": "json inválido"})
                caminho = urlparse(self.path).path
                if caminho not in ("/publicado", "/nota"):
                    return self._responder(404, {"erro": "rota desconhecida"})
                pid = int(corpo.get("id", 0))
                db = N.Banco()
                try:
                    p = db.um(pid)
                    if not p or p["canal"] != c["id"]:
                        return self._responder(404, {"erro": "post não encontrado"})
                    if caminho == "/nota":
                        db.anotar(pid, "Extensão: " + str(corpo.get("texto", ""))[:300])
                        return self._responder(200, {"ok": True})
                    link = (corpo.get("link") or "").strip() or None
                    db.atualizar(pid, "Publicado (avisado pela extensão)" + (f": {link}" if link else ""), status="publicado", link=link)
                finally:
                    db.con.close()
                if ponte.ao_publicar:
                    ponte.ao_publicar(pid)
                return self._responder(200, {"ok": True})

        try:
            self.servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Pedido)
        except OSError as e:
            self.erro = f"porta {PORTA} ocupada ({e})"
            return False
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        return True

    def parar(self):
        if self.servidor:
            self.servidor.shutdown()
