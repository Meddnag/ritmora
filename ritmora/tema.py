# Ritmora: tema noturno "vivo" (chão noturno, aurora na cor de destaque, painéis grafite, LED em pontos).
# A cor de destaque é escolhida pela pessoa (Configurações > Cor do Ritmora); tudo que brilha segue ela.
from PySide6.QtGui import QColor, QFont

CORES_DESTAQUE = {
    # cores de destaque longe das cores de estado (âmbar aguardando, verde publicado, vermelho na hora)
    "cobalto": ("Cobalto", "#3a6bff", "#8fb4ff"),
    "indigo": ("Índigo", "#5b4dff", "#a9a2ff"),
    "grafite": ("Grafite", "#5a6178", "#c3c8d8"),
    "gelo": ("Gelo", "#5d6f9e", "#d6def5"),
}

COR = {
    "noite": "#070a1c",
    "painel": "#10152c",
    "painel_2": "#171d38",
    "cabecalho": "#141a34",
    "hoje": "#151c3c",
    "fio": "#232a4a",
    "borda": "#2b335a",
    "tinta": "#eef1fa",
    "tinta_suave": "#9aa4c8",
    "agora": "#ff4d5e",
    "ambar": "#ffc857",
    "ambar_fundo": "#2a2414",
    "ambar_listra": "#3a3118",
    "ambar_tinta": "#ffd98a",
    "youtube": "#ff7a3d",
    "tiktok": "#5ce1ff",
    "instagram": "#e07bff",
    "verde": "#3dffa0",
    "led_apagado": "#151b36",
}

FAMILIA_TV = "Segoe UI"
FAMILIA_UI = "Segoe UI"


def definir_destaque(chave):
    nome, forte, claro = CORES_DESTAQUE.get(chave, CORES_DESTAQUE["cobalto"])
    COR["destaque"], COR["destaque_claro"] = forte, claro
    COR["destaque_hover"] = QColor(forte).lighter(115).name()


definir_destaque("cobalto")


def cor_rede(rede):
    return QColor(COR.get(rede, COR["destaque"]))


def fonte_tv(pt, negrito=False):
    """Rótulos e metadados: Segoe UI com algarismos tabulares (os números de destaque vão em LED)."""
    f = QFont(FAMILIA_UI)
    f.setPointSizeF(pt)
    f.setWeight(QFont.DemiBold if negrito else QFont.Normal)
    f.setLetterSpacing(QFont.PercentageSpacing, 103)
    try:
        f.setFeature(QFont.Tag("tnum"), 1)
    except Exception:
        pass
    return f


def fonte_ui(pt, negrito=False):
    f = QFont(FAMILIA_UI)
    f.setPointSizeF(pt)
    f.setWeight(QFont.DemiBold if negrito else QFont.Normal)
    return f


