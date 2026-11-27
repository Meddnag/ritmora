# Ritmora: escolha do navegador (e do perfil) usado no login do Google e nas páginas de envio.
# Cada perfil do Chrome/Edge/Brave pode estar logado numa conta diferente; por isso o perfil também é escolhível.
import json, os, subprocess, webbrowser

try:
    import winreg
except ImportError:  # fora do Windows
    winreg = None

PADRAO = ""  # vazio = navegador padrão do sistema

# navegadores do tipo Chromium: (id, nome, exe relativo comum, pasta de dados em %LOCALAPPDATA%)
CHROMIUM = [
    ("chrome", "Google Chrome", r"Google\Chrome\Application\chrome.exe", r"Google\Chrome\User Data"),
    ("edge", "Microsoft Edge", r"Microsoft\Edge\Application\msedge.exe", r"Microsoft\Edge\User Data"),
    ("brave", "Brave", r"BraveSoftware\Brave-Browser\Application\brave.exe", r"BraveSoftware\Brave-Browser\User Data"),
    ("vivaldi", "Vivaldi", r"Vivaldi\Application\vivaldi.exe", r"Vivaldi\User Data"),
]
OUTROS = [
    ("firefox", "Mozilla Firefox", r"Mozilla Firefox\firefox.exe"),
    ("opera", "Opera", r"Programs\Opera\opera.exe"),
    ("operagx", "Opera GX", r"Programs\Opera GX\opera.exe"),
]


def _bases():
    return [os.environ.get(v) for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA") if os.environ.get(v)]


def _achar(rel):
    for b in _bases():
        p = os.path.join(b, rel)
        if os.path.isfile(p):
            return p
    return None


def _registro():
    """exes registrados em StartMenuInternet (pega instalações fora dos caminhos comuns)."""
    achados = {}
    if not winreg:
        return achados
    for raiz in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            k = winreg.OpenKey(raiz, r"SOFTWARE\Clients\StartMenuInternet")
        except OSError:
            continue
        i = 0
        while True:
            try:
                nome = winreg.EnumKey(k, i)
            except OSError:
                break
            i += 1
            try:
                cmd = winreg.QueryValue(k, nome + r"\shell\open\command")
            except OSError:
                continue
            exe = cmd.split('"')[1] if cmd.startswith('"') else cmd.split()[0]
            if os.path.isfile(exe):
                achados[os.path.basename(exe).lower()] = exe
    return achados


def _perfis(pasta_dados):
    """perfis de um navegador Chromium: [(diretório, nome mostrado)]."""
    arq = os.path.join(os.environ.get("LOCALAPPDATA", ""), pasta_dados, "Local State")
    try:
        cache = json.load(open(arq, encoding="utf-8"))["profile"]["info_cache"]
    except Exception:
        return []
    perfis = []
    for d, info in cache.items():
        nome = info.get("name") or d
        conta = info.get("user_name") or info.get("gaia_name")
        perfis.append((d, f"{nome} · {conta}" if conta and conta != nome else nome))
    return sorted(perfis, key=lambda x: (x[0] != "Default", x[1].lower()))


def listar():
    """[(id, rótulo)] com o padrão do sistema primeiro. id = "navegador" ou "navegador|perfil"."""
    reg = _registro()
    itens = [(PADRAO, "Navegador padrão do Windows")]
    for nid, nome, rel, dados in CHROMIUM:
        exe = _achar(rel) or reg.get(os.path.basename(rel).lower())
        if not exe:
            continue
        perfis = _perfis(dados)
        if len(perfis) <= 1:
            itens.append((nid, nome))
        else:
            itens += [(f"{nid}|{d}", f"{nome} — {rot}") for d, rot in perfis]
    for nid, nome, rel in OUTROS:
        if _achar(rel) or reg.get(os.path.basename(rel).lower()):
            itens.append((nid, nome))
    return itens


def _comando(escolha):
    """linha de comando (lista) para abrir uma URL no navegador escolhido, ou None para o padrão."""
    if not escolha:
        return None
    nid, _, perfil = escolha.partition("|")
    reg = _registro()
    for cid, _n, rel, _d in CHROMIUM:
        if cid == nid:
            exe = _achar(rel) or reg.get(os.path.basename(rel).lower())
            if not exe:
                return None
            return [exe] + ([f"--profile-directory={perfil}"] if perfil else []) + ["%s"]
    for cid, _n, rel in OUTROS:
        if cid == nid:
            exe = _achar(rel) or reg.get(os.path.basename(rel).lower())
            return [exe, "%s"] if exe else None
    return None


def nome_webbrowser(escolha):
    """registra o navegador escolhido no módulo webbrowser e devolve o nome a usar (None = padrão)."""
    cmd = _comando(escolha)
    if not cmd:
        return None
    webbrowser.register("ritmora", None, webbrowser.BackgroundBrowser(cmd))
    return "ritmora"


def abrir(url, escolha):
    cmd = _comando(escolha)
    if cmd:
        subprocess.Popen([url if a == "%s" else a for a in cmd])
    else:
        webbrowser.open(url)
