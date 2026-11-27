# Ritmora: interface (PySide6), mundo "Grade de Programação". Faixa marinho no topo, a semana como grade de canais,
# a gaveta do post escolhido embaixo (revisão, declarações e aprovação), bandeja do Windows e relógio de 30 s.
import os, sys, traceback
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDateTime, QUrl, QSize, QRectF, QItemSelectionModel
from PySide6.QtGui import QIcon, QPixmap, QAction, QFont, QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidget,
                               QListWidgetItem, QLineEdit, QPlainTextEdit, QDateTimeEdit, QRadioButton, QButtonGroup, QComboBox,
                               QFileDialog, QMessageBox, QDialog, QFormLayout, QSpinBox, QSystemTrayIcon, QMenu, QFrame,
                               QInputDialog, QDialogButtonBox, QTimeEdit, QStackedWidget, QSplitter, QSizePolicy)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from . import nucleo as N
from . import redes as R
from . import navegador as NAV
from . import ponte as P
from .tema import COR, estilo, definir_destaque, CORES_DESTAQUE, fonte_tv, fonte_ui, cor_rede
from .mascote import Rito, pixmap_rito
from .capa import Capa
from . import led
from .grade import Grade, desenhar_marca, STATUS_CURTO


PASTA_EXTENSAO = os.path.join(N.pasta_base(), "extensao")


def icone_app():
    aqui = os.path.dirname(os.path.abspath(__file__))
    for base in (aqui, os.path.join(getattr(sys, "_MEIPASS", aqui), "ritmora")):
        p = os.path.join(base, "ritmora.ico")
        if os.path.exists(p):
            return QIcon(p)
    return QIcon(pixmap_rito(256))


class LogoLed(QWidget):
    """RITMORA em letras de LED."""
    def __init__(self, texto="RITMORA", passo=3.0):
        super().__init__()
        self.texto, self.passo = texto, passo
        self.setFixedSize(int(led.largura(texto, passo)) + 2, int(7 * passo) + 2)

    def paintEvent(self, _):
        p = QPainter(self)
        led.desenhar(p, self.texto, 0, 0, self.passo, COR["tinta"])
        p.end()


class RelogioLed(QWidget):
    """Relógio em LED na cor de destaque, com os pontos apagados à mostra."""
    def __init__(self, passo=3.2):
        super().__init__()
        self.passo = passo
        self.setFixedSize(int(led.largura("00:00", passo)) + 2, int(7 * passo) + 2)
        t = QTimer(self)
        t.timeout.connect(self.update)
        t.start(15_000)

    def paintEvent(self, _):
        p = QPainter(self)
        led.desenhar(p, datetime.now().strftime("%H:%M"), 0, 0, self.passo, COR["destaque_claro"], COR["led_apagado"])
        p.end()


def fmt_data(iso):
    if not iso:
        return "sem data"
    d = datetime.fromisoformat(iso)
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    return f"{dias[d.weekday()]} {d:%d/%m · %H:%M}"


def rotulo(txt):
    l = QLabel(txt.upper())
    l.setObjectName("rotulo")
    return l


