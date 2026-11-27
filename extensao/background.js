// Ritmora Ajudante: fala com o Ritmora (127.0.0.1:47321) em nome das páginas.
// As páginas não falam direto com o Ritmora; só a extensão, com a chave guardada aqui.
const BASE = "http://127.0.0.1:47321";
const PEDACO = 4 * 1024 * 1024;

async function chave() {
  const { chave } = await chrome.storage.local.get("chave");
  return chave || "";
}

async function pedir(caminho, opcoes = {}) {
  const r = await fetch(BASE + caminho, {
    ...opcoes,
    headers: { "X-Ritmora-Token": await chave(), "Content-Type": "application/json", ...(opcoes.headers || {}) },
  });
  if (r.status === 403) throw new Error("Chave inválida. Cole a chave do Ritmora (Configurações) no ícone da extensão.");
  if (!r.ok) throw new Error(`O Ritmora respondeu ${r.status}.`);
  return r;
}

function paraBase64(buf) {
  const bytes = new Uint8Array(buf);
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

chrome.runtime.onMessage.addListener((msg, _de, responder) => {
  (async () => {
    try {
      if (msg.tipo === "estado") return responder({ ok: true, dados: await (await pedir("/estado")).json() });
      if (msg.tipo === "posts") return responder({ ok: true, dados: await (await pedir("/posts?rede=" + msg.rede)).json() });
      if (msg.tipo === "publicado")
        return responder({ ok: true, dados: await (await pedir("/publicado", { method: "POST", body: JSON.stringify({ id: msg.id, link: msg.link }) })).json() });
      if (msg.tipo === "nota")
        return responder({ ok: true, dados: await (await pedir("/nota", { method: "POST", body: JSON.stringify({ id: msg.id, texto: msg.texto }) })).json() });
      responder({ ok: false, erro: "pedido desconhecido" });
    } catch (e) {
      responder({ ok: false, erro: e.message.includes("Failed to fetch") ? "O Ritmora não está aberto neste computador." : e.message });
    }
  })();
  return true;
});

// arquivos grandes vão em pedaços por uma porta (mensagens comuns têm limite de tamanho)
chrome.runtime.onConnect.addListener((porta) => {
  if (porta.name !== "arquivo") return;
  porta.onMessage.addListener(async ({ id, qual, tamanho }) => {
    try {
      for (let ini = 0; ini < tamanho; ini += PEDACO) {
        const buf = await (await pedir(`/arquivo?id=${id}&qual=${qual}&ini=${ini}&tam=${PEDACO}`)).arrayBuffer();
        porta.postMessage({ pedaco: paraBase64(buf), feito: Math.min(ini + PEDACO, tamanho) });
      }
      porta.postMessage({ fim: true });
    } catch (e) {
      porta.postMessage({ erro: e.message.includes("Failed to fetch") ? "O Ritmora não está aberto neste computador." : e.message });
    }
  });
});

// O Ritmora pede para abrir as páginas de envio AQUI, no navegador e perfil onde a extensão está instalada.
// A extensão fica perguntando (/comandos espera até 20 s por um pedido); o alarme religa o ciclo se o navegador o pausar.
let ouvindo = false;

async function abrirPagina(url) {
  const aba = await chrome.tabs.create({ url, active: true });
  try {
    await chrome.windows.update(aba.windowId, { focused: true, drawAttention: true });
  } catch (_) {}
}

async function ouvirRitmora() {
  if (ouvindo) return;
  ouvindo = true;
  try {
    for (let i = 0; i < 40; i++) {
      if (!(await chave())) break;
      let r;
      try {
        r = await pedir("/comandos");
      } catch (_) {
        break; // Ritmora fechado ou chave errada: tenta de novo no próximo alarme
      }
      const { abrir } = await r.json();
      for (const url of abrir || []) {
        if (/^https:\/\/(studio\.youtube\.com|www\.tiktok\.com|www\.instagram\.com)\//.test(url)) await abrirPagina(url);
      }
    }
  } finally {
    ouvindo = false;
  }
}

chrome.alarms.create("ritmora", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((a) => a.name === "ritmora" && ouvirRitmora());
chrome.runtime.onStartup.addListener(ouvirRitmora);
chrome.runtime.onInstalled.addListener(ouvirRitmora);
chrome.storage.onChanged.addListener((m) => m.chave && ouvirRitmora());
ouvirRitmora();
