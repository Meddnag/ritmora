# Ritmora: o mascote Rito, uma folhinha de calendário com olhos de LED. O rosto mostra o estado da agenda:
#  "feliz" (tudo em dia), "atento" (normal), "alerta" (post na hora ou erro), "pendente" (esperando aprovação), "dormindo" (fila vazia).
# Ele pisca sozinho de tempos em tempos para parecer vivo.
import math

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QRadialGradient, QPainterPath, QPixmap, QPen, QIcon, QImage
from PySide6.QtWidgets import QWidget

COR_LED = "#e9f0ff"
COR_LED_ALERTA = "#ff8a95"


# olhos em grade de pontos (cada olho 4x6 pontos, 1 = aceso)
OLHOS = {
    "atento": ["0110", "1111", "1111", "1111", "1111", "0110"],
    "feliz": ["0000", "0110", "1001", "0000", "0000", "0000"],
    "fechado": ["0000", "0000", "0000", "1111", "0000", "0000"],
    "alerta": ["0110", "0110", "0110", "0110", "0000", "0110"],
    "pendente": ["0000", "0000", "1111", "1111", "1111", "0110"],
    "dormindo": ["0000", "0000", "0000", "1001", "0110", "0000"],
}


def desenhar_rito(p: QPainter, r: QRectF, humor="atento", piscando=False, brilho=True, papel="claro"):
    """Rito, uma folhinha de calendário de mesa: argolas no topo, faixa do mês na cor de destaque,
    olhos de LED na folha e a ponta dobrada no canto. papel='claro' (folha de papel) ou 'escuro' (folha grafite)."""
    from .tema import COR
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    s = min(r.width(), r.height())
    cx, cy = r.center().x(), r.center().y()
    dest = QColor(COR["destaque"])
    if brilho:
        g = QRadialGradient(QPointF(cx, cy + s * 0.05), s * 0.75)
        for pos, a in ((0.0, 120), (0.55, 40), (1.0, 0)):
            c = QColor(dest)
            c.setAlpha(a)
            g.setColorAt(pos, c)
        p.setBrush(g)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy + s * 0.05), s * 0.75, s * 0.7)
    corpo = QRectF(cx - s * 0.4, cy - s * 0.33, s * 0.8, s * 0.76)
    raio = s * 0.11
    dobra = s * 0.17
    # folha com a ponta de baixo à direita dobrada
    folha = QPainterPath()
    folha.moveTo(corpo.left() + raio, corpo.top())
    folha.lineTo(corpo.right() - raio, corpo.top())
    folha.quadTo(corpo.right(), corpo.top(), corpo.right(), corpo.top() + raio)
    folha.lineTo(corpo.right(), corpo.bottom() - dobra)
    folha.lineTo(corpo.right() - dobra, corpo.bottom())
    folha.lineTo(corpo.left() + raio, corpo.bottom())
    folha.quadTo(corpo.left(), corpo.bottom(), corpo.left(), corpo.bottom() - raio)
    folha.lineTo(corpo.left(), corpo.top() + raio)
    folha.quadTo(corpo.left(), corpo.top(), corpo.left() + raio, corpo.top())
    if papel == "claro":
        gc = QLinearGradient(corpo.topLeft(), corpo.bottomLeft())
        gc.setColorAt(0, QColor("#f4f6fd"))
        gc.setColorAt(1, QColor("#c9cfe4"))
        borda, tinta, apagado = QColor("#ffffff"), QColor("#141a34"), QColor(20, 26, 52, 22)
    else:
        gc = QLinearGradient(corpo.topLeft(), corpo.bottomLeft())
        gc.setColorAt(0, QColor("#3a4262"))
        gc.setColorAt(1, QColor("#171d38"))
        borda, tinta, apagado = QColor("#8a95bf"), QColor(COR_LED), QColor(255, 255, 255, 16)
    p.setBrush(gc)
    p.setPen(QPen(borda, max(1.0, s * 0.012)))
    p.drawPath(folha)
    # faixa do mês (cor de destaque), recortada pela folha
    faixa = QRectF(corpo.left(), corpo.top(), corpo.width(), s * 0.2)
    p.save()
    p.setClipPath(folha)
    gf = QLinearGradient(faixa.topLeft(), faixa.bottomLeft())
    gf.setColorAt(0, dest.lighter(125))
    gf.setColorAt(1, dest)
    p.fillRect(faixa, gf)
    p.restore()
    # ponta dobrada
    canto = QPainterPath()
    canto.moveTo(corpo.right(), corpo.bottom() - dobra)
    canto.lineTo(corpo.right() - dobra, corpo.bottom() - dobra)
    canto.lineTo(corpo.right() - dobra, corpo.bottom())
    canto.closeSubpath()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#9aa3c4") if papel == "claro" else QColor("#5d6684"))
    p.drawPath(canto)
    # argolas
    for k in (-1, 1):
        ax = cx + k * s * 0.2
        p.setBrush(QColor("#070a1c"))
        p.drawEllipse(QPointF(ax, corpo.top() + s * 0.07), s * 0.035, s * 0.035)
        p.setPen(QPen(QColor("#dfe5f5"), max(1.2, s * 0.032), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(ax, corpo.top() - s * 0.07), QPointF(ax, corpo.top() + s * 0.07))
        p.setPen(Qt.NoPen)
    # olhos de LED na folha
    olho = OLHOS["fechado" if piscando else humor]
    area = QRectF(corpo.left(), faixa.bottom(), corpo.width(), corpo.bottom() - faixa.bottom() - s * 0.1)
    passo = s * 0.047
    cor = QColor("#ff4d5e") if humor == "alerta" else tinta
    larg_olho = 4 * passo
    gap = passo * 2.4
    x0 = area.center().x() - larg_olho - gap / 2
    y0 = area.center().y() - 3 * passo
    for k in range(2):
        ox = x0 + k * (larg_olho + gap)
        for li, linha in enumerate(olho):
            for ci, bit in enumerate(linha):
                c = QPointF(ox + ci * passo + passo / 2, y0 + li * passo + passo / 2)
                p.setBrush(cor if bit == "1" else apagado)
                p.drawEllipse(c, passo * 0.42, passo * 0.42)
    # linha de dias embaixo (a "boca"): sete quadradinhos, o de hoje aceso na cor de destaque
    q = s * 0.045
    by = corpo.bottom() - s * 0.1
    for i in range(7):
        bx = cx - 3.5 * q * 1.45 + i * q * 1.45 - dobra * 0.25
        p.setBrush(dest if i == 3 else apagado if papel == "escuro" else QColor(20, 26, 52, 45))
        p.drawRoundedRect(QRectF(bx, by, q, q), q * 0.25, q * 0.25)
    p.restore()


class Rito(QWidget):
    """O mascote como widget, com piscar automático."""

    def __init__(self, tamanho=40, brilho=True):
        super().__init__()
        self.setFixedSize(tamanho, tamanho)
        self.humor = "atento"
        self.piscando = False
        self.brilho = brilho
        self._t = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tique)
        self.timer.start(120)

    def definir(self, humor):
        if humor != self.humor:
            self.humor = humor
            self.update()

    def _tique(self):
        self._t += 1
        # pisca ~ a cada 4,3 s (não pisca dormindo)
        pisca = self.humor not in ("dormindo",) and (self._t % 36) in (0, 1)
        if pisca != self.piscando:
            self.piscando = pisca
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        desenhar_rito(p, QRectF(self.rect()), self.humor, self.piscando, self.brilho)
        p.end()


def pixmap_rito(tam=256, humor="atento", fundo=True):
    img = QImage(tam, tam, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    if fundo:
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, tam, tam), tam * 0.22, tam * 0.22)
        g = QRadialGradient(QPointF(tam * 0.5, tam * 0.62), tam * 0.75)
        g.setColorAt(0, QColor("#1d2f80"))
        g.setColorAt(0.6, QColor("#0f1640"))
        g.setColorAt(1, QColor("#070a1c"))
        p.fillPath(path, g)
        desenhar_rito(p, QRectF(tam * 0.06, tam * 0.08, tam * 0.88, tam * 0.88), humor, False, False)
    else:
        desenhar_rito(p, QRectF(0, 0, tam, tam), humor, False, False)
    p.end()
    return QPixmap.fromImage(img)