def estilo():
    C = COR
    return f"""
QWidget {{ background: transparent; color: {C['tinta']}; font-family: 'Segoe UI'; font-size: 10pt; }}
QMainWindow, QDialog, QWidget#raiz {{ background: {C['noite']}; }}
QToolTip {{ background: {C['painel_2']}; color: {C['tinta']}; border: 1px solid {C['borda']}; padding: 6px 8px; }}
QFrame#topo {{ background: {C['noite']}; border-bottom: 1px solid {C['fio']}; }}
QFrame#reparticoes {{ background: {C['noite']}; border-right: 1px solid {C['fio']}; }}
QPushButton#novoCanal {{ background: transparent; color: {C['tinta_suave']}; border: 1px dashed {C['borda']}; border-radius: 10px;
    padding: 9px 10px; font-weight: 600; }}
QPushButton#novoCanal:hover {{ color: {C['tinta']}; border-color: {C['destaque_claro']}; background: {C['painel']}; }}
QFrame#bannerCanal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C['painel_2']}, stop:1 {C['noite']});
    border: 1px solid {C['borda']}; border-radius: 21px; }}
QLabel#bannerRotulo {{ color: {C['youtube']}; font-size: 7pt; font-weight: 700; letter-spacing: 1px; }}
QLabel#bannerNome {{ color: {C['tinta']}; font-size: 10.5pt; font-weight: 600; }}
QLabel#proximo {{ color: {C['tinta_suave']}; }}
QPushButton#aba {{ background: transparent; color: {C['tinta_suave']}; border: none; border-radius: 8px; padding: 7px 14px;
    font-family: '{FAMILIA_TV}'; font-size: 10.5pt; }}
QPushButton#aba:hover {{ background: {C['painel_2']}; color: {C['tinta']}; }}
QPushButton#aba:checked {{ background: {C['painel_2']}; color: {C['tinta']}; font-weight: 600; }}
QPushButton {{ background: {C['painel_2']}; color: {C['tinta']}; border: 1px solid {C['borda']}; border-radius: 8px; padding: 8px 14px; }}
QPushButton:hover {{ border-color: {C['destaque_claro']}; }}
QPushButton:focus {{ border: 2px solid {C['destaque_claro']}; }}
QPushButton:disabled {{ color: #6f78a6; background: {C['painel']}; border-color: {C['fio']}; }}
QPushButton#primario {{ background: {C['destaque']}; color: #ffffff; border: none; font-weight: 700; padding: 9px 18px; }}
QPushButton#primario:hover {{ background: {C['destaque_hover']}; }}
QPushButton#primario:disabled {{ background: {C['painel_2']}; color: #5a6390; }}
QPushButton#perigo {{ color: {C['agora']}; border-color: #4a2333; }}
QPushButton#perigo:hover {{ border-color: {C['agora']}; }}
QPushButton#semana {{ background: transparent; border: 1px solid {C['borda']}; padding: 5px 10px; font-family: '{FAMILIA_TV}'; }}
QLineEdit, QPlainTextEdit, QDateTimeEdit, QComboBox, QSpinBox, QTimeEdit {{ background: {C['noite']}; color: {C['tinta']};
    border: 1px solid {C['borda']}; border-radius: 8px; padding: 6px 8px; selection-background-color: {C['destaque']};
    selection-color: #ffffff; }}
QLineEdit:focus, QPlainTextEdit:focus, QDateTimeEdit:focus, QComboBox:focus, QSpinBox:focus, QTimeEdit:focus {{
    border: 2px solid {C['destaque_claro']}; }}
QComboBox QAbstractItemView {{ background: {C['painel_2']}; color: {C['tinta']}; selection-background-color: {C['destaque']}; }}
QCalendarWidget QWidget {{ background: {C['painel_2']}; color: {C['tinta']}; }}
QLabel#rotulo {{ color: {C['tinta_suave']}; font-family: '{FAMILIA_TV}'; font-size: 9pt; font-weight: 600; letter-spacing: 1px; padding-top: 3px; min-height: 16px; }}
QLabel#titulo_post {{ font-size: 14pt; font-weight: 600; }}
QFrame#gaveta {{ background: {C['painel']}; border-top: 1px solid {C['fio']}; }}
QFrame#declara {{ background: {C['noite']}; border: 1px solid {C['borda']}; border-radius: 10px; }}
QFrame#declara[falta="true"] {{ border: 2px solid {C['ambar']}; }}
QLabel#dica {{ color: {C['tinta_suave']}; font-size: 8.5pt; }}
QLabel#contador {{ font-size: 8.5pt; }}
QLabel#aviso_dec {{ color: {C['ambar_tinta']}; }}
QPushButton#motivo {{ background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 4px 10px; color: {C['agora']}; font-weight: 600; text-align: left; }}
QPushButton#motivo:hover {{ border-color: {C['agora']}; }}
QPushButton#motivo[tom="pendente"] {{ color: {C['ambar_tinta']}; }}
QPushButton#motivo[tom="pendente"]:hover {{ border-color: {C['ambar']}; }}
QPushButton#motivo[tom="ok"] {{ color: {C['verde']}; }}
QListWidget {{ background: {C['painel']}; border: 1px solid {C['fio']}; border-radius: 12px; outline: none; }}
QListWidget::item {{ border-bottom: 1px solid {C['fio']}; }}
QListWidget::item:selected {{ background: {C['painel_2']}; }}
QListWidget::item:hover {{ background: {C['hoje']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {C['borda']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {C['borda']}; border-radius: 5px; min-width: 30px; }}
QSplitter::handle {{ background: {C['fio']}; }}
QRadioButton {{ spacing: 6px; }}
QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 8px; border: 2px solid {C['destaque_claro']}; background: {C['noite']}; }}
QRadioButton::indicator:checked {{ background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 {C['destaque_claro']},
    stop:0.5 {C['destaque_claro']}, stop:0.56 {C['noite']}, stop:1 {C['noite']}); }}
QStatusBar {{ background: {C['noite']}; color: {C['tinta_suave']}; border-top: 1px solid {C['fio']}; }}
QMenu {{ background: {C['painel_2']}; border: 1px solid {C['borda']}; }}
QMenu::item:selected {{ background: {C['destaque']}; }}
"""


ESTILO = estilo()
