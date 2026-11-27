// Ritmora Ajudante: painel flutuante nas páginas de envio.
// Faz só o que a pessoa manda (cada botão é uma ação) e NUNCA clica em publicar: quem publica é a pessoa.
(() => {
  if (window.__ritmora) return;
  window.__ritmora = true;

  const host = location.hostname;
  const REDE = host.includes("youtube") ? "youtube" : host.includes("tiktok") ? "tiktok" : "instagram";
  const NOME_REDE = { youtube: "YouTube", tiktok: "TikTok", instagram: "Instagram" }[REDE];

  // ------------------------------------------------------------ utilidades
  const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
  const pedir = (msg) => new Promise((r) => chrome.runtime.sendMessage(msg, (resp) => r(resp || { ok: false, erro: "sem resposta" })));

  function visivel(el) {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden";
  }

  // procura dentro de shadow roots também (o YouTube Studio usa web components)
  function todos(sel, raiz = document) {
    const achados = [...raiz.querySelectorAll(sel)];
    for (const el of raiz.querySelectorAll("*")) if (el.shadowRoot) achados.push(...todos(sel, el.shadowRoot));
    return achados;
  }

  async function aparecer(fn, ms = 8000) {
    const fim = Date.now() + ms;
    while (Date.now() < fim) {
      const v = fn();
      if (v) return v;
      await esperar(250);
    }
    return null;
  }

  function porTexto(seletor, textos) {
    const alvo = textos.map((t) => t.toLowerCase());
    return todos(seletor).find((el) => visivel(el) && alvo.some((t) => (el.textContent || "").trim().toLowerCase() === t));
  }

  // escreve num campo editável (contenteditable, input ou textarea) como se a pessoa digitasse
  function escrever(el, texto) {
    el.focus();
    if (el.isContentEditable) {
      document.execCommand("selectAll", false, null);
      document.execCommand("delete", false, null);
      document.execCommand("insertText", false, texto);
    } else {
      const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(proto, "value").set.call(el, texto);
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  async function baixar(post, qual, aoAvancar) {
    const info = post[qual];
    if (!info) throw new Error(qual === "video" ? "O vídeo deste post não foi encontrado no computador." : "Este post não tem capa.");
    return new Promise((resolve, reject) => {
      const partes = [];
      const porta = chrome.runtime.connect({ name: "arquivo" });
      porta.onMessage.addListener((m) => {
        if (m.erro) return reject(new Error(m.erro));
        if (m.pedaco) {
          const bin = atob(m.pedaco);
          const bytes = new Uint8Array(bin.length);
          for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
          partes.push(bytes);
          aoAvancar && aoAvancar(m.feito / info.tamanho);
        }
        if (m.fim) {
          porta.disconnect();
          const ext = info.nome.split(".").pop().toLowerCase();
          const tipo = { mp4: "video/mp4", mov: "video/quicktime", webm: "video/webm", jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png" }[ext] || "application/octet-stream";
          resolve(new File(partes, info.nome, { type: tipo }));
        }
      });
      porta.postMessage({ id: post.id, qual, tamanho: info.tamanho });
    });
  }

  function anexar(input, arquivo) {
    const dt = new DataTransfer();
    dt.items.add(arquivo);
    input.files = dt.files;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // ------------------------------------------------------------ ações por rede
  const ACOES = {
    youtube: {
      async video(post, prog) {
        let input = todos('input[type="file"]').find((i) => !(i.accept || "").includes("image"));
        if (!input) {
          const criar = todos("#create-icon, ytcp-button#create-icon")[0];
          if (criar) {
            criar.click();
            await esperar(600);
            const enviar = todos("tp-yt-paper-item#text-item-0, #text-item-0")[0];
            enviar && enviar.click();
          }
          input = await aparecer(() => todos('input[type="file"]').find((i) => !(i.accept || "").includes("image")));
        }
        if (!input) throw new Error("Não achei a janela de envio. Clique em Criar > Enviar vídeos e tente de novo.");
        anexar(input, await baixar(post, "video", prog));
        return "Vídeo anexado. Aguarde o YouTube carregar e clique em “Preencher textos”.";
      },
      async textos(post) {
        const titulo = await aparecer(() => todos("#title-textarea #textbox, ytcp-social-suggestions-textbox#title-textarea #textbox")[0]);
        if (!titulo) throw new Error("Os campos ainda não apareceram. Anexe o vídeo primeiro.");
        if (post.titulo) escrever(titulo, post.titulo.slice(0, 100));
        const desc = todos("#description-textarea #textbox")[0];
        if (desc && post.descricao) escrever(desc, post.descricao);
        let extra = "";
        if (post.tags.length) {
          const mais = todos("#toggle-button")[0];
          if (mais && !todos("#tags-container input, ytcp-free-text-chip-bar input").some(visivel)) {
            mais.click();
            await esperar(700);
          }
          const tags = todos("#tags-container input#text-input, ytcp-free-text-chip-bar input").find(visivel);
          if (tags) {
            tags.focus();
            escrever(tags, post.tags.join(", "));
            tags.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, bubbles: true }));
          } else extra = " Não achei o campo de tags; coloque à mão em “Mostrar mais”.";
        }
        return "Título e descrição preenchidos." + extra + " Confira na tela.";
      },
      async declaracoes(post) {
        const marcar = (nome) => {
          const r = todos(`tp-yt-paper-radio-button[name="${nome}"]`)[0];
          if (!r) return false;
          r.click();
          return true;
        };
        const feito = [];
        if (post.criancas !== null && post.criancas !== undefined)
          feito.push(marcar(post.criancas ? "VIDEO_MADE_FOR_KIDS_MFK" : "VIDEO_MADE_FOR_KIDS_NOT_MFK") ? "crianças" : "");
        if (post.ia !== null && post.ia !== undefined) {
          let ok = marcar(post.ia ? "VIDEO_HAS_ALTERED_CONTENT_YES" : "VIDEO_HAS_ALTERED_CONTENT_NO");
          if (!ok) {
            const mais = todos("#toggle-button")[0];
            if (mais) { mais.click(); await esperar(700); }
            ok = marcar(post.ia ? "VIDEO_HAS_ALTERED_CONTENT_YES" : "VIDEO_HAS_ALTERED_CONTENT_NO");
          }
          feito.push(ok ? "IA" : "");
        }
        const certos = feito.filter(Boolean);
        if (!certos.length) throw new Error("Não achei as perguntas. Anexe o vídeo e espere a tela de detalhes.");
        return `Marquei como você declarou no Ritmora: ${certos.join(" e ")}. Confira antes de avançar.`;
      },
      async capa(post, prog) {
        const input = todos('input[type="file"]').find((i) => (i.accept || "").includes("image"));
        if (!input) throw new Error("Não achei o campo da miniatura (pode exigir conta verificada).");
        anexar(input, await baixar(post, "thumb", prog));
        return "Capa enviada. Confira a miniatura.";
      },
      link() {
        const t = todos("a, span, div").map((e) => e.href || e.textContent || "").join(" ");
        const m = t.match(/https:\/\/(youtu\.be\/[\w-]{6,}|(www\.)?youtube\.com\/shorts\/[\w-]{6,})/);
        return m ? m[0] : "";
      },
    },

    tiktok: {
      async video(post, prog) {
        const input = await aparecer(() => todos('input[type="file"]').find((i) => (i.accept || "video").includes("video")));
        if (!input) throw new Error("Não achei o campo de envio. Abra a página de upload do TikTok Studio.");
        anexar(input, await baixar(post, "video", prog));
        return "Vídeo anexado. Quando a página de detalhes abrir, clique em “Preencher textos”.";
      },
      async textos(post) {
        const campo = await aparecer(() => todos('.public-DraftEditor-content, [contenteditable="true"]').find(visivel));
        if (!campo) throw new Error("A legenda ainda não apareceu. Anexe o vídeo e espere carregar.");
        escrever(campo, post.descricao || post.titulo);
        return "Legenda preenchida. Confira se as hashtags viraram links.";
      },
      async declaracoes(post) {
        if (post.ia === null || post.ia === undefined) throw new Error("Você ainda não declarou no Ritmora se tem IA.");
        const mais = porTexto("div, span, button", ["exibir mais", "mostrar mais", "show more"]);
        if (mais) { mais.click(); await esperar(800); }
        const rotulo = todos("div, span, label").find((el) => visivel(el) && el.children.length < 4 &&
          /gerado por ia|gerado por intelig|ai-generated|ai generated/i.test(el.textContent || ""));
        if (!rotulo) throw new Error("Não achei a opção “Conteúdo gerado por IA”. Abra “Exibir mais” e marque à mão.");
        let caixa = rotulo;
        let chave = null;
        for (let i = 0; i < 6 && caixa && !chave; i++, caixa = caixa.parentElement)
          chave = caixa.querySelector('[role="switch"], input[type="checkbox"]');
        if (!chave) throw new Error("Achei o texto da IA mas não a chave. Marque à mão.");
        const ligada = chave.getAttribute("aria-checked") === "true" || chave.checked === true;
        if (ligada !== !!post.ia) {
          chave.click();
          await esperar(700);
          const ativar = porTexto("button, div[role=button]", ["ativar", "turn on", "ligar"]);
          ativar && ativar.click();
        }
        return post.ia ? "Selo de conteúdo gerado por IA ligado." : "Selo de IA desligado, como você declarou.";
      },
      link() { return ""; },
    },

    instagram: {
      async video(post, prog) {
        let input = todos('input[type="file"]').find((i) => /video|\*/.test(i.accept || "video"));
        if (!input) {
          const criar = todos('svg[aria-label="Nova publicação"], svg[aria-label="New post"], svg[aria-label="Criar"]')[0];
          if (criar) { criar.closest("a, div[role=button], span")?.click(); await esperar(1200); }
          input = await aparecer(() => todos('input[type="file"]').find((i) => /video|\*/.test(i.accept || "video")));
        }
        if (!input) throw new Error("Não achei o envio. Clique em Criar (+) e tente de novo.");
        anexar(input, await baixar(post, "video", prog));
        return "Vídeo anexado. Ajuste o corte, avance até a legenda e clique em “Preencher textos”.";
      },
      async textos(post) {
        const campo = await aparecer(() => todos('div[aria-label*="legenda" i][contenteditable="true"], div[aria-label*="caption" i][contenteditable="true"], [contenteditable="true"]').find(visivel));
        if (!campo) throw new Error("A legenda ainda não apareceu. Avance até a tela da legenda.");
        escrever(campo, post.descricao || post.titulo);
        return "Legenda preenchida. Confira na tela.";
      },
      async declaracoes(post) {
        throw new Error(post.ia ? "No Instagram o rótulo de IA fica em “Configurações avançadas”; ligue à mão." : "Sem IA declarada: nada a marcar.");
      },
      link() {
        const m = location.href.match(/https:\/\/www\.instagram\.com\/(reel|p)\/[\w-]+/);
        return m ? m[0] : "";
      },
    },
  };

  // ------------------------------------------------------------ painel
  const LOGO_LED = "<svg class=\"logo\" xmlns=\"http://www.w3.org/2000/svg\" width=\"109.0\" height=\"18.2\" viewBox=\"0 0 109.0 18.2\" aria-label=\"Ritmora\"><g fill=\"#1b2246\"><circle cx=\"11.62\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"3.82\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"6.42\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"9.02\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"3.82\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"6.42\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"9.02\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"11.62\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"3.82\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"9.02\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"11.62\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"3.82\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"6.42\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"11.62\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"3.82\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"6.42\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"9.02\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"16.82\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"19.42\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"24.62\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"27.22\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"16.82\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"19.42\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"24.62\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"27.22\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"16.82\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"19.42\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"24.62\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"27.22\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"16.82\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"19.42\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"24.62\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"27.22\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"16.82\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"19.42\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"24.62\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"27.22\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"32.42\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"35.02\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"40.22\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"42.82\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"32.42\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"35.02\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"40.22\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"42.82\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"32.42\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"35.02\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"40.22\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"42.82\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"32.42\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"35.02\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"40.22\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"42.82\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"32.42\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"35.02\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"40.22\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"42.82\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"32.42\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"35.02\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"40.22\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"42.82\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"50.62\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"53.22\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"55.82\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"53.22\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"50.62\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"55.82\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"50.62\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"55.82\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"50.62\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"53.22\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"55.82\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"50.62\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"53.22\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"55.82\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"50.62\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"53.22\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"55.82\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"63.62\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"74.02\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"66.22\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"68.82\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"71.42\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"66.22\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"68.82\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"71.42\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"66.22\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"68.82\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"71.42\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"66.22\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"68.82\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"71.42\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"66.22\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"68.82\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"71.42\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"63.62\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"74.02\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"89.62\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"81.82\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"84.42\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"87.02\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"81.82\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"84.42\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"87.02\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"89.62\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"81.82\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"87.02\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"89.62\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"81.82\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"84.42\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"89.62\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"81.82\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"84.42\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"87.02\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"94.82\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"105.22\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"97.42\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"100.02\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"102.62\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"97.42\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"100.02\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"102.62\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"97.42\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"100.02\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"102.62\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"97.42\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"100.02\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"102.62\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"97.42\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"100.02\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"102.62\" cy=\"16.82\" r=\"1.22\"/></g><g fill=\"#eef1fa\"><circle cx=\"1.22\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"3.82\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"6.42\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"9.02\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"1.22\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"11.62\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"1.22\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"11.62\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"1.22\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"3.82\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"6.42\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"9.02\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"1.22\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"6.42\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"1.22\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"9.02\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"1.22\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"11.62\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"16.82\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"19.42\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"22.02\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"24.62\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"27.22\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"22.02\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"22.02\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"22.02\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"22.02\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"22.02\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"16.82\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"19.42\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"22.02\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"24.62\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"27.22\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"32.42\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"35.02\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"37.62\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"40.22\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"42.82\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"37.62\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"37.62\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"37.62\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"37.62\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"37.62\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"37.62\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"48.02\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"58.42\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"48.02\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"50.62\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"55.82\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"58.42\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"48.02\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"53.22\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"58.42\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"48.02\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"53.22\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"58.42\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"48.02\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"58.42\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"48.02\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"58.42\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"48.02\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"58.42\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"66.22\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"68.82\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"71.42\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"63.62\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"74.02\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"63.62\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"74.02\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"63.62\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"74.02\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"63.62\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"74.02\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"63.62\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"74.02\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"66.22\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"68.82\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"71.42\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"79.22\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"81.82\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"84.42\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"87.02\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"79.22\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"89.62\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"79.22\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"89.62\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"79.22\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"81.82\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"84.42\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"87.02\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"79.22\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"84.42\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"79.22\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"87.02\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"79.22\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"89.62\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"97.42\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"100.02\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"102.62\" cy=\"1.22\" r=\"1.22\"/><circle cx=\"94.82\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"105.22\" cy=\"3.82\" r=\"1.22\"/><circle cx=\"94.82\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"105.22\" cy=\"6.42\" r=\"1.22\"/><circle cx=\"94.82\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"97.42\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"100.02\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"102.62\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"105.22\" cy=\"9.02\" r=\"1.22\"/><circle cx=\"94.82\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"105.22\" cy=\"11.62\" r=\"1.22\"/><circle cx=\"94.82\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"105.22\" cy=\"14.22\" r=\"1.22\"/><circle cx=\"94.82\" cy=\"16.82\" r=\"1.22\"/><circle cx=\"105.22\" cy=\"16.82\" r=\"1.22\"/></g></svg>";
  const raiz = document.createElement("div");
  raiz.id = "ritmora-ajudante";
  const sombra = raiz.attachShadow({ mode: "open" });
  sombra.innerHTML = `
  <style>
    :host { all: initial; }
    .caixa { position: fixed; right: 18px; bottom: 18px; z-index: 2147483646; width: 300px; font: 13px/1.4 "Segoe UI", system-ui, sans-serif;
      color: #eef1fa; background: #10152c; border: 1px solid #2b335a; border-radius: 12px; box-shadow: 0 12px 32px rgba(0,0,0,.45); overflow: hidden; }
    .topo { --cor: #3a6bff; position: relative; display: flex; align-items: center; gap: 10px; padding: 10px 10px 10px 12px;
      background: radial-gradient(120% 140% at 0% 0%, color-mix(in srgb, var(--cor) 26%, transparent) 0%, transparent 55%),
        linear-gradient(180deg, #161d3c 0%, #10152c 100%);
      border-bottom: 1px solid #232a4a; cursor: move; user-select: none; }
    .topo.youtube { --cor: #ff7a3d } .topo.tiktok { --cor: #5ce1ff } .topo.instagram { --cor: #e07bff }
    .topo::after { content: ""; position: absolute; left: 12px; right: 12px; bottom: -1px; height: 1px;
      background: linear-gradient(90deg, transparent, var(--cor), transparent); opacity: .7; }
    .rito { width: 38px; height: 38px; flex: none; filter: drop-shadow(0 3px 6px rgba(0,0,0,.45)); transition: transform .25s ease; }
    .topo:hover .rito { transform: rotate(-6deg) translateY(-1px); }
    .titulo { display: grid; gap: 5px; min-width: 0; }
    .logo { display: block; }
    .rede { display: inline-flex; align-items: center; gap: 5px; width: max-content; font-size: 11px; font-weight: 600; letter-spacing: .04em;
      color: var(--cor); text-transform: uppercase; }
    .rede::before { content: ""; width: 6px; height: 6px; border-radius: 99px; background: var(--cor); box-shadow: 0 0 6px var(--cor); }
    .x { margin-left: auto; align-self: flex-start; width: 24px; height: 24px; display: grid; place-items: center; background: transparent;
      border: 1px solid transparent; border-radius: 6px; color: #9aa4c8; font-size: 15px; line-height: 1; cursor: pointer; }
    .x:hover { border-color: #2b335a; background: #171d38; color: #eef1fa; }
    .mini .topo { border-bottom-color: transparent; }
    .corpo { padding: 12px; display: grid; gap: 10px; }
    .mini .corpo { display: none; }
    select { width: 100%; background: #171d38; color: #eef1fa; border: 1px solid #2b335a; border-radius: 8px; padding: 6px 8px; font: inherit; }
    .info { color: #9aa4c8; font-size: 12px; }
    .info b { color: #eef1fa; font-weight: 600; }
    .botoes { display: grid; gap: 6px; }
    button.acao { display: flex; align-items: center; gap: 8px; width: 100%; text-align: left; background: #171d38; color: #eef1fa;
      border: 1px solid #2b335a; border-radius: 8px; padding: 8px 10px; font: inherit; cursor: pointer; }
    button.acao:hover:not(:disabled) { border-color: #3a6bff; }
    button.acao:disabled { opacity: .45; cursor: default; }
    button.acao .n { width: 18px; height: 18px; border-radius: 99px; background: #232a4a; display: grid; place-items: center; font-size: 11px; flex: none; }
    button.acao.ok .n { background: #3dffa0; color: #070a1c; }
    button.final { background: #3a6bff; border-color: #3a6bff; justify-content: center; font-weight: 600; }
    button.final:hover:not(:disabled) { background: #2c57e0; }
    .barra { height: 3px; background: #232a4a; border-radius: 3px; overflow: hidden; display: none; }
    .barra i { display: block; height: 100%; width: 0; background: #3a6bff; }
    .msg { font-size: 12px; color: #9aa4c8; min-height: 16px; }
    .msg.erro { color: #ff8a95; } .msg.bom { color: #3dffa0; }
    .aviso { font-size: 11px; color: #9aa4c8; border-top: 1px solid #232a4a; padding-top: 8px; }
  </style>
  <div class="caixa">
    <div class="topo ${REDE}">
      <img class="rito" data-rito alt="" src="${chrome.runtime.getURL("rito/atento.png")}">
      <div class="titulo">${LOGO_LED}<span class="rede">${NOME_REDE}</span></div>
      <button class="x" data-mini title="Minimizar">–</button></div>
    <div class="corpo">
      <select data-posts><option>Carregando…</option></select>
      <div class="info" data-info></div>
      <div class="botoes">
        <button class="acao" data-acao="video"><span class="n">1</span>Anexar vídeo</button>
        <button class="acao" data-acao="textos"><span class="n">2</span>Preencher textos</button>
        <button class="acao" data-acao="declaracoes"><span class="n">3</span>Marcar declarações</button>
        ${REDE === "youtube" ? '<button class="acao" data-acao="capa"><span class="n">4</span>Enviar capa</button>' : ""}
      </div>
      <div class="barra"><i></i></div>
      <div class="msg" data-msg></div>
      <button class="acao final" data-publiquei>Já publiquei</button>
      <div class="aviso">Confira tudo e clique em publicar você mesmo. O Ritmora nunca publica sozinho por aqui.</div>
    </div>
  </div>`;
  document.documentElement.appendChild(raiz);

  const $ = (s) => sombra.querySelector(s);
  const caixa = $(".caixa");
  // o Rito muda de cara conforme o que acontece: feliz quando um passo dá certo, alerta no erro, dormindo sem posts
  const humor = (h) => { $("[data-rito]").src = chrome.runtime.getURL(`rito/${h}.png`); };
  const msg = (t, tipo = "") => {
    const m = $("[data-msg]"); m.textContent = t; m.className = "msg " + tipo;
    humor(tipo === "erro" ? "alerta" : tipo === "bom" ? "feliz" : "atento");
  };
  const barra = (f) => { const b = $(".barra"); b.style.display = f === null ? "none" : "block"; $(".barra i").style.width = Math.round((f || 0) * 100) + "%"; };
  let posts = [];
  const atual = () => posts.find((p) => String(p.id) === $("[data-posts]").value);

  function mostrarInfo() {
    const p = atual();
    const info = $("[data-info]");
    if (!p) { info.textContent = ""; return; }
    const sim = (v) => (v === null || v === undefined ? "<b style='color:#ffc857'>não declarado</b>" : v ? "<b>sim</b>" : "<b>não</b>");
    const quando = p.quando ? new Date(p.quando).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "sem data";
    info.innerHTML = `${p.formato === "longo" ? "Vídeo longo" : "Short"} · ${quando}<br>IA: ${sim(p.ia)}` +
      (REDE === "youtube" ? ` · Crianças: ${sim(p.criancas)}` : "") + (p.video ? "" : "<br><b style='color:#ff8a95'>vídeo não encontrado</b>");
    sombra.querySelectorAll("button.acao[data-acao]").forEach((b) => b.classList.remove("ok"));
    ajustar();
  }

  // botões que não fazem sentido para o post escolhido ficam apagados
  function ajustar() {
    const p = atual();
    const capa = sombra.querySelector('[data-acao="capa"]');
    if (capa) capa.disabled = !p || !p.thumb;
    const video = sombra.querySelector('[data-acao="video"]');
    if (video) video.disabled = !p || !p.video;
  }

  async function carregar() {
    const r = await pedir({ tipo: "posts", rede: REDE });
    const sel = $("[data-posts]");
    if (!r.ok) {
      sel.innerHTML = "<option>Sem conexão com o Ritmora</option>";
      msg(r.erro, "erro");
      return;
    }
    posts = r.dados;
    // sem nada para postar nesta rede, o painel fica recolhido para não atrapalhar
    if (!posts.length || (REDE === "instagram" && !posts.some((p) => p.ativo || p.status === "na_hora"))) {
      caixa.classList.add("mini");
      $("[data-mini]").textContent = "+";
    }
    if (!posts.length) {
      sel.innerHTML = `<option>Nada aprovado para o ${NOME_REDE}</option>`;
      msg("Aprove um post no Ritmora para ele aparecer aqui.");
      humor("dormindo");
      return;
    }
    sel.innerHTML = posts.map((p) => `<option value="${p.id}">${p.ativo ? "▶ " : ""}${(p.titulo || p.projeto).replace(/</g, "&lt;").slice(0, 60)}</option>`).join("");
    msg(posts[0].ativo ? "Post aberto pelo Ritmora selecionado." : "");
    mostrarInfo();
  }

  $("[data-posts]").addEventListener("change", mostrarInfo);
  $("[data-mini]").addEventListener("click", () => {
    caixa.classList.toggle("mini");
    $("[data-mini]").textContent = caixa.classList.contains("mini") ? "+" : "–";
  });

  sombra.querySelectorAll("button.acao[data-acao]").forEach((b) =>
    b.addEventListener("click", async () => {
      const p = atual();
      if (!p) return msg("Escolha um post.", "erro");
      sombra.querySelectorAll("button.acao").forEach((x) => (x.disabled = true));
      msg(b.dataset.acao === "video" || b.dataset.acao === "capa" ? "Pegando o arquivo no Ritmora…" : "Trabalhando…");
      try {
        const texto = await ACOES[REDE][b.dataset.acao](p, (f) => barra(f));
        b.classList.add("ok");
        msg(texto, "bom");
      } catch (e) {
        msg(e.message, "erro");
      } finally {
        barra(null);
        sombra.querySelectorAll("button.acao").forEach((x) => (x.disabled = false));
        ajustar();
      }
    })
  );

  $("[data-publiquei]").addEventListener("click", async () => {
    const p = atual();
    if (!p) return;
    const achado = ACOES[REDE].link();
    const link = prompt(`Link do post publicado no ${NOME_REDE} (pode deixar vazio):`, achado);
    if (link === null) return;
    const r = await pedir({ tipo: "publicado", id: p.id, link });
    if (!r.ok) return msg(r.erro, "erro");
    msg("Marcado como publicado no Ritmora.", "bom");
    await carregar();
  });

  // arrastar pelo topo
  let arraste = null;
  $(".topo").addEventListener("mousedown", (e) => {
    if (e.target.closest("button")) return;
    const r = caixa.getBoundingClientRect();
    arraste = { dx: e.clientX - r.left, dy: e.clientY - r.top };
    e.preventDefault();
  });
  addEventListener("mousemove", (e) => {
    if (!arraste) return;
    caixa.style.left = Math.max(0, e.clientX - arraste.dx) + "px";
    caixa.style.top = Math.max(0, e.clientY - arraste.dy) + "px";
    caixa.style.right = caixa.style.bottom = "auto";
  });
  addEventListener("mouseup", () => (arraste = null));

  carregar();
})();
