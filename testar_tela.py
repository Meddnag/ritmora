# Teste visual do Ritmora: monta dados de exemplo em uma pasta temporária e salva capturas em .impeccable/review/.
#   .venv\Scripts\python testar_tela.py [tema]
import os, shutil, sys, tempfile
from datetime import datetime, timedelta

tmp = tempfile.mkdtemp(prefix="ritmora_teste_", dir=r"D:\PROJETOS IA\jogos\canal-shorts\build\tmp")
from ritmora import nucleo as N
N.DADOS = tmp
N.ARQ_CFG = os.path.join(tmp, "config.json")
cfg = N.carregar_cfg()
cfg["tema"] = sys.argv[1] if len(sys.argv) > 1 else "cobalto"
cfg["pasta_fila"] = os.path.join(tmp, "fila")
N.salvar_cfg(cfg)
# copia o item real da fila (sem mexer na fila verdadeira)
shutil.copytree(r"D:\PROJETOS IA\jogos\canal-shorts\fila\knull-top5", os.path.join(tmp, "fila", "knull-top5"))

from PySide6.QtWidgets import QApplication
from ritmora import ui
from ritmora.tema import definir_destaque, estilo
app = QApplication(sys.argv)
definir_destaque(cfg["tema"])
app.setStyleSheet(estilo())
N.Banco.__init__.__defaults__ = (os.path.join(tmp, "ritmora.db"),)
j = ui.Janela()
j.resize(1440, 900)
j.show()
N.importar_fila(j.db, j.cfg)
cs = r"D:\PROJETOS IA\jogos\canal-shorts"
hoje = datetime.now().replace(second=0, microsecond=0)


def q(d, h):
    return (hoje + timedelta(days=d)).replace(hour=h, minute=0).isoformat(timespec="minutes")


j.db.criar(projeto="Doomguy", rede="youtube", formato="longo", titulo="A HISTÓRIA DO DOOMGUY: do bebê ao auge", descricao="", tags="",
           video=cs + r"\doomguy-historia\doomguy_historia.mp4", thumb=cs + r"\doomguy-historia\thumbnail_doomguy.jpg", quando=q(2, 12),
           pasta=cs, ia=None, criancas=None)
pid = j.db.criar(projeto="Surfista", rede="instagram", formato="short", titulo="5 jeitos ridículos de derrotar o Surfista", descricao="",
                 tags="", video=cs + r"\surfista-top5\derrotar_surfista.mp4", thumb=None, quando=q(0, 9), pasta=cs, ia=0, criancas=None)
j.db.atualizar(pid, None, status="na_hora")
pid = j.db.criar(projeto="Carnificina", rede="youtube", formato="short", titulo="5 jeitos ridículos de derrotar o Carnificina",
                 descricao="", tags="", video=cs + r"\carnificina-top5\derrotar_carnificina.mp4", thumb=None, quando=q(3, 12), pasta=cs, ia=1,
                 criancas=0)
j.db.atualizar(pid, None, status="aprovado")
pid = j.db.criar(projeto="Doomguy curto", rede="tiktok", formato="short", titulo="Doomguy em 1 minuto", descricao="", tags="",
                 video=cs + r"\doomguy-historia\curto\doomguy_short.mp4", thumb=None, quando=q(1, 19), pasta=cs, ia=1, criancas=None)
j.db.atualizar(pid, None, status="publicado")
j.recarregar()
alvo = [p for p in j.db.todos() if p["rede"] == "tiktok" and p["status"] == "aguardando"][0]
j.escolher_id(alvo["id"])
for _ in range(40):
    app.processEvents()
os.makedirs(".impeccable/review", exist_ok=True)
sufixo = "" if cfg["tema"] == "cobalto" else "_" + cfg["tema"]
for nome, (w, h) in (("desktop", (1440, 900)), ("laptop", (1280, 760))):
    j.resize(w, h)
    for _ in range(40):
        app.processEvents()
    img = j.grab()
    assert (img.width(), img.height()) == (w, h), f"{nome}: {img.width()}x{img.height()}"
    img.save(f".impeccable/review/{nome}{sufixo}.png")
j.ir(1)
for _ in range(20):
    app.processEvents()
img = j.grab()
assert (img.width(), img.height()) == (1280, 760), f"fila: {img.width()}x{img.height()}"
img.save(f".impeccable/review/fila{sufixo}.png")
j.bandeja.hide()
shutil.rmtree(tmp, ignore_errors=True)
print("ok")
