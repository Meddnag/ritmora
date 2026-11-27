# Ritmora: envio para as redes. Dois modos por rede:
#  - "assistido": na hora marcada o Ritmora abre a página de envio, copia a legenda e mostra o arquivo; você confirma o envio.
#  - "api": envio automático pela API oficial (YouTube Data API v3 já pronto; Instagram e TikTok exigem app aprovado pela rede).
import os, subprocess

from . import navegador as NAV
from . import nucleo as N
from datetime import datetime

PAGINA_ENVIO = {
    "youtube": "https://studio.youtube.com/channel/UC/videos/upload?d=ud",
    "tiktok": "https://www.tiktok.com/tiktokstudio/upload",
    "instagram": "https://www.instagram.com/",
}


def mostrar_arquivo(caminho):
    if caminho and os.path.exists(caminho):
        subprocess.Popen(["explorer", "/select,", os.path.normpath(caminho)])


def texto_para_copiar(p):
    partes = []
    if p["rede"] == "youtube" and p["titulo"]:
        partes.append(p["titulo"])
        partes.append("")
    partes.append(p["descricao"] or "")
    return "\n".join(partes).strip()


def assistido(p, copiar, navegador=NAV.PADRAO):
    """Prepara o envio manual: abre a página da rede, copia o texto e seleciona o vídeo no Explorer."""
    copiar(texto_para_copiar(p))
    NAV.abrir(PAGINA_ENVIO[p["rede"]], navegador)
    mostrar_arquivo(p["video"])


# ---------------------------------------------------------------- YouTube (API oficial)
ESCOPOS_YT = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


def youtube_servico(pasta_dados, interativo=False, navegador=NAV.PADRAO):
    """Serviço autenticado. O login é feito pelo próprio Google no navegador (o Ritmora nunca vê a senha).
    Precisa de dados/client_secret.json (cliente OAuth "App para computador" criado no Google Cloud pelo dono do canal)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    tok = os.path.join(pasta_dados, "youtube_token.json")
    cli = os.path.join(N.DADOS, "client_secret.json")  # um só cliente OAuth serve para todos os canais
    cred = Credentials.from_authorized_user_file(tok, ESCOPOS_YT) if os.path.exists(tok) else None
    if cred and cred.expired and cred.refresh_token:
        cred.refresh(Request())
    if not cred or not cred.valid:
        if not interativo:
            raise RuntimeError("YouTube não conectado. Abra Configurações > Conectar YouTube.")
        if not os.path.exists(cli):
            raise RuntimeError(f"Falta o arquivo client_secret.json em {N.DADOS}.")
        cred = InstalledAppFlow.from_client_secrets_file(cli, ESCOPOS_YT).run_local_server(
            port=0, open_browser=True, browser=NAV.nome_webbrowser(navegador))
    open(tok, "w").write(cred.to_json())
    return build("youtube", "v3", credentials=cred, cache_discovery=False)


def youtube_conectado(pasta_dados):
    return os.path.exists(os.path.join(pasta_dados, "youtube_token.json"))


def youtube_enviar(p, pasta_dados, progresso=None):
    """Envia o vídeo já agendado (publishAt): o próprio YouTube publica na hora, mesmo com o PC desligado."""
    from googleapiclient.http import MediaFileUpload
    yt = youtube_servico(pasta_dados)
    quando = datetime.fromisoformat(p["quando"]).astimezone()
    futuro = quando > datetime.now().astimezone()
    corpo = {
        "snippet": {"title": p["titulo"][:100], "description": p["descricao"] or "",
                    "tags": [t.strip() for t in (p["tags"] or "").split(",") if t.strip()], "categoryId": "20"},
        "status": {"privacyStatus": "private" if futuro else "public", "selfDeclaredMadeForKids": bool(p["criancas"]),
                   "containsSyntheticMedia": bool(p["ia"])},
    }
    if futuro:
        corpo["status"]["publishAt"] = quando.isoformat()
    midia = MediaFileUpload(p["video"], chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=corpo, media_body=midia)
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st and progresso:
            progresso(int(st.progress() * 100))
    vid = resp["id"]
    if p["thumb"] and os.path.exists(p["thumb"]):
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(p["thumb"])).execute()
    link = f"https://youtube.com/shorts/{vid}" if p["formato"] == "short" else f"https://youtu.be/{vid}"
    return link, futuro


# ---------------------------------------------------------------- canal conectado (banner do topo)
def _arquivo_canal(pasta_dados):
    return os.path.join(pasta_dados, "canal.json")


def canal_salvo(pasta_dados):
    """Nome e foto do canal conectado, guardados na última consulta. None quando nenhuma conta está conectada."""
    import json
    if not youtube_conectado(pasta_dados):
        return None
    try:
        with open(_arquivo_canal(pasta_dados), encoding="utf-8") as f:
            d = json.load(f)
        return d if d.get("nome") else None
    except (OSError, ValueError):
        return None


def youtube_canal(pasta_dados):
    """Pergunta ao YouTube qual canal está conectado e guarda nome e foto em dados/canal.json."""
    import json, urllib.request
    yt = youtube_servico(pasta_dados)
    itens = yt.channels().list(part="snippet", mine=True).execute().get("items") or []
    if not itens:
        raise RuntimeError("A conta conectada não tem canal no YouTube.")
    sn = itens[0]["snippet"]
    d = {"id": itens[0]["id"], "nome": sn.get("title", ""), "foto": ""}
    url = ((sn.get("thumbnails") or {}).get("default") or {}).get("url")
    if url:
        foto = os.path.join(pasta_dados, "canal_foto.jpg")
        try:
            with urllib.request.urlopen(url, timeout=15) as r, open(foto, "wb") as f:
                f.write(r.read())
            d["foto"] = foto
        except OSError:
            pass
    with open(_arquivo_canal(pasta_dados), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    return d
