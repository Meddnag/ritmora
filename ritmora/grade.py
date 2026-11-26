# Ritmora: a grade da semana (desenhada à mão com QPainter). Cada rede é um canal (linha), cada dia uma coluna,
# cada post um bloco no seu horário. Hoje tem cabeçalho marinho e uma linha vermelha marca o agora.
from datetime import datetime, timedelta, date

from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath, QFontMetrics, QRadialGradient
from PySide6.QtWidgets import QWidget, QToolTip

from . import nucleo as N
from .tema import COR, fonte_tv, fonte_ui, cor_rede
from . import led
from .mascote import desenhar_rito

DIAS = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
STATUS_CURTO = {"aguardando": "Aguardando", "aprovado": "Na agenda", "agendado_rede": "Agendado na rede", "na_hora": "Na hora",
                "publicado": "Publicado", "reprovado": "Reprovado", "erro": "Erro"}


def desenhar_marca(p, x, y, status, cor):
    """Marca de status com forma própria (lida sem depender de cor)."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(x, y, 10, 10)
    pen = QPen(cor, 1.6)
    p.setPen(pen)
    if status == "publicado":
        p.setBrush(cor)
        p.drawEllipse(r)
        ck = QPainterPath(QPointF(x + 2.6, y + 5.2))
        ck.lineTo(x + 4.4, y + 7.0)
        ck.lineTo(x + 7.6, y + 3.4)
        p.setPen(QPen(QColor("#ffffff"), 1.6))
        p.setBrush(Qt.NoBrush)
        p.drawPath(ck)
    elif status in ("aprovado", "agendado_rede"):
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(r)
        if status == "agendado_rede":
            p.setBrush(cor)
            p.drawEllipse(QRectF(x + 3, y + 3, 4, 4))
    elif status == "aguardando":
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(r)
        meia = QPainterPath()
        meia.moveTo(x + 5, y)
        meia.arcTo(r, 90, 180)
        meia.closeSubpath()
        p.setBrush(cor)
        p.drawPath(meia)
    elif status == "na_hora":
        p.setBrush(cor)
        tri = QPainterPath(QPointF(x + 5, y))
        tri.lineTo(x + 10, y + 9.5)
        tri.lineTo(x, y + 9.5)
        tri.closeSubpath()
        p.drawPath(tri)
    elif status == "erro":
        p.drawLine(QPointF(x, y), QPointF(x + 10, y + 10))
        p.drawLine(QPointF(x + 10, y), QPointF(x, y + 10))
    else:  # reprovado
        p.drawEllipse(r)
        p.drawLine(QPointF(x + 1, y + 9), QPointF(x + 9, y + 1))
    p.restore()


class Grade(QWidget):
    escolhido = Signal(int)
    semana_mudou = Signal()

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setMinimumHeight(230)
        self.inicio = date.today()
        self.posts = []
        self.sel = None
        self.blocos = []
        self.sobre = None

    def mostrar(self, posts, sel=None):
        self.posts = [p for p in posts if p["quando"]]
        self.sel = sel
        self.update()

    def andar(self, dias):
        self.inicio = date.today() if dias == 0 else self.inicio + timedelta(days=dias)
        self.semana_mudou.emit()
        self.update()

    def titulo_semana(self):
        fim = self.inicio + timedelta(days=6)
        return f"{self.inicio:%d/%m} a {fim:%d/%m/%Y}"

    # ------------------------------------------------------------ desenho
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        p.fillRect(self.rect(), QColor(COR["painel"]))
        dest = QColor(COR["destaque"])
        hoje0 = date.today()
        di0 = (hoje0 - self.inicio).days
        colw0 = (W - 150) / 7
        agora0 = datetime.now()
        xa0 = 150 + (di0 + (agora0.hour * 60 + agora0.minute) / 1440) * colw0 if 0 <= di0 < 7 else W * 0.7
        for cx, cy, rr, a in ((xa0, H * 0.85, W * 0.33, 150), (W * 0.92, H * 1.05, W * 0.3, 70), (W * 0.05, H * 1.1, W * 0.22, 45)):
            g = QRadialGradient(QPointF(cx, cy), rr)
            c0, c1, c2 = QColor(dest), QColor(dest), QColor(dest)
            c0.setAlpha(a)
            c1.setAlpha(int(a * 0.35))
            c2.setAlpha(0)
            g.setColorAt(0, c0)
            g.setColorAt(0.45, c1)
            g.setColorAt(1, c2)
            p.fillRect(self.rect(), g)
        x0, cab = 150, 44
        colw = (W - x0) / 7
        linh = (H - cab) / 3
        hoje = date.today()
        # cabeçalho dos dias
        for i in range(7):
            d = self.inicio + timedelta(days=i)
            r = QRectF(x0 + i * colw, 0, colw, cab)
            eh_hoje = d == hoje
            p.fillRect(r, QColor(COR["painel_2"] if eh_hoje else COR["cabecalho"]))
            led.desenhar(p, f"{DIAS[d.weekday()]} {d.day:02d}", r.x() + 12, r.y() + 13, 2.6,
                         COR["destaque_claro"] if eh_hoje else COR["tinta_suave"], COR["led_apagado"] if eh_hoje else None)
            if eh_hoje:
                p.fillRect(QRectF(r.x(), r.bottom() - 2, r.width(), 2), QColor(COR["destaque"]))
        di = (hoje - self.inicio).days
        if 0 <= di < 7:
            agora = datetime.now()
            xa = x0 + di * colw + (agora.hour * 60 + agora.minute) / 1440 * colw
            p.setBrush(QColor(COR["agora"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(xa, cab - 1), 4, 4)
            p.setBrush(Qt.NoBrush)
        p.fillRect(QRectF(0, 0, x0, cab), QColor(COR["cabecalho"]))
        led.desenhar(p, "CANAL", 16, 13, 2.6, COR["tinta_suave"])
        # linhas dos canais
        self.blocos = []
        self._agora = None
        for k, rede in enumerate(N.REDES):
            y = cab + k * linh
            fundo = QColor(COR["noite"])
            fundo.setAlpha(35)
            p.fillRect(QRectF(0, y, W, linh), fundo)
            p.fillRect(QRectF(16, y + 16, 6, linh - 32), cor_rede(rede))
            p.setFont(fonte_ui(12.5, True))
            p.setPen(QColor(COR["tinta"]))
            p.drawText(QRectF(32, y, x0 - 36, linh), Qt.AlignVCenter, N.NOMES_REDE[rede])
            n = sum(1 for q in self.posts if q["rede"] == rede and self.na_semana(q))
            led.desenhar(p, str(n), 33, y + linh / 2 + 12, 1.6, COR["tinta_suave"])
            p.setFont(fonte_ui(8.5))
            p.setPen(QColor(COR["tinta_suave"]))
            p.drawText(QRectF(33 + led.largura(str(n), 1.6) + 5, y + linh / 2 + 9, 60, 16), Qt.AlignLeft | Qt.AlignVCenter,
                       "post" if n == 1 else "posts")
            for i in range(7):
                d = self.inicio + timedelta(days=i)
                cel = QRectF(x0 + i * colw, y, colw, linh)
                if d == hoje:
                    ch = QColor(COR["hoje"])
                    ch.setAlpha(60)
                    p.fillRect(cel, ch)
                    self.linha_agora(p, x0, colw, cel)
                doc = sorted((q for q in self.posts if q["rede"] == rede and q["quando"][:10] == d.isoformat()), key=lambda q: q["quando"])
                if doc:
                    alt = (linh - 16 - 6 * (len(doc) - 1)) / len(doc)
                    for j, q in enumerate(doc):
                        b = QRectF(cel.x() + 8, cel.y() + 8 + j * (alt + 6), cel.width() - 16, alt)
                        self.bloco(p, b, q)
                        self.blocos.append((b, q))
        # grade de 1 px
        p.setPen(QPen(QColor(COR["fio"]), 1))
        for k in range(4):
            p.drawLine(QPointF(0, cab + k * linh), QPointF(W, cab + k * linh))
        for i in range(8):
            p.drawLine(QPointF(x0 + i * colw, 0), QPointF(x0 + i * colw, H))
        if not any(self.na_semana(q) for q in self.posts):
            meio = QRectF(x0, cab, W - x0, H - cab)
            desenhar_rito(p, QRectF(meio.center().x() - 50, meio.center().y() - 85, 100, 100), "dormindo")
            p.setFont(fonte_ui(12))
            p.setPen(QColor(COR["tinta_suave"]))
            p.drawText(QRectF(x0, meio.center().y() + 22, W - x0, 50), Qt.AlignHCenter | Qt.AlignTop,
                       "Nenhum post nesta semana.\nImporte a fila de produção ou adicione um vídeo.")
        p.end()

    def linha_agora(self, p, x0, colw, cel):
        """A linha vermelha do agora, por baixo dos blocos, desenhada em cada faixa de canal."""
        hoje = date.today()
        di = (hoje - self.inicio).days
        agora = datetime.now()
        xa = x0 + di * colw + (agora.hour * 60 + agora.minute) / 1440 * colw
        p.save()
        p.setPen(QPen(QColor(COR["agora"]), 2))
        p.drawLine(QPointF(xa, cel.top()), QPointF(xa, cel.bottom()))
        p.restore()

    def na_semana(self, q):
        d = date.fromisoformat(q["quando"][:10])
        return 0 <= (d - self.inicio).days < 7

    def bloco(self, p, b, q):
        p.save()
        p.setBrush(Qt.NoBrush)
        self._bloco(p, b, q)
        p.restore()

    def _bloco(self, p, b, q):
        cor = cor_rede(q["rede"])
        st = q["status"]
        path = QPainterPath()
        path.addRoundedRect(b, 6, 6)
        claro = st in ("aguardando", "aprovado", "agendado_rede", "erro", "reprovado")
        if st == "aguardando":
            p.fillPath(path, QColor(COR["ambar_fundo"]))
            p.save()
            p.setClipPath(path)
            p.setPen(QPen(QColor(COR["ambar_listra"]), 6))
            x = b.x() - b.height()
            while x < b.right():
                p.drawLine(QPointF(x, b.bottom()), QPointF(x + b.height(), b.y()))
                x += 16
            p.restore()
            p.setPen(QPen(QColor(COR["ambar"]), 1.2, Qt.DashLine))
            p.drawPath(path)
            texto, marca = QColor(COR["ambar_tinta"]), QColor(COR["ambar"])
        elif st in ("aprovado", "agendado_rede"):
            p.fillPath(path, QColor(COR["painel_2"]))
            p.setPen(QPen(cor, 2))
            p.drawPath(path)
            texto, marca = cor, cor
        elif st == "reprovado":
            p.fillPath(path, QColor(COR["cabecalho"]))
            texto, marca = QColor(COR["tinta_suave"]), QColor(COR["tinta_suave"])
        elif st == "erro":
            p.fillPath(path, QColor(COR["painel_2"]))
            p.setPen(QPen(QColor(COR["agora"]), 2, Qt.DashLine))
            p.drawPath(path)
            texto, marca = QColor(COR["agora"]), QColor(COR["agora"])
        elif st == "publicado":
            p.fillPath(path, QColor(COR["verde"]))
            texto, marca = QColor(COR["noite"]), QColor(COR["noite"])
        else:  # na_hora
            p.fillPath(path, cor)
            texto, marca = QColor(COR["noite"]), QColor(COR["noite"])
            p.setPen(QPen(QColor(COR["agora"]), 3))
            p.drawPath(path)
        if self.sel == q["id"]:
            p.setPen(QPen(QColor(COR["destaque_claro"]), 2))
            p.drawRoundedRect(b.adjusted(-4, -4, 4, 4), 8, 8)
        if self.sobre == q["id"] and self.sel != q["id"]:
            p.setPen(QPen(QColor(COR["borda"]), 1))
            p.drawRoundedRect(b.adjusted(-3, -3, 3, 3), 7, 7)
        # textos
        pad = 9
        p.setFont(fonte_tv(10, True))
        p.setPen(texto)
        hora = q["quando"][11:16]
        if b.height() <= 44:
            if st == "na_hora":
                desenhar_marca(p, b.x() + pad, b.y() + (b.height() - 10) / 2, st, marca)
                pad2 = pad + 15
            else:
                pad2 = pad
            led.desenhar(p, hora, b.x() + pad2, b.y() + (b.height() - 7 * 1.45) / 2, 1.45, texto.name())
            pad3 = pad2 + led.largura(hora, 1.45) + 7
            p.setFont(fonte_ui(10, True))
            fm = QFontMetrics(p.font())
            linha = fm.elidedText(q['titulo'] or q['projeto'], Qt.ElideRight, int(b.width() - pad - pad3))
            p.drawText(QRectF(b.x() + pad3, b.y(), b.width() - pad - pad3, b.height()), Qt.AlignLeft | Qt.AlignVCenter, linha)
            return
        led.desenhar(p, hora, b.x() + pad, b.y() + 8, 1.55, texto.name())
        p.setFont(fonte_tv(8.5, True))
        p.setPen(texto)
        p.drawText(QRectF(b.x() + pad + led.largura(hora, 1.55) + 6, b.y() + 5, b.width() - 2 * pad, 16), Qt.AlignLeft | Qt.AlignVCenter,
                   q['formato'].upper())
        if b.height() > 44:
            p.setFont(fonte_ui(11, True))
            fm = QFontMetrics(p.font())
            nome = fm.elidedText(q["titulo"] or q["projeto"], Qt.ElideRight, int(b.width() - 2 * pad))
            p.drawText(QRectF(b.x() + pad, b.y() + 22, b.width() - 2 * pad, 22), Qt.AlignLeft, nome)
        if b.height() > 62:
            desenhar_marca(p, b.x() + pad, b.bottom() - 19, st, marca)
            p.setFont(fonte_ui(10))
            p.drawText(QRectF(b.x() + pad + 15, b.bottom() - 25, b.width() - 2 * pad - 15, 20), Qt.AlignLeft | Qt.AlignVCenter,
                       STATUS_CURTO.get(st, st))
        if st == "reprovado":
            p.setPen(QPen(QColor(COR["tinta_suave"]), 1))
            p.drawLine(QPointF(b.x() + pad, b.y() + 14), QPointF(b.right() - pad, b.y() + 14))

    # ------------------------------------------------------------ interação
    def em(self, pos):
        for b, q in self.blocos:
            if b.contains(QPointF(pos)):
                return q
        return None

    def mouseMoveEvent(self, ev):
        q = self.em(ev.position())
        novo = q["id"] if q else None
        self.setCursor(Qt.PointingHandCursor if q else Qt.ArrowCursor)
        if novo != self.sobre:
            self.sobre = novo
            self.update()
            if q:
                QToolTip.showText(ev.globalPosition().toPoint(), f"{q['titulo'] or q['projeto']}\n{N.NOMES_REDE[q['rede']]} · "
                                  f"{q['quando'].replace('T', ' ')} · {STATUS_CURTO.get(q['status'])}", self)

    def leaveEvent(self, _):
        self.sobre = None
        self.update()

    def mousePressEvent(self, ev):
        q = self.em(ev.position())
        if q:
            self.escolhido.emit(q["id"])
