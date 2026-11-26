# Ritmora: a capa do post na gaveta, dentro de uma moldura de celular (short) ou de tela (longo).
# Passando o mouse, toca uma prévia muda do vídeo na própria moldura; clicando, abre o player.
# Sem capa, usa o primeiro quadro do vídeo.
import os

from PySide6.QtCore import Qt, QRectF, QPointF, QUrl, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPainterPath, QPixmap, QPen, QLinearGradient, QImage
from PySide6.QtWidgets import QWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink

from .tema import COR, fonte_ui


class Capa(QWidget):
    clicado = Signal()

    def __init__(self, largura=118, altura=212):
        super().__init__()
        self.setFixedSize(largura, altura)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.formato = "short"
        self.foto = None          # QImage da capa
        self.quadro = None        # QImage do vídeo durante a prévia
        self.video = None
        self.tocando = False
        self.pegar_primeiro = False
        self.progresso = 0.0
        self.player = QMediaPlayer(self)
        self.som = QAudioOutput(self)
        self.som.setMuted(True)
        self.player.setAudioOutput(self.som)
        self.sink = QVideoSink(self)
        self.player.setVideoOutput(self.sink)
        self.sink.videoFrameChanged.connect(self._quadro)
        self.player.positionChanged.connect(self._pos)
        self.setToolTip("Passe o mouse para ver a prévia · clique para assistir")

    # ---------- dados
    def definir(self, formato, thumb, video):
        self.parar()
        self.formato = formato
        self.video = video if video and os.path.exists(video) else None
        self.foto = QImage(thumb) if thumb and os.path.exists(thumb) else None
        if self.foto is not None and self.foto.isNull():
            self.foto = None
        self.quadro = None
        if self.foto is None and self.video:
            # sem capa: pega o primeiro quadro do vídeo
            self.pegar_primeiro = True
            self.player.setSource(QUrl.fromLocalFile(self.video))
            self.player.setPosition(0)
            self.player.play()
        self.update()

    def parar(self):
        self.tocando = False
        self.pegar_primeiro = False
        self.player.stop()
        self.quadro = None
        self.progresso = 0.0
        self.update()

    # ---------- prévia
    def enterEvent(self, e):
        if self.video:
            self.tocando = True
            self.player.setSource(QUrl.fromLocalFile(self.video))
            self.player.setPosition(0)
            self.player.play()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self.tocando:
            self.parar()
        super().leaveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.parar()
            self.clicado.emit()

    def _quadro(self, frame):
        img = frame.toImage()
        if img.isNull():
            return
        if self.pegar_primeiro and not self.tocando:
            self.foto = img.copy()
            self.pegar_primeiro = False
            QTimer.singleShot(0, self.player.stop)
        elif self.tocando:
            self.quadro = img
        self.update()

    def _pos(self, ms):
        dur = self.player.duration()
        self.progresso = ms / dur if dur > 0 else 0.0
        if self.tocando and ms > 12000:      # prévia curta: volta ao começo
            self.player.setPosition(0)

    # ---------- desenho
    def _telas(self):
        W, H = self.width(), self.height()
        if self.formato == "longo":
            w = W - 2
            h = w * 9 / 16
            corpo = QRectF(1, (H - h - 18) / 2, w, h + 8)
            tela = corpo.adjusted(4, 4, -4, -4)
            return corpo, tela
        corpo = QRectF(1, 1, W - 2, H - 2)
        tela = corpo.adjusted(5, 7, -5, -7)
        return corpo, tela

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        corpo, tela = self._telas()
        longo = self.formato == "longo"
        # moldura
        rc = 6 if longo else 16
        pc = QPainterPath()
        pc.addRoundedRect(corpo, rc, rc)
        g = QLinearGradient(corpo.topLeft(), corpo.bottomRight())
        g.setColorAt(0, QColor("#3a4262"))
        g.setColorAt(1, QColor("#12172e"))
        p.fillPath(pc, g)
        p.setPen(QPen(QColor(COR["borda"]), 1))
        p.drawPath(pc)
        # tela
        rt = 3 if longo else 11
        pt = QPainterPath()
        pt.addRoundedRect(tela, rt, rt)
        p.fillPath(pt, QColor("#03050c"))
        img = self.quadro if (self.tocando and self.quadro is not None) else self.foto
        p.save()
        p.setClipPath(pt)
        if img is not None:
            # preenche a tela (corta o excesso), centralizado
            esc = max(tela.width() / img.width(), tela.height() / img.height())
            w, h = img.width() * esc, img.height() * esc
            p.drawImage(QRectF(tela.center().x() - w / 2, tela.center().y() - h / 2, w, h), img)
        else:
            p.setPen(QColor(COR["tinta_suave"]))
            p.setFont(fonte_ui(8.5))
            p.drawText(tela, Qt.AlignCenter, "sem capa")
        if self.tocando:
            # barrinha de progresso na cor de destaque
            barra = QRectF(tela.left(), tela.bottom() - 3, tela.width() * self.progresso, 3)
            p.fillRect(barra, QColor(COR["destaque_claro"]))
        elif img is not None and self.video:
            # selo de play discreto
            c = QPointF(tela.center().x(), tela.center().y())
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(7, 10, 28, 150))
            p.drawEllipse(c, 15, 15)
            tri = QPainterPath()
            tri.moveTo(c.x() - 5, c.y() - 7)
            tri.lineTo(c.x() + 8, c.y())
            tri.lineTo(c.x() - 5, c.y() + 7)
            tri.closeSubpath()
            p.fillPath(tri, QColor("#eef1fa"))
        p.restore()
        p.setPen(Qt.NoPen)
        if longo:
            # pé do monitor
            base = QRectF(corpo.center().x() - 18, corpo.bottom() + 3, 36, 4)
            p.setBrush(QColor("#3a4262"))
            p.drawRoundedRect(QRectF(corpo.center().x() - 4, corpo.bottom(), 8, 4), 1, 1)
            p.drawRoundedRect(base, 2, 2)
        else:
            # ilha da câmera
            p.setBrush(QColor("#03050c"))
            p.drawRoundedRect(QRectF(corpo.center().x() - 14, tela.top() + 5, 28, 7), 3.5, 3.5)
        p.end()
