const campo = document.getElementById("chave");
const estado = document.getElementById("estado");

function mostrar(texto, tipo) {
  estado.textContent = texto;
  estado.className = tipo || "";
}

async function testar() {
  mostrar("Testando…");
  chrome.runtime.sendMessage({ tipo: "estado" }, (r) => {
    if (r && r.ok) mostrar(`Conectado ao Ritmora${r.dados.canal ? " · " + r.dados.canal : ""}.`, "bom");
    else mostrar((r && r.erro) || "Sem resposta.", "erro");
  });
}

chrome.storage.local.get("chave").then(({ chave }) => {
  if (chave) {
    campo.value = chave;
    testar();
  }
});

document.getElementById("salvar").addEventListener("click", async () => {
  await chrome.storage.local.set({ chave: campo.value.trim() });
  testar();
});
