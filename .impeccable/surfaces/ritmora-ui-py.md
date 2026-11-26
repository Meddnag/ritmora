---
version: 1
slug: "ritmora-ui-py"
primary_target: "ritmora/ui.py"
related_targets: []
---

# Ritmora: janela principal

Escopo: a janela principal do app desktop (grade da semana, fila, detalhe e aprovação). Modo: Operate.
Público e tarefa: criador solo (depois, outros criadores) planejando a semana de posts em YouTube, TikTok e Instagram e aprovando posts soltos em segundos. Conteúdo real: posts do canal Escala de Poder.
Restrições: Qt/PySide6 nativo no Windows; controles padrão da plataforma; declarações (IA, crianças) sempre marcadas pela pessoa; português do Brasil.
Referência fixada pelo dono (2026-11-26): post "Brands should feel alive" de @heydamir: chão noturno azul-escuro, auroras de cobalto, mascote cubo-robô com rosto de LED em matriz de pontos, tipografia de pontos, paleta Paper/Night/Graphite/Cobalt/Sky/Dawn/Spark. Ela substitui o visual claro de revista de programação; a estrutura da grade da semana continua.

## Direction contract

THESIS: Um agendador que parece vivo: o mascote Rito, um cubinho com rosto de LED, mostra no rosto o estado da agenda, e a semana é uma grade de canais acesa sobre a noite. Recusa o painel SaaS cinza e sem personalidade.

OWN-WORLD: Chão Night #070a1c com auroras de cobalto (#2f5bff a #8fb4ff) pintadas só atrás da grade e do mascote; painéis Graphite #11162e com cantos de 14 px; texto Paper #eef1fa. Matriz de pontos (LED) para o logotipo, o relógio, os dias da grade e os números; Segoe UI para o resto. Cores por canal: YouTube coral #ff6b7d, TikTok céu #7cc7ff, Instagram aurora #c08bff. Estados: aguardando âmbar listrado #ffc857, publicado Spark #3dffa0, na hora vermelho #ff4d5e, cada um com forma própria.

STORY: Abre, o Rito diz de cara se está tudo bem; a grade mostra buracos, pendências e o que está na hora. Clica num bloco, revisa e aprova na gaveta.

FIRST VIEWPORT: Barra superior com o Rito (40 px) e RITMORA em LED à esquerda, abas, e à direita o relógio em LED com o próximo post e Importar fila em cobalto. Grade de 7 dias com dias em LED, linha do agora; gaveta embaixo com capa, legenda, data, declarações e Aprovar e agendar.

FORM: referência fixada pelo dono, aplicada sobre a grade de programação (posição 1 da minha lista); seed:8bd72001955b4fb1.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