def foto_redonda(caminho, letra="?", cor=None, lado=32):
    """Foto do canal em círculo (ou a inicial sobre a cor do canal quando não há foto)."""
    from PySide6.QtGui import QPainterPath
    out = QPixmap(lado * 2, lado * 2)
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    src = QPixmap(caminho) if caminho and os.path.exists(caminho) else QPixmap()
    path = QPainterPath()
    path.addEllipse(QRectF(0, 0, lado * 2, lado * 2))
    p.setClipPath(path)
    if src.isNull():
        p.fillRect(out.rect(), QColor(cor) if cor else cor_rede("youtube"))
        p.setPen(QColor("#ffffff"))
        p.setFont(fonte_ui(lado * 0.62, True))
        p.drawText(out.rect(), Qt.AlignCenter, (letra or "?")[:1].upper())
    else:
        p.drawPixmap(out.rect(), src.scaled(lado * 2, lado * 2, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
    p.end()
    out.setDevicePixelRatio(2)
    return out


class BotaoCanal(QWidget):
    """Uma repartição na coluna de canais: foto, nome, conta do YouTube e o que está pendente."""
    clicado = Signal(int)
    menu = Signal(int, object)

    def __init__(self, info):
        super().__init__()
        self.info = info
        self.compacto = False
        self.selecionado = False
        self.sobre = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(58)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: self.menu.emit(self.info["id"], self.mapToGlobal(pos)))
        self.foto = foto_redonda(info.get("foto"), info["nome"], info["cor"], 34)
        dica = info["nome"] + (f"\nYouTube: {info['youtube']}" if info.get("youtube") else "\nYouTube não conectado")
        if info["alerta"]:
            dica += f"\n{info['alerta']} na hora ou com erro"
        if info["pendentes"]:
            dica += f"\n{info['pendentes']} esperando aprovação"
        self.setToolTip(dica)

    def enterEvent(self, e):
        self.sobre = True
        self.update()

    def leaveEvent(self, e):
        self.sobre = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicado.emit(self.info["id"])

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(8, 3, -8, -3)
        cor = QColor(self.info["cor"])
        if self.selecionado or self.sobre:
            fundo = QColor(COR["painel_2"]) if self.selecionado else QColor(COR["painel"])
            p.setPen(QColor(COR["borda"]) if self.selecionado else Qt.NoPen)
            p.setBrush(fundo)
            p.drawRoundedRect(r, 10, 10)
        if self.selecionado:
            p.setPen(Qt.NoPen)
            p.setBrush(cor)
            p.drawRoundedRect(QRectF(r.left() - 5, r.top() + 12, 3, r.height() - 24), 1.5, 1.5)
        x = r.left() + (r.width() - 34) / 2 if self.compacto else r.left() + 10
        y = r.top() + (r.height() - 34) / 2
        p.drawPixmap(int(x), int(y), self.foto)
        # pontinho de alerta / contagem de pendentes
        if self.info["alerta"] or self.info["pendentes"]:
            tom = QColor(COR["agora"]) if self.info["alerta"] else QColor(COR["ambar"])
            n = self.info["alerta"] or self.info["pendentes"]
            txt = str(n) if n < 100 else "99+"
            larg = max(16, 8 + 6 * len(txt))
            bx, by = x + 34 - larg / 2 - 2, y - 4
            p.setPen(QColor(COR["noite"]))
            p.setBrush(tom)
            p.drawRoundedRect(QRectF(bx, by, larg, 16), 8, 8)
            p.setPen(QColor("#070a1c"))
            p.setFont(fonte_ui(7.5, True))
            p.drawText(QRectF(bx, by, larg, 16), Qt.AlignCenter, txt)
        if not self.compacto:
            tx = x + 34 + 10
            largura = r.right() - tx - 6
            p.setPen(QColor(COR["tinta"]))
            p.setFont(fonte_ui(10, True))
            fm = p.fontMetrics()
            p.drawText(QRectF(tx, r.top() + 9, largura, 20), Qt.AlignLeft | Qt.AlignVCenter,
                       fm.elidedText(self.info["nome"], Qt.ElideRight, int(largura)))
            p.setFont(fonte_ui(8.5))
            fm = p.fontMetrics()
            if self.info.get("youtube"):
                p.setPen(cor_rede("youtube"))
                sub = "● " + self.info["youtube"]
            else:
                p.setPen(QColor(COR["tinta_suave"]))
                sub = "YouTube não conectado"
            p.drawText(QRectF(tx, r.top() + 28, largura, 18), Qt.AlignLeft | Qt.AlignVCenter,
                       fm.elidedText(sub, Qt.ElideRight, int(largura)))
        p.end()


class Reparticoes(QFrame):
    """Coluna da esquerda: cada canal na sua repartição. Clique para trocar; botão direito para configurar."""
    escolhido = Signal(int)
    novo = Signal()
    acao = Signal(int, str)
    LARGA, ESTREITA = 224, 68

    def __init__(self):
        super().__init__()
        self.setObjectName("reparticoes")
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(0, 12, 0, 12)
        self.v.setSpacing(2)
        self.titulo = QLabel("CANAIS")
        self.titulo.setObjectName("rotulo")
        self.titulo.setContentsMargins(18, 0, 0, 6)
        self.v.addWidget(self.titulo)
        self.caixa = QVBoxLayout()
        self.caixa.setSpacing(2)
        self.v.addLayout(self.caixa)
        self.v.addStretch(1)
        self.bt_novo = QPushButton("+  Novo canal")
        self.bt_novo.setObjectName("novoCanal")
        self.bt_novo.setCursor(Qt.PointingHandCursor)
        self.bt_novo.clicked.connect(self.novo.emit)
        linha = QHBoxLayout()
        linha.setContentsMargins(10, 0, 10, 0)
        linha.addWidget(self.bt_novo)
        self.v.addLayout(linha)
        self.botoes = []
        self.compacto = False
        self.setFixedWidth(self.LARGA)

    def montar(self, infos, atual):
        for b in self.botoes:
            b.setParent(None)
            b.deleteLater()
        self.botoes = []
        for info in infos:
            b = BotaoCanal(info)
            b.selecionado = info["id"] == atual
            b.compacto = self.compacto
            b.clicado.connect(self.escolhido.emit)
            b.menu.connect(self.abrir_menu)
            self.caixa.addWidget(b)
            self.botoes.append(b)

    def abrir_menu(self, cid, pos):
        m = QMenu(self)
        for rotulo, chave in (("Configurações do canal…", "config"), ("Renomear…", "renomear"), ("Remover canal…", "remover")):
            a = m.addAction(rotulo)
            a.triggered.connect(lambda _=False, c=chave: self.acao.emit(cid, c))
        m.exec(pos)

    def definir_compacto(self, on):
        if on == self.compacto:
            return
        self.compacto = on
        self.setFixedWidth(self.ESTREITA if on else self.LARGA)
        self.titulo.setText("" if on else "CANAIS")
        self.bt_novo.setText("+" if on else "+  Novo canal")
        self.bt_novo.setToolTip("Novo canal" if on else "")
        for b in self.botoes:
            b.compacto = on
            b.update()


class BannerCanal(QFrame):
    """Banner do canal conectado no topo. Some quando nenhuma conta está conectada."""
    def __init__(self):
        super().__init__()
        self.setObjectName("bannerCanal")
        self.setFixedHeight(42)
        h = QHBoxLayout(self)
        h.setContentsMargins(6, 4, 14, 4)
        h.setSpacing(9)
        self.foto = QLabel()
        self.foto.setFixedSize(32, 32)
        h.addWidget(self.foto)
        col = QVBoxLayout()
        col.setSpacing(0)
        col.setContentsMargins(0, 0, 0, 0)
        self.rotulo = QLabel("CANAL CONECTADO")
        self.rotulo.setObjectName("bannerRotulo")
        self.nome = QLabel()
        self.nome.setObjectName("bannerNome")
        col.addWidget(self.rotulo)
        col.addWidget(self.nome)
        h.addLayout(col)
        self.dados = None
        self.largura_janela = 1600
        self.mostrar(None)

    def mostrar(self, dados):
        self.dados = dados
        if dados:
            self.nome.setText(dados["nome"])
            self.setToolTip(f"YouTube: {dados['nome']}")
            self.foto.setPixmap(foto_redonda(dados.get("foto"), dados["nome"], None, 32))
        self._atualizar()

    def ajustar_largura(self, largura):
        self.largura_janela = largura
        self._atualizar()

    def _atualizar(self):
        cheio = self.largura_janela >= 1250
        self.rotulo.setVisible(cheio)
        self.nome.setVisible(cheio)
        if cheio:
            self.layout().setContentsMargins(6, 4, 14, 4)
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
        else:
            self.layout().setContentsMargins(5, 4, 5, 4)
            self.setFixedWidth(44)
        self.setVisible(bool(self.dados))


class Tarefa(QThread):
    """Roda uma função fora da interface (envio por API, login do YouTube)."""
    feito = Signal(object)
    falhou = Signal(str)
    progresso = Signal(int)

    def __init__(self, fn, *a):
        super().__init__()
        self.fn, self.a = fn, a

    def run(self):
        try:
            self.feito.emit(self.fn(*self.a, self.progresso.emit) if self.fn.__name__ == "youtube_enviar" else self.fn(*self.a))
        except Exception as e:
            self.falhou.emit(f"{e}\n\n{traceback.format_exc(limit=2)}")


class Marca(QWidget):
    """A marca de status (forma + cor) como widget, para listas e a gaveta."""
    def __init__(self, status, cor):
        super().__init__()
        self.status, self.cor = status, cor
        self.setFixedSize(12, 12)

    def paintEvent(self, _):
        p = QPainter(self)
        desenhar_marca(p, 1, 1, self.status, self.cor)
        p.end()


def cor_status(st, rede):
    return {"aguardando": QColor(COR["ambar"]), "na_hora": QColor(COR["agora"]), "erro": QColor(COR["agora"]),
            "reprovado": QColor(COR["tinta_suave"]), "publicado": QColor(COR["verde"])}.get(st, cor_rede(rede))


class ItemPost(QWidget):
    def __init__(self, p):
        super().__init__()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 6, 16, 6)
        lay.setSpacing(14)
        img = QLabel()
        img.setFixedSize(QSize(64, 36) if p["formato"] == "longo" else QSize(34, 60))
        img.setStyleSheet(f"background:{COR['painel_2']};border-radius:4px")
        if p["thumb"] and os.path.exists(p["thumb"]):
            img.setPixmap(QPixmap(p["thumb"]).scaled(img.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        lay.addWidget(img)
        col = QVBoxLayout()
        col.setSpacing(3)
        t = QLabel(p["titulo"] or p["projeto"])
        t.setFont(fonte_ui(10.5, True))
        t.setStyleSheet("background:transparent")
        col.addWidget(t)
        meta = QLabel(f"<span style='color:{cor_rede(p['rede']).name()};font-weight:600'>{N.NOMES_REDE[p['rede']].upper()}</span>"
                      f" · {p['formato'].upper()} · {fmt_data(p['quando']).upper()}")
        meta.setFont(fonte_tv(9))
        meta.setStyleSheet(f"color:{COR['tinta_suave']};background:transparent")
        col.addWidget(meta)
        st = QHBoxLayout()
        st.setSpacing(6)
        st.addWidget(Marca(p["status"], cor_status(p["status"], p["rede"])))
        sl = QLabel(N.STATUS.get(p["status"], (p["status"],))[0])
        sl.setStyleSheet(f"color:{cor_status(p['status'], p['rede']).name()};background:transparent")
        st.addWidget(sl)
        st.addStretch()
        col.addLayout(st)
        lay.addLayout(col, 1)


class Previa(QDialog):
    def __init__(self, caminho, pai):
        super().__init__(pai)
        self.setWindowTitle("Prévia do vídeo")
        self.resize(420, 760)
        v = QVBoxLayout(self)
        tela = QVideoWidget()
        tela.setStyleSheet("background:#000")
        v.addWidget(tela, 1)
        self.player = QMediaPlayer(self)
        self.saida = QAudioOutput(self)
        self.player.setAudioOutput(self.saida)
        self.player.setVideoOutput(tela)
        self.player.setSource(QUrl.fromLocalFile(caminho))
        b = QPushButton("Pausar")
        b.clicked.connect(lambda: (self.player.pause(), b.setText("Continuar")) if self.player.playbackState() == QMediaPlayer.PlayingState
                          else (self.player.play(), b.setText("Pausar")))
        v.addWidget(b)
        self.player.play()

    def closeEvent(self, ev):
        self.player.stop()
        super().closeEvent(ev)


class Configuracoes(QDialog):
    """Configurações da repartição de um canal (e a cor do Ritmora, que vale para todos)."""
    def __init__(self, cfg, cid, pai):
        super().__init__(pai)
        self.cfg, self.cid = cfg, cid
        cc = N.canal(cfg, cid)
        self.pasta = N.pasta_canal(cid)
        self.setWindowTitle(f"Configurações · {cc['nome']}")
        f = QFormLayout(self)
        f.setVerticalSpacing(10)
        cab = QLabel(f"<b>{cc['nome']}</b><br><span style='color:{COR['tinta_suave']}'>Tudo abaixo vale só para este canal, "
                     "menos a cor do Ritmora.</span>")
        f.addRow(cab)
        self.nome = QLineEdit(cc["nome"])
        f.addRow("Nome do canal no Ritmora", self.nome)
        self.fila = QLineEdit(cc["pasta_fila"])
        b = QPushButton("Escolher…")
        b.clicked.connect(self.escolher)
        linha = QHBoxLayout()
        linha.addWidget(self.fila, 1)
        linha.addWidget(b)
        f.addRow("Pasta da fila de produção", linha)
        self.horas, self.modos = {}, {}
        for r in N.REDES:
            te = QTimeEdit()
            te.setDisplayFormat("HH:mm")
            te.setTime(te.time().fromString(cc["horarios"][r], "HH:mm"))
            self.horas[r] = te
            f.addRow(f"Horário padrão no {N.NOMES_REDE[r]}", te)
            cb = QComboBox()
            cb.addItem("Assistido: abre a página e copia a legenda", "assistido")
            cb.addItem("Automático pela API oficial" if r == "youtube" else "Automático pela API (requer app aprovado pela rede)", "api")
            cb.setCurrentIndex(max(0, cb.findData(cc["modo"].get(r, "assistido"))))
            self.modos[r] = cb
            f.addRow(f"Modo de envio no {N.NOMES_REDE[r]}", cb)
        self.cor = QComboBox()
        for chave, (nome, forte, _c) in CORES_DESTAQUE.items():
            pm = QPixmap(14, 14)
            pm.fill(QColor(forte))
            self.cor.addItem(QIcon(pm), nome, chave)
        self.cor.setCurrentIndex(max(0, self.cor.findData(cfg.get("tema", "cobalto"))))
        f.addRow("Cor do Ritmora", self.cor)
        self.intervalo = QSpinBox()
        self.intervalo.setRange(1, 14)
        self.intervalo.setValue(int(cc.get("intervalo_dias", 1)))
        f.addRow("Dias entre posts na mesma rede", self.intervalo)
        self.nav = QComboBox()
        for nid, rotulo in NAV.listar():
            self.nav.addItem(rotulo, nid)
        i = self.nav.findData(cc.get("navegador", NAV.PADRAO))
        if i < 0 and cc.get("navegador"):
            self.nav.addItem("(não encontrado) " + cc["navegador"], cc["navegador"])
            i = self.nav.count() - 1
        self.nav.setCurrentIndex(max(0, i))
        self.nav.setToolTip("Onde abrir o login do Google e as páginas de envio. Escolha o perfil logado na conta do canal.")
        f.addRow("Navegador", self.nav)
        self.chave = QLineEdit(P.token(self.cfg, cid))
        self.chave.setReadOnly(True)
        bc = QPushButton("Copiar chave")
        bc.clicked.connect(lambda: (QGuiApplication.clipboard().setText(self.chave.text()), bc.setText("Copiada")))
        bp = QPushButton("Abrir pasta da extensão")
        bp.clicked.connect(lambda: os.startfile(PASTA_EXTENSAO) if os.path.isdir(PASTA_EXTENSAO) else
                           QMessageBox.warning(self, "Extensão", f"Não achei a pasta da extensão em: {PASTA_EXTENSAO}"))
        linha_ext = QHBoxLayout()
        linha_ext.addWidget(self.chave, 1)
        linha_ext.addWidget(bc)
        linha_ext.addWidget(bp)
        f.addRow("Chave da extensão", linha_ext)
        dica_ext = QLabel("Cada canal tem a sua chave. Cole esta chave na extensão do navegador (ou perfil) logado neste canal: "
                          "ela só mostra e abre os posts dele.")
        dica_ext.setWordWrap(True)
        dica_ext.setStyleSheet(f"color:{COR['tinta_suave']}")
        f.addRow(dica_ext)
        salvo = R.canal_salvo(self.pasta)
        self.bt_yt = QPushButton("Conectar o YouTube" if not R.youtube_conectado(self.pasta)
                                 else f"Conectado: {salvo['nome'] if salvo else 'YouTube'} (reconectar)")
        self.bt_yt.clicked.connect(self.conectar_yt)
        f.addRow("Conta do YouTube", self.bt_yt)
        ajuda = QLabel("Para o envio automático no YouTube, coloque o arquivo <b>client_secret.json</b> (cliente OAuth do tipo "
                       f"“App para computador”, com a YouTube Data API v3 ativada no Google Cloud) em:<br>{N.DADOS}<br>"
                       "Um só arquivo serve para todos os canais. Ao conectar, escolha no Google a conta e o canal desta repartição "
                       "(conta de outro Google precisa estar em “Usuários de teste” no Google Cloud). "
                       "O login acontece na página do Google; o Ritmora nunca vê sua senha.")
        ajuda.setWordWrap(True)
        ajuda.setStyleSheet(f"color:{COR['tinta_suave']}")
        f.addRow(ajuda)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText("Salvar")
        bb.button(QDialogButtonBox.Save).setObjectName("primario")
        bb.button(QDialogButtonBox.Cancel).setText("Cancelar")
        bb.accepted.connect(self.salvar)
        bb.rejected.connect(self.reject)
        f.addRow(bb)

    def escolher(self):
        d = QFileDialog.getExistingDirectory(self, "Pasta da fila", self.fila.text())
        if d:
            self.fila.setText(d)

    def conectar_yt(self):
        self.bt_yt.setEnabled(False)
        self.bt_yt.setText("Abrindo o login do Google no navegador…")
        self.t = Tarefa(R.youtube_servico, self.pasta, True, self.nav.currentData())
        self.t.feito.connect(lambda _: (self.bt_yt.setText("YouTube conectado"), self.bt_yt.setEnabled(True)))
        self.t.falhou.connect(lambda e: (QMessageBox.warning(self, "Não consegui conectar o YouTube", e),
                                         self.bt_yt.setText("Conectar o YouTube"), self.bt_yt.setEnabled(True)))
        self.t.start()

    def salvar(self):
        cc = N.canal(self.cfg, self.cid)
        cc["nome"] = self.nome.text().strip() or cc["nome"]
        cc["pasta_fila"] = self.fila.text().strip()
        cc["horarios"] = {r: self.horas[r].time().toString("HH:mm") for r in N.REDES}
        cc["modo"] = {r: self.modos[r].currentData() for r in N.REDES}
        cc["intervalo_dias"] = self.intervalo.value()
        cc["navegador"] = self.nav.currentData()
        self.cfg["tema"] = self.cor.currentData()
        N.salvar_cfg(self.cfg)
        self.accept()


class Janela(QMainWindow):
    publicado_pela_extensao = Signal(int)

    def __init__(self):
        super().__init__()
        self.cfg = N.carregar_cfg()
        self.cid = self.cfg["canal_atual"]
        self.db = N.Banco()
        self.atual = None
        self.tarefas = []
        self.setWindowTitle("Ritmora")
        self.setWindowIcon(icone_app())
        self.resize(1440, 900)
        raiz = QWidget()
        raiz.setObjectName("raiz")
        self.setCentralWidget(raiz)
        v = QVBoxLayout(raiz)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.topo())
        corpo = QHBoxLayout()
        corpo.setContentsMargins(0, 0, 0, 0)
        corpo.setSpacing(0)
        self.rep = Reparticoes()
        self.rep.escolhido.connect(self.trocar_canal)
        self.rep.novo.connect(self.novo_canal)
        self.rep.acao.connect(self.acao_canal)
        corpo.addWidget(self.rep)
        div = QSplitter(Qt.Vertical)
        div.setHandleWidth(1)
        div.addWidget(self.miolo())
        div.addWidget(self.gaveta())
        div.setSizes([520, 290])
        div.setStretchFactor(0, 3)
        div.setStretchFactor(1, 0)
        div.setChildrenCollapsible(False)
        self.div = div
        corpo.addWidget(div, 1)
        v.addLayout(corpo, 1)
        self.statusBar().setSizeGripEnabled(False)
        self.setMinimumSize(1100, 640)
        # bandeja e relógio
        self.bandeja = QSystemTrayIcon(icone_app(), self)
        menu = QMenu()
        a1 = QAction("Abrir o Ritmora", self)
        a1.triggered.connect(self.showNormal)
        a2 = QAction("Sair do Ritmora", self)
        a2.triggered.connect(QApplication.quit)
        menu.addAction(a1)
        menu.addAction(a2)
        self.bandeja.setContextMenu(menu)
        self.bandeja.setToolTip("Ritmora: vigiando a agenda")
        self.bandeja.activated.connect(lambda *_: self.showNormal())
        self.bandeja.show()
        self.relogio = QTimer(self)
        self.relogio.timeout.connect(self.verificar)
        self.relogio.start(30_000)
        self.recarregar()
        QTimer.singleShot(1500, self.verificar)
        # ponte com a extensão do navegador
        self.publicado_pela_extensao.connect(self.extensao_publicou)
        for c in self.cfg["canais"]:
            P.token(self.cfg, c["id"])
        self.ponte = P.Ponte(self.cfg, ao_publicar=self.publicado_pela_extensao.emit)
        if not self.ponte.iniciar():
            self.statusBar().showMessage("Extensão do navegador desligada: " + self.ponte.erro, 10000)
        # banner do canal conectado: mostra o que já está guardado e confere com o YouTube em segundo plano
        self.banner.mostrar(R.canal_salvo(N.pasta_canal(self.cid)))
        for c in self.cfg["canais"]:
            self.atualizar_canal(c["id"])

    # ------------------------------------------------------------ repartições (canais)
    @property
    def cc(self):
        return N.canal(self.cfg, self.cid)

    def cc_de(self, p):
        return N.canal(self.cfg, p.get("canal") or 1)

    def atualizar_canal(self, cid=None):
        """Confere no YouTube qual canal está conectado nesta repartição (nome e foto) e atualiza banner e coluna."""
        cid = cid or self.cid
        pasta = N.pasta_canal(cid)
        if not R.youtube_conectado(pasta):
            if cid == self.cid:
                self.banner.mostrar(None)
            self.montar_reparticoes()
            return
        t = Tarefa(R.youtube_canal, pasta)
        self.tarefas.append(t)
        t.feito.connect(lambda d, cid=cid: self.canal_conferido(cid, d))
        t.falhou.connect(lambda e, cid=cid: self.canal_conferido(cid, R.canal_salvo(N.pasta_canal(cid))))
        t.start()

    def canal_conferido(self, cid, dados):
        if cid == self.cid:
            self.banner.mostrar(dados)
        self.montar_reparticoes()

    def montar_reparticoes(self):
        todos = self.db.todos()
        infos = []
        for c in self.cfg["canais"]:
            meus = [p for p in todos if (p.get("canal") or 1) == c["id"]]
            yt = R.canal_salvo(N.pasta_canal(c["id"]))
            infos.append({"id": c["id"], "nome": c["nome"], "cor": c.get("cor") or N.CORES_CANAL[0],
                          "foto": yt.get("foto") if yt else None, "youtube": yt.get("nome") if yt else "",
                          "alerta": sum(1 for p in meus if p["status"] in ("na_hora", "erro")),
                          "pendentes": sum(1 for p in meus if p["status"] == "aguardando")})
        self.rep.montar(infos, self.cid)

    def trocar_canal(self, cid):
        if cid == self.cid:
            return
        self.cid = cid
        self.cfg["canal_atual"] = cid
        N.salvar_cfg(self.cfg)
        self.atual = None
        self.mostrar(None)
        self.banner.mostrar(R.canal_salvo(N.pasta_canal(cid)))
        self.recarregar()

    def novo_canal(self):
        nome, ok = QInputDialog.getText(self, "Novo canal", "Nome do canal (só para você reconhecer no Ritmora):")
        if not ok or not nome.strip():
            return
        cid = N.novo_canal(self.cfg, nome.strip())
        P.token(self.cfg, cid)
        self.trocar_canal(cid)
        self.configurar(cid)

    def acao_canal(self, cid, acao):
        c = N.canal(self.cfg, cid)
        if acao == "config":
            self.trocar_canal(cid)
            self.configurar(cid)
        elif acao == "renomear":
            nome, ok = QInputDialog.getText(self, "Renomear canal", "Nome do canal no Ritmora:", text=c["nome"])
            if ok and nome.strip():
                c["nome"] = nome.strip()
                N.salvar_cfg(self.cfg)
                self.recarregar()
        elif acao == "remover":
            if len(self.cfg["canais"]) == 1:
                QMessageBox.information(self, "Remover canal", "Este é o único canal do Ritmora; não dá para remover.")
                return
            n = self.db.contar_canal(cid)
            if n:
                QMessageBox.information(self, "Remover canal", f"“{c['nome']}” ainda tem {n} post(s) no Ritmora. "
                                        "Apague ou reprove esses posts antes de remover o canal.")
                return
            if QMessageBox.question(self, "Remover canal", f"Remover a repartição “{c['nome']}” do Ritmora?\n\n"
                                    "A chave da extensão deste canal deixa de funcionar. Os arquivos de login ficam guardados em "
                                    f"{N.pasta_canal(cid)}.") != QMessageBox.Yes:
                return
            self.cfg["canais"] = [x for x in self.cfg["canais"] if x["id"] != cid]
            if self.cid == cid:
                self.cid = self.cfg["canais"][0]["id"]
                self.cfg["canal_atual"] = self.cid
                self.banner.mostrar(R.canal_salvo(N.pasta_canal(self.cid)))
            N.salvar_cfg(self.cfg)
            self.ponte.cfg = self.cfg
            self.atual = None
            self.mostrar(None)
            self.recarregar()

    def extensao_publicou(self, pid):
        p = self.db.um(pid)
        if p:
            self.bandeja.showMessage(f"Ritmora · {self.cc_de(p)['nome']}", f"Publicado no {N.NOMES_REDE[p['rede']]}: {p['titulo'] or p['projeto']}")
        if self.ponte.ativo == pid:
            self.ponte.ativo = None
        self.recarregar()

    # ------------------------------------------------------------ montagem
    def topo(self):
        f = QFrame()
        f.setObjectName("topo")
        f.setFixedHeight(68)
        h = QHBoxLayout(f)
        h.setContentsMargins(20, 0, 20, 0)
        h.setSpacing(10)
        self.rito = Rito(48)
        h.addWidget(self.rito)
        h.addWidget(LogoLed())
        h.addSpacing(6)
        self.motivo = QPushButton()
        self.motivo.setObjectName("motivo")
        self.motivo.setCursor(Qt.PointingHandCursor)
        self.motivo.clicked.connect(self.ir_urgente)
        h.addWidget(self.motivo)
        h.addSpacing(6)
        self.banner = BannerCanal()
        h.addWidget(self.banner)
        h.addStretch(1)
        h.addSpacing(12)
        self.abas = []
        for i, nome in enumerate(("Grade da semana", "Fila", "Publicados")):
            b = QPushButton(nome)
            b.setObjectName("aba")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, i=i: self.ir(i))
            h.addWidget(b)
            self.abas.append(b)
        self.abas[0].setChecked(True)
        self.proximo = QLabel()
        self.proximo.setObjectName("proximo")
        self.proximo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.proximo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        h.addWidget(self.proximo, 2)
        h.addWidget(RelogioLed())
        h.addSpacing(14)
        mais = QPushButton("Mais")
        menu = QMenu(mais)
        a = menu.addAction("Adicionar vídeo…")
        a.triggered.connect(self.adicionar)
        a = menu.addAction("Configurações do canal…")
        a.triggered.connect(lambda: self.configurar())
        mais.setMenu(menu)
        h.addWidget(mais)
        b = QPushButton("Importar fila")
        b.setObjectName("primario")
        b.clicked.connect(self.importar)
        h.addWidget(b)
        return f

    def miolo(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 12, 20, 10)
        v.setSpacing(8)
        barra = QHBoxLayout()
        self.titulo_aba = QLabel()
        self.titulo_aba.setFont(fonte_ui(13, True))
        barra.addWidget(self.titulo_aba)
        self.resumo = QLabel()
        self.resumo.setStyleSheet(f"color:{COR['tinta_suave']}")
        barra.addSpacing(16)
        barra.addWidget(self.resumo)
        barra.addStretch()
        self.nav = QWidget()
        nh = QHBoxLayout(self.nav)
        nh.setContentsMargins(0, 0, 0, 0)
        for txt, d in (("Anterior", -7), ("Hoje", 0), ("Próxima", 7)):
            b = QPushButton(txt)
            b.setObjectName("semana")
            b.clicked.connect(lambda _=False, d=d: (self.grade.andar(d), self.atualizar_titulo()))
            nh.addWidget(b)
        barra.addWidget(self.nav)
        v.addLayout(barra)
        self.pilha = QStackedWidget()
        moldura = QFrame()
        moldura.setStyleSheet(f"QFrame{{border:1px solid {COR['borda']};border-radius:8px;background:#ffffff}}")
        ml = QVBoxLayout(moldura)
        ml.setContentsMargins(1, 1, 1, 1)
        self.grade = Grade()
        self.grade.escolhido.connect(self.escolher_id)
        ml.addWidget(self.grade)
        self.pilha.addWidget(moldura)
        self.lista = QListWidget()
        self.lista.currentItemChanged.connect(lambda it, _a: it and self.escolher_id(it.data(Qt.UserRole)))
        self.pilha.addWidget(self.lista)
        self.lista_pub = QListWidget()
        self.lista_pub.currentItemChanged.connect(lambda it, _a: it and self.escolher_id(it.data(Qt.UserRole)))
        self.pilha.addWidget(self.lista_pub)
        v.addWidget(self.pilha, 1)
        return w

    def gaveta(self):
        f = QFrame()
        f.setObjectName("gaveta")
        h = QHBoxLayout(f)
        h.setContentsMargins(20, 14, 20, 12)
        h.setSpacing(20)
        # capa
        col = QVBoxLayout()
        self.capa = Capa(104, 186)
        self.capa.clicado.connect(self.assistir)
        col.addWidget(self.capa, 0, Qt.AlignHCenter)
        self.bt_pasta = QPushButton("Mostrar arquivo")
        self.bt_pasta.clicked.connect(lambda: self.atual and R.mostrar_arquivo(self.atual["video"]))
        col.addWidget(self.bt_pasta)
        h.addLayout(col)
        col.setAlignment(Qt.AlignTop)
        # texto
        meio = QVBoxLayout()
        meio.setSpacing(6)
        linha_cab = QHBoxLayout()
        linha_cab.setSpacing(12)
        self.rito_post = Rito(44, brilho=False)
        linha_cab.addWidget(self.rito_post, 0, Qt.AlignTop)
        self.cab = QLabel("Escolha um post na grade")
        self.cab.setObjectName("titulo_post")
        self.cab.setWordWrap(True)
        linha_cab.addWidget(self.cab, 1)
        meio.addLayout(linha_cab)
        est = QHBoxLayout()
        est.setSpacing(8)
        self.marca_estado = Marca("aguardando", QColor(COR["ambar"]))
        est.addWidget(self.marca_estado)
        self.estado = QLabel()
        self.estado.setOpenExternalLinks(True)
        est.addWidget(self.estado, 1)
        meio.addLayout(est)
        meio.addSpacing(8)
        self.lab_titulo = rotulo("Título no YouTube")
        meio.addWidget(self.lab_titulo)
        self.e_titulo = QLineEdit()
        self.e_titulo.setMaxLength(100)
        self.e_titulo.textChanged.connect(self.contar)
        meio.addWidget(self.e_titulo)
        meio.addWidget(rotulo("Descrição e legenda"))
        self.e_desc = QPlainTextEdit()
        self.e_desc.setMinimumHeight(56)
        self.e_desc.setMaximumHeight(118)
        meio.addWidget(self.e_desc)
        self.lab_cont = QLabel()
        self.lab_cont.setObjectName("contador")
        self.lab_cont.setTextFormat(Qt.RichText)
        meio.addWidget(self.lab_cont)
        self.e_desc.textChanged.connect(self.contar)
        self.lab_tags = rotulo("Tags no YouTube, separadas por vírgula")
        meio.addWidget(self.lab_tags)
        self.e_tags = QLineEdit()
        meio.addWidget(self.e_tags)
        meio.addStretch(1)
        h.addLayout(meio, 3)
        meio.setAlignment(Qt.AlignTop)
        # decisão
        dir_ = QVBoxLayout()
        dir_.setSpacing(6)
        lq = QHBoxLayout()
        lq.addWidget(rotulo("Publicar em"))
        self.e_quando = QDateTimeEdit()
        self.e_quando.setCalendarPopup(True)
        self.e_quando.setDisplayFormat("ddd dd/MM/yyyy · HH:mm")
        lq.addWidget(self.e_quando, 1)
        dir_.addLayout(lq)
        dec = QFrame()
        dec.setObjectName("declara")
        dl = QVBoxLayout(dec)
        dl.setContentsMargins(14, 12, 14, 12)
        dl.setSpacing(8)
        dl.addWidget(rotulo("Declarações · você marca"))
        self.g_ia, self.g_cr = QButtonGroup(self), QButtonGroup(self)
        self.linhas_dec = {}
        for grupo, texto, chave in ((self.g_ia, "Gerado ou alterado por IA?", "ia"),
                                    (self.g_cr, "Conteúdo para crianças?", "cr")):
            w = QWidget()
            lin = QHBoxLayout(w)
            lin.setContentsMargins(0, 0, 0, 0)
            l = QLabel(texto)
            lin.addWidget(l, 1)
            for val, nome in ((1, "Sim"), (0, "Não")):
                rb = QRadioButton(nome)
                grupo.addButton(rb, val)
                lin.addWidget(rb)
            dl.addWidget(w)
            self.linhas_dec[chave] = w
        self.aviso_dec = QLabel("Marque para poder aprovar.")
        self.aviso_dec.setObjectName("aviso_dec")
        self.aviso_dec.setVisible(False)
        dl.addWidget(self.aviso_dec)
        dec.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.caixa_dec = dec
        dir_.addWidget(dec)
        self.falta = QLabel()
        self.falta.setWordWrap(True)
        self.falta.setStyleSheet(f"color:{COR['ambar_tinta']}")
        dir_.addWidget(self.falta)
        self.bt_aprovar = QPushButton("Aprovar e agendar")
        self.bt_aprovar.setObjectName("primario")
        self.bt_aprovar.clicked.connect(self.aprovar)
        dir_.addWidget(self.bt_aprovar)
        l2 = QHBoxLayout()
        self.bt_salvar = QPushButton("Salvar")
        self.bt_salvar.clicked.connect(self.salvar)
        self.bt_enviar = QPushButton("Preparar envio")
        self.bt_enviar.clicked.connect(self.enviar_agora)
        l2.addWidget(self.bt_salvar)
        l2.addWidget(self.bt_enviar)
        l3 = l2
        self.bt_pub = QPushButton("Marcar publicado")
        self.bt_pub.clicked.connect(self.marcar_publicado)
        self.bt_rep = QPushButton("Reprovar")
        self.bt_rep.setObjectName("perigo")
        self.bt_rep.clicked.connect(self.reprovar)
        l3.addWidget(self.bt_pub)
        l3.addWidget(self.bt_rep)
        l2.setSpacing(6)
        for b, dica in ((self.bt_salvar, "Salvar as edições"), (self.bt_enviar, "Preparar o envio agora"),
                        (self.bt_pub, "Marcar como publicado"), (self.bt_rep, "Reprovar este post")):
            b.setToolTip(dica)
            b.setStyleSheet("padding: 7px 6px;")
        self.bt_enviar.setText("Enviar")
        self.bt_pub.setText("Publicado")
        dir_.addLayout(l2)
        self.hist = QLabel()
        self.hist.setWordWrap(True)
        self.hist.setStyleSheet(f"color:{COR['tinta_suave']};font-size:8.5pt")
        dir_.addWidget(self.hist)
        cdir = QWidget()
        cdir.setLayout(dir_)
        cdir.setFixedWidth(330)
        h.addWidget(cdir)
        self.habilitar(False)
        return f

    def habilitar(self, on):
        for w in (self.e_titulo, self.e_desc, self.e_tags, self.e_quando, self.bt_salvar, self.bt_aprovar, self.bt_enviar, self.bt_pub,
                  self.bt_rep, self.bt_pasta):
            w.setEnabled(on)
        for b in self.g_ia.buttons() + self.g_cr.buttons():
            b.setEnabled(on)

    # ------------------------------------------------------------ dados
    def ir(self, i):
        for k, b in enumerate(self.abas):
            b.setChecked(k == i)
        self.pilha.setCurrentIndex(i)
        self.nav.setVisible(i == 0)
        self.atualizar_titulo()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.banner.ajustar_largura(self.width())
        if hasattr(self, "rep"):
            self.rep.definir_compacto(self.width() < 1320)
        if hasattr(self, "div"):
            g = self.div.widget(1).sizeHint().height()
            tot = sum(self.div.sizes())
            self.div.setSizes([max(tot - g, 1), g])

    def atualizar_titulo(self):
        i = self.pilha.currentIndex()
        self.titulo_aba.setText(["Semana de " + self.grade.titulo_semana(), "Fila de aprovação", "Publicados"][i])

    def recarregar(self):
        todos = self.db.todos(canal=self.cid)
        self.setWindowTitle(f"Ritmora · {self.cc['nome']}")
        self.montar_reparticoes()
        sel = self.atual["id"] if self.atual else None
        self.grade.mostrar(todos, sel)
        ordem = {"na_hora": 0, "erro": 1, "aguardando": 2, "aprovado": 3, "agendado_rede": 4, "reprovado": 5, "publicado": 6}
        for lista, filtro in ((self.lista, lambda p: p["status"] not in ("publicado",)), (self.lista_pub, lambda p: p["status"] == "publicado")):
            lista.blockSignals(True)
            lista.clear()
            for p in sorted((p for p in todos if filtro(p)), key=lambda p: (ordem.get(p["status"], 9), p["quando"] or "")):
                it = QListWidgetItem()
                it.setData(Qt.UserRole, p["id"])
                it.setSizeHint(QSize(400, 76))
                lista.addItem(it)
                lista.setItemWidget(it, ItemPost(p))
                if p["id"] == sel:
                    lista.setCurrentItem(it, QItemSelectionModel.ClearAndSelect)
            lista.scrollToTop()
            lista.blockSignals(False)
        cont = {k: sum(1 for p in todos if p["status"] == k) for k in N.STATUS}
        partes = [f"{n} {N.STATUS[k][0].split(',')[0].lower()}" for k, n in cont.items() if n and k in ("na_hora", "aguardando", "aprovado",
                                                                                                         "agendado_rede", "erro")]
        self.resumo.setText(" · ".join(partes) if partes else ("Nada pendente." if todos else ""))
        self.abas[1].setText(f"Fila ({sum(1 for p in todos if p['status'] != 'publicado')})")
        self.urgente = None
        if cont["na_hora"] or cont["erro"]:
            self.rito.definir("alerta")
            self.urgente = next(p for p in todos if p["status"] in ("na_hora", "erro"))
            txt, tom = (f"{cont['na_hora']} na hora: confirme o envio" if cont["na_hora"] else f"{cont['erro']} com erro no envio"), "alerta"
        elif cont["aguardando"]:
            self.rito.definir("pendente")
            self.urgente = next(p for p in todos if p["status"] == "aguardando")
            txt, tom = f"{cont['aguardando']} esperando sua aprovação", "pendente"
        elif todos:
            self.rito.definir("feliz")
            txt, tom = "Tudo em dia", "ok"
        else:
            self.rito.definir("dormindo")
            txt, tom = "", "ok"
        self.motivo.setText(txt)
        self.motivo.setVisible(bool(txt))
        self.motivo.setProperty("tom", tom)
        self.motivo.style().unpolish(self.motivo)
        self.motivo.style().polish(self.motivo)
        agora_iso = datetime.now().isoformat(timespec="minutes")
        futuros = sorted((p for p in todos if p["status"] in ("aprovado", "agendado_rede", "aguardando") and p["quando"]
                          and p["quando"] >= agora_iso), key=lambda p: p["quando"])
        sv = COR["tinta_suave"]
        if futuros:
            p0 = futuros[0]
            falta = datetime.fromisoformat(p0["quando"]) - datetime.now()
            horas, mins = divmod(int(falta.total_seconds() // 60), 60)
            quanto = f"{horas} h {mins:02d} min" if horas < 48 else f"{horas // 24} dias"
            self.proximo.setText(f"<span style='color:{sv}'>Próximo post em</span> <b>{quanto}</b><br>"
                                 f"<span style='color:{sv}'>{N.NOMES_REDE[p0['rede']]} · {fmt_data(p0['quando'])}</span>")
        else:
            self.proximo.setText(f"<span style='color:{sv}'>Nenhum post agendado</span>")
        self.atualizar_titulo()
        if sel:
            self.mostrar(self.db.um(sel))

    def ir_urgente(self):
        if self.urgente:
            q = self.urgente
            self.ir(0)
            from datetime import date as _d
            dia = _d.fromisoformat(q["quando"][:10])
            if not (0 <= (dia - self.grade.inicio).days < 7):
                self.grade.inicio = dia
            self.escolher_id(q["id"])
            self.atualizar_titulo()

    def escolher_id(self, pid):
        self.mostrar(self.db.um(pid))
        self.grade.mostrar(self.db.todos(canal=self.cid), pid)

    def mostrar(self, p):
        self.atual = p
        if not p:
            self.habilitar(False)
            return
        self.habilitar(True)
        yt = p["rede"] == "youtube"
        self.cab.setText(p["titulo"] or p["projeto"])
        nome, _ = N.STATUS.get(p["status"], (p["status"], ""))
        cor = cor_status(p["status"], p["rede"])
        self.marca_estado.status, self.marca_estado.cor = p["status"], cor
        self.marca_estado.update()
        link = f" · <a style='color:{COR['destaque_claro']}' href='{p['link']}'>abrir post</a>" if p["link"] else ""
        erro = f"<br><span style='color:{COR['agora']}'>{p['erro']}</span>" if p["status"] == "erro" and p["erro"] else ""
        self.estado.setText(f"<span style='color:{cor.name()};font-weight:600'>{nome}</span>"
                            f"<span style='color:{COR['tinta_suave']}'> · {N.NOMES_REDE[p['rede']]} · {p['formato']}</span>{link}{erro}")
        self.e_titulo.setText(p["titulo"] or "")
        self.e_desc.setPlainText(p["descricao"] or "")
        self.e_tags.setText(p["tags"] or "")
        for w in (self.e_titulo, self.lab_titulo, self.e_tags, self.lab_tags, self.linhas_dec["cr"]):
            w.setVisible(yt)
        self.caixa_dec.setFixedHeight(140 if yt else 106)
        if p["quando"]:
            self.e_quando.setDateTime(QDateTime.fromString(p["quando"], "yyyy-MM-ddTHH:mm"))
        for grupo, val in ((self.g_ia, p["ia"]), (self.g_cr, p["criancas"])):
            grupo.setExclusive(False)
            for b in grupo.buttons():
                b.setChecked(val is not None and grupo.id(b) == val)
            grupo.setExclusive(True)
        self.capa.definir(p["formato"], p["thumb"], p["video"])
        self.contar()
        editavel = p["status"] in ("aguardando", "aprovado", "erro", "reprovado")
        for w in (self.e_titulo, self.e_desc, self.e_tags, self.e_quando, self.bt_salvar):
            w.setEnabled(editavel)
        self.bt_aprovar.setEnabled(p["status"] in ("aguardando", "erro", "reprovado"))
        self.bt_aprovar.setText("Aprovado" if p["status"] in ("aprovado", "agendado_rede", "na_hora", "publicado") else "Aprovar e agendar")
        self.bt_pub.setEnabled(p["status"] in ("aprovado", "na_hora", "agendado_rede", "erro"))
        self.bt_rep.setEnabled(p["status"] in ("aguardando", "aprovado", "na_hora"))
        self.bt_enviar.setEnabled(p["status"] in ("aprovado", "na_hora", "erro"))
        falta = N.pode_aprovar(p)
        self.falta.setVisible(False)
        humor = {"na_hora": "alerta", "erro": "alerta", "aguardando": "pendente", "aprovado": "feliz", "agendado_rede": "feliz",
                 "publicado": "feliz", "reprovado": "dormindo"}.get(p["status"], "atento")
        self.rito_post.definir(humor)
        bloqueado = bool(falta) and p["status"] == "aguardando"
        self.caixa_dec.setProperty("falta", "true" if bloqueado and p["ia"] is None or (bloqueado and p["rede"] == "youtube" and p["criancas"] is None) else "false")
        self.caixa_dec.style().unpolish(self.caixa_dec)
        self.caixa_dec.style().polish(self.caixa_dec)
        self.aviso_dec.setVisible(self.caixa_dec.property("falta") == "true")
        outras = [f for f in falta if "declarar" not in f]
        if outras and p["status"] == "aguardando":
            self.estado.setText(self.estado.text() + f"<br><span style='color:{COR['ambar_tinta']}'>Para aprovar, falta "
                                + "; ".join(outras) + ".</span>")
        self.hist.setText("<br>".join(f"{h['quando'][5:16].replace('T', ' ')} · {h['texto']}" for h in self.db.historico(p["id"])[:4]))

    LIMITES = {"youtube": (5000, 15), "tiktok": (4000, None), "instagram": (2200, 30)}

    def contar(self):
        """Contador da legenda e do título por rede: suave, âmbar perto do limite, vermelho passando."""
        if not self.atual:
            self.lab_cont.clear()
            return
        import re
        rede = self.atual["rede"]
        lim, lim_tags = self.LIMITES.get(rede, (2200, 30))
        txt = self.e_desc.toPlainText()
        n, tags = len(txt), len(re.findall(r"#\w+", txt))

        def tom(v, lim_):
            if lim_ and v > lim_:
                return COR["agora"]
            if lim_ and v > lim_ * 0.9:
                return COR["ambar_tinta"]
            return COR["tinta_suave"]

        def mil(v):
            return f"{v:,}".replace(",", ".")

        partes = [f"<span style='color:{tom(n, lim)}'>{mil(n)} / {mil(lim)} caracteres</span>"]
        if lim_tags:
            extra = " (o YouTube ignora todas acima de 15)" if rede == "youtube" and tags > lim_tags else ""
            partes.append(f"<span style='color:{tom(tags, lim_tags)}'>{tags} / {lim_tags} hashtags{extra}</span>")
        else:
            partes.append(f"<span style='color:{COR['tinta_suave']}'>{tags} hashtags</span>")
        if rede == "tiktok" or rede == "instagram":
            corte = 125 if rede == "instagram" else 100
            if n > corte:
                partes.append(f"<span style='color:{COR['tinta_suave']}'>aparecem ~{corte} antes do “mais”</span>")
        self.lab_cont.setText("  ·  ".join(partes))
        if rede == "youtube":
            t = len(self.e_titulo.text())
            self.lab_titulo.setText(f"TÍTULO NO YOUTUBE  ·  {t}/100")

    def assistir(self):
        if self.atual and self.atual["video"] and os.path.exists(self.atual["video"]):
            Previa(self.atual["video"], self).exec()

    # ------------------------------------------------------------ ações
    def coletar(self):
        return dict(titulo=self.e_titulo.text().strip(), descricao=self.e_desc.toPlainText().strip(), tags=self.e_tags.text().strip(),
                    quando=self.e_quando.dateTime().toString("yyyy-MM-ddTHH:mm"),
                    ia=self.g_ia.checkedId() if self.g_ia.checkedId() >= 0 else None,
                    criancas=self.g_cr.checkedId() if self.g_cr.checkedId() >= 0 else None)

    def salvar(self):
        if self.atual:
            self.db.atualizar(self.atual["id"], "Editado", **self.coletar())
            self.statusBar().showMessage("Alterações salvas.", 3000)
            self.recarregar()

    def aprovar(self):
        if not self.atual:
            return
        self.db.atualizar(self.atual["id"], None, **self.coletar())
        p = self.db.um(self.atual["id"])
        falta = N.pode_aprovar(p)
        if falta:
            self.mostrar(p)
            if any("declarar" in f for f in falta):
                (self.g_ia.buttons() + self.g_cr.buttons())[0].setFocus()
            else:
                self.statusBar().showMessage("Ainda não dá para aprovar: falta " + "; ".join(falta) + ".", 6000)
            return
        self.db.atualizar(p["id"], f"Aprovado para {fmt_data(p['quando'])} (IA: {'sim' if p['ia'] else 'não'}"
                          + (f", crianças: {'sim' if p['criancas'] else 'não'}" if p["rede"] == "youtube" else "") + ")", status="aprovado",
                          erro=None)
        if p["rede"] == "youtube" and self.cc_de(p)["modo"]["youtube"] == "api":
            self.enviar_api(self.db.um(p["id"]))
        self.statusBar().showMessage(f"Aprovado: {N.NOMES_REDE[p['rede']]} em {fmt_data(p['quando'])}.", 5000)
        self.recarregar()
        self.rito.definir("feliz")
        QTimer.singleShot(2500, self.recarregar)

    def reprovar(self):
        if self.atual:
            motivo, ok = QInputDialog.getText(self, "Reprovar este post", "Motivo (fica no histórico):")
            if ok:
                self.db.atualizar(self.atual["id"], f"Reprovado: {motivo}", status="reprovado")
                self.recarregar()

    def marcar_publicado(self):
        if self.atual:
            link, ok = QInputDialog.getText(self, "Marcar como publicado", "Cole o link do post publicado:")
            if ok:
                self.db.atualizar(self.atual["id"], f"Publicado {link}", status="publicado", link=link.strip() or None)
                self.recarregar()

    def enviar_agora(self):
        if not self.atual:
            return
        p = self.db.um(self.atual["id"])
        cc = self.cc_de(p)
        if p["rede"] == "youtube" and cc["modo"]["youtube"] == "api":
            self.enviar_api(p)
            return
        self.ponte.ativo = p["id"]
        copiar = lambda s: QGuiApplication.clipboard().setText(s)
        if self.ponte.extensao_ativa(cc["id"]):
            # abre no navegador onde a extensão está (e no perfil logado nela), não no navegador padrão
            copiar(R.texto_para_copiar(p))
            self.ponte.abrir(cc["id"], R.PAGINA_ENVIO[p["rede"]])
            self.db.atualizar(p["id"], "Envio preparado: página aberta pela extensão e legenda copiada", status="na_hora")
            self.recarregar()
            QMessageBox.information(self, "Envio preparado",
                                    f"Abri a página de envio do {N.NOMES_REDE[p['rede']]} no navegador onde está a extensão Ritmora Ajudante "
                                    f"com a chave de “{cc['nome']}” "
                                    "e copiei a legenda.\n\nUse o painel do Ritmora na página: anexa o vídeo, preenche os textos e marca "
                                    "as declarações. Você confere, publica e clica em “Já publiquei”.")
            return
        R.assistido(p, copiar, cc.get("navegador", NAV.PADRAO))
        self.db.atualizar(p["id"], "Envio preparado: página aberta e legenda copiada", status="na_hora")
        self.recarregar()
        QMessageBox.information(self, "Envio preparado",
                                f"Abri a página de envio do {N.NOMES_REDE[p['rede']]}, copiei a legenda (cole com Ctrl+V) e selecionei o vídeo "
                                "no Explorer.\n\nSe a extensão Ritmora Ajudante estiver instalada, use o painel dela na página: anexa o vídeo, preenche "
                                "os textos e marca as declarações; você confere e publica e clica em “Já publiquei”. Sem ela, marque "
                                "as mesmas declarações que marcou aqui, publique e clique em "
                                "“Publicado”.")

    def enviar_api(self, p):
        self.db.atualizar(p["id"], "Enviando para o YouTube pela API…")
        t = Tarefa(R.youtube_enviar, p, N.pasta_canal(p.get("canal") or 1))
        self.tarefas.append(t)
        t.progresso.connect(lambda n: self.statusBar().showMessage(f"Enviando para o YouTube: {n}%"))
        t.feito.connect(lambda r, pid=p["id"]: self.api_ok(pid, r))
        t.falhou.connect(lambda e, pid=p["id"]: self.api_erro(pid, e))
        t.start()

    def api_ok(self, pid, r):
        link, futuro = r
        self.db.atualizar(pid, ("Enviado e agendado no YouTube: " if futuro else "Publicado no YouTube: ") + link,
                          status="agendado_rede" if futuro else "publicado", link=link)
        self.bandeja.showMessage("Ritmora", "YouTube: " + link)
        self.statusBar().clearMessage()
        self.recarregar()

    def api_erro(self, pid, e):
        self.db.atualizar(pid, "Erro no envio", status="erro", erro=e.splitlines()[0][:300])
        self.bandeja.showMessage("Ritmora", "O envio para o YouTube falhou. Veja o erro no post.", QSystemTrayIcon.Warning)
        self.recarregar()

    def verificar(self):
        for p in self.db.vencidos():
            cc = self.cc_de(p)
            if p["rede"] == "youtube" and cc["modo"]["youtube"] == "api":
                continue
            self.db.atualizar(p["id"], "Chegou a hora", status="na_hora")
            self.bandeja.showMessage(f"Ritmora · {cc['nome']}: hora de postar", f"{N.NOMES_REDE[p['rede']]}: {p['titulo'] or p['projeto']}")
        self.recarregar()

    def importar(self):
        n, avisos = N.importar_fila(self.db, self.cc)
        self.recarregar()
        msg = (f"{n} post{'s' if n != 1 else ''} importado{'s' if n != 1 else ''} da fila de “{self.cc['nome']}”." if n
               else f"A fila de produção de “{self.cc['nome']}” está vazia.")
        self.statusBar().showMessage(msg + (" " + " ".join(avisos) if avisos else ""), 8000)

    def adicionar(self):
        arq, _ = QFileDialog.getOpenFileName(self, "Escolha o vídeo", "", "Vídeos (*.mp4 *.mov *.webm)")
        if not arq:
            return
        rede, ok = QInputDialog.getItem(self, "Rede", "Para qual rede é este vídeo?", [N.NOMES_REDE[r] for r in N.REDES], 0, False)
        if not ok:
            return
        rede = next(k for k, v in N.NOMES_REDE.items() if v == rede)
        nome = os.path.splitext(os.path.basename(arq))[0]
        self.db.criar(projeto=nome, rede=rede, formato="short", titulo=nome, descricao="", tags="", video=arq, thumb=None,
                      quando=N.proximo_horario(self.db, rede, self.cc), pasta=os.path.dirname(arq), ia=None, criancas=None,
                      canal=self.cid)
        self.recarregar()

    def configurar(self, cid=None):
        cid = cid or self.cid
        d = Configuracoes(self.cfg, cid, self)
        d.exec()
        # salvo ou não, o login do YouTube pode ter mudado durante o diálogo
        self.cfg = N.carregar_cfg()
        self.cfg["canal_atual"] = self.cid
        self.ponte.cfg = self.cfg
        self.atualizar_canal(cid)
        if d.result():
            definir_destaque(self.cfg.get("tema", "cobalto"))
            QApplication.instance().setStyleSheet(estilo())
            self.recarregar()
            for w in self.findChildren(QWidget):
                w.update()

    def closeEvent(self, ev):
        ev.ignore()
        self.hide()
        self.bandeja.showMessage("Ritmora", "Continuo na bandeja vigiando a agenda. Para sair, clique com o botão direito no ícone.")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Ritmora")
    app.setQuitOnLastWindowClosed(False)
    definir_destaque(N.carregar_cfg().get("tema", "cobalto"))
    app.setStyleSheet(estilo())
    app.setFont(QFont("Segoe UI", 10))
    j = Janela()
    j.show()
    sys.exit(app.exec())
