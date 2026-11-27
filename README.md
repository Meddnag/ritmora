# Ritmora

Agendador de posts para **YouTube, TikTok e Instagram**, com várias contas de canal, cada uma na sua repartição.
São duas peças, e cada uma tem o seu download:

| | O que é | Download |
|---|---|---|
| 🖥️ **Aplicativo** | O Ritmora para Windows: grade da semana, fila de aprovação, declarações, agenda e envio. | [`Ritmora-app-windows.zip`](https://github.com/Meddnag/ritmora/releases/latest/download/Ritmora-app-windows.zip) |
| 🧩 **Extensão** | O *Ritmora Ajudante* para Chrome, Edge e Brave: um painel nas páginas de envio que anexa o vídeo, preenche os textos e marca as declarações. | [`Ritmora-extensao-navegador.zip`](https://github.com/Meddnag/ritmora/releases/latest/download/Ritmora-extensao-navegador.zip) |

Todas as versões estão em [Releases](https://github.com/Meddnag/ritmora/releases).

---

## 🖥️ Aplicativo (Windows)

1. Baixe **Ritmora-app-windows.zip** e extraia numa pasta.
2. Abra **Ritmora.exe**. Ao fechar a janela, ele continua na bandeja, perto do relógio, vigiando a agenda.
3. Na coluna **CANAIS**, clique em **+ Novo canal** para cada canal. Pelo botão direito, **Configurações do canal** guarda as
   configurações daquele canal:
   - pasta da fila de produção, horários e modo de envio de cada rede;
   - navegador;
   - conta do YouTube;
   - chave da extensão.
4. **Importar fila** traz os vídeos prontos da pasta do canal aberto. Em cada vídeo, assista e marque você as declarações
   (IA e crianças). Depois clique em **Aprovar e agendar**.

Os seus dados (banco, configurações e login do Google) ficam na pasta `dados`, ao lado do `Ritmora.exe`. Eles **não** fazem
parte do zip nem do repositório. Para atualizar o Ritmora, troque só o `Ritmora.exe` e a pasta `_internal`.

**YouTube automático (opcional):** coloque o `client_secret.json` em `dados\`. Ele é um cliente OAuth do tipo "App para
computador", com a YouTube Data API v3 ativada no Google Cloud, e um só arquivo serve para todos os canais. Depois, nas
Configurações do canal, clique em **Conectar o YouTube**.

## 🧩 Extensão do navegador (Ritmora Ajudante)

1. Baixe **Ritmora-extensao-navegador.zip** e extraia numa pasta que não vá apagar.
2. Abra `chrome://extensions` (no Edge, `edge://extensions`; no Brave, `brave://extensions`) e ligue o **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação** e escolha a pasta extraída.
4. No Ritmora, abra **Configurações do canal**, vá em **Chave da extensão** e clique em **Copiar chave**. Depois clique no ícone da extensão, cole a chave e clique em
   **Salvar e testar**.

**Cada canal tem a sua chave.** Instale a extensão no navegador ou perfil logado naquele canal e cole a chave dele. Ela só
mostra e abre os posts desse canal. Quando você clica em **Enviar agora** no Ritmora, a página de envio abre nesse navegador.
A extensão nunca clica em publicar: quem confere e publica é você.

Para atualizar a extensão, extraia a versão nova por cima da pasta e clique no botão de recarregar em `chrome://extensions`.

---

## Código

- `ritmora/` é o aplicativo (Python 3.15 + PySide6). Para rodar: `.venv\Scripts\python Ritmora.pyw`.
- `extensao/` é a extensão (Manifest V3, sem etapa de build).
- O executável é gerado com PyInstaller pelo `Ritmora.spec`.
