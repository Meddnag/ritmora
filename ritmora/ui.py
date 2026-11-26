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
from .tema import COR, estilo, definir_destaque, CORES_DESTAQUE, fonte_tv, fonte_ui, cor_rede
from .mascote import Rito, pixmap_rito
from .capa import Capa
from . import led
from .grade import Grade, desenhar_marca, STATUS_CURTO


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
    def __init__(self, cfg, pai):
        super().__init__(pai)
        self.setWindowTitle("Configurações do Ritmora")
        self.cfg = dict(cfg)
        f = QFormLayout(self)
        f.setVerticalSpacing(10)
        self.fila = QLineEdit(cfg["pasta_fila"])
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
            te.setTime(te.time().fromString(cfg["horarios"][r], "HH:mm"))
            self.horas[r] = te
            f.addRow(f"Horário padrão no {N.NOMES_REDE[r]}", te)
            cb = QComboBox()
            cb.addItem("Assistido: abre a página e copia a legenda", "assistido")
            cb.addItem("Automático pela API oficial" if r == "youtube" else "Automático pela API (requer app aprovado pela rede)", "api")
            cb.setCurrentIndex(max(0, cb.findData(cfg["modo"].get(r, "assistido"))))
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
        self.intervalo.setValue(int(cfg.get("intervalo_dias", 1)))
        f.addRow("Dias entre posts na mesma rede", self.intervalo)
        self.bt_yt = QPushButton("Conectar o YouTube" if not R.youtube_conectado(N.DADOS) else "YouTube conectado (reconectar)")
        self.bt_yt.clicked.connect(self.conectar_yt)
        f.addRow("Conta do YouTube", self.bt_yt)
        ajuda = QLabel("Para o envio automático no YouTube, coloque o arquivo <b>client_secret.json</b> (cliente OAuth do tipo "
                       f"“App para computador”, com a YouTube Data API v3 ativada no Google Cloud) em:<br>{N.DADOS}<br>"
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
        self.t = Tarefa(R.youtube_servico, N.DADOS, True)
        self.t.feito.connect(lambda _: (self.bt_yt.setText("YouTube conectado"), self.bt_yt.setEnabled(True)))
        self.t.falhou.connect(lambda e: (QMessageBox.warning(self, "Não consegui conectar o YouTube", e),
                                         self.bt_yt.setText("Conectar o YouTube"), self.bt_yt.setEnabled(True)))
        self.t.start()

    def salvar(self):
        self.cfg["pasta_fila"] = self.fila.text()
        self.cfg["horarios"] = {r: self.horas[r].time().toString("HH:mm") for r in N.REDES}
        self.cfg["modo"] = {r: self.modos[r].currentData() for r in N.REDES}
        self.cfg["intervalo_dias"] = self.intervalo.value()
        self.cfg["tema"] = self.cor.currentData()
        N.salvar_cfg(self.cfg)
        self.accept()


class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = N.carregar_cfg()
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
        div = QSplitter(Qt.Vertical)
        div.setHandleWidth(1)
        div.addWidget(self.miolo())
        div.addWidget(self.gaveta())
        div.setSizes([520, 290])
        div.setStretchFactor(0, 3)
        div.setStretchFactor(1, 0)
        div.setChildrenCollapsible(False)
        self.div = div
        v.addWidget(div, 1)
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
        self.lab_canal = QLabel(self.cfg.get("canal", ""))
        self.lab_canal.setObjectName("canal")
        self.lab_canal.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.lab_canal.setMinimumWidth(0)
        h.addWidget(self.lab_canal, 1)
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
        a = menu.addAction("Configurações…")
        a.triggered.connect(self.configurar)
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
        self.lab_canal.setVisible(self.width() >= 1400)
        if hasattr(self, "div"):
            g = self.div.widget(1).sizeHint().height()
            tot = sum(self.div.sizes())
            self.div.setSizes([max(tot - g, 1), g])

    def atualizar_titulo(self):
        i = self.pilha.currentIndex()
        self.titulo_aba.setText(["Semana de " + self.grade.titulo_semana(), "Fila de aprovação", "Publicados"][i])

    def recarregar(self):
        todos = self.db.todos()
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
        self.grade.mostrar(self.db.todos(), pid)

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
        if p["rede"] == "youtube" and self.cfg["modo"]["youtube"] == "api":
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
        if p["rede"] == "youtube" and self.cfg["modo"]["youtube"] == "api":
            self.enviar_api(p)
            return
        R.assistido(p, lambda s: QGuiApplication.clipboard().setText(s))
        self.db.atualizar(p["id"], "Envio preparado: página aberta e legenda copiada", status="na_hora")
        self.recarregar()
        QMessageBox.information(self, "Envio preparado",
                                f"Abri a página de envio do {N.NOMES_REDE[p['rede']]}, copiei a legenda (cole com Ctrl+V) e selecionei o vídeo "
                                "no Explorer.\n\nMarque lá as mesmas declarações que você marcou aqui e publique. Depois clique em "
                                "“Publicado”.")

    def enviar_api(self, p):
        self.db.atualizar(p["id"], "Enviando para o YouTube pela API…")
        t = Tarefa(R.youtube_enviar, p, N.DADOS)
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
            if p["rede"] == "youtube" and self.cfg["modo"]["youtube"] == "api":
                continue
            self.db.atualizar(p["id"], "Chegou a hora", status="na_hora")
            self.bandeja.showMessage("Ritmora: hora de postar", f"{N.NOMES_REDE[p['rede']]}: {p['titulo'] or p['projeto']}")
        self.recarregar()

    def importar(self):
        n, avisos = N.importar_fila(self.db, self.cfg)
        self.recarregar()
        msg = f"{n} post{'s' if n != 1 else ''} importado{'s' if n != 1 else ''} da fila." if n else "A fila de produção está vazia."
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
                      quando=N.proximo_horario(self.db, rede, self.cfg), pasta=os.path.dirname(arq), ia=None, criancas=None)
        self.recarregar()

    def configurar(self):
        d = Configuracoes(self.cfg, self)
        if d.exec():
            self.cfg = N.carregar_cfg()
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
