---
name: Ritmora
description: Agendador de posts de vídeo que parece vivo, uma grade de canais acesa sobre a noite.
colors:
  noite: "#070a1c"
  painel: "#10152c"
  painel-2: "#171d38"
  cabecalho: "#141a34"
  hoje: "#151c3c"
  fio: "#232a4a"
  borda: "#2b335a"
  tinta: "#eef1fa"
  tinta-suave: "#9aa4c8"
  led-apagado: "#151b36"
  destaque-cobalto: "#3a6bff"
  destaque-cobalto-claro: "#8fb4ff"
  destaque-indigo: "#5b4dff"
  destaque-indigo-claro: "#a9a2ff"
  destaque-gelo: "#5d6f9e"
  destaque-gelo-claro: "#d6def5"
  destaque-grafite: "#5a6178"
  destaque-grafite-claro: "#c3c8d8"
  estado-agora: "#ff4d5e"
  estado-ambar: "#ffc857"
  estado-ambar-fundo: "#2a2414"
  estado-ambar-listra: "#3a3118"
  estado-ambar-tinta: "#ffd98a"
  estado-verde: "#3dffa0"
  rede-youtube: "#ff7a3d"
  rede-tiktok: "#5ce1ff"
  rede-instagram: "#e07bff"
typography:
  display:
    fontFamily: "LED 5x7 em pontos (desenhada em ritmora/led.py)"
    fontSize: "21px"
    lineHeight: 1
    letterSpacing: "1 ponto entre caracteres"
  led-cabecalho:
    fontFamily: "LED 5x7 em pontos (desenhada em ritmora/led.py)"
    fontSize: "18.2px"
    lineHeight: 1
  led-numero:
    fontFamily: "LED 5x7 em pontos (desenhada em ritmora/led.py)"
    fontSize: "11px"
    lineHeight: 1
  headline:
    fontFamily: "Segoe UI, sans-serif"
    fontSize: "14pt"
    fontWeight: 600
  title:
    fontFamily: "Segoe UI, sans-serif"
    fontSize: "13pt"
    fontWeight: 600
  body:
    fontFamily: "Segoe UI, sans-serif"
    fontSize: "10pt"
    fontWeight: 400
  meta:
    fontFamily: "Segoe UI, sans-serif"
    fontSize: "9pt"
    fontWeight: 400
    letterSpacing: "0.03em"
    fontFeature: "tnum"
  label:
    fontFamily: "Segoe UI, sans-serif"
    fontSize: "9pt"
    fontWeight: 600
    letterSpacing: "1px"
rounded:
  capa: "4px"
  bloco: "6px"
  controle: "8px"
  caixa: "10px"
  lista: "12px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "14px"
  lg: "20px"
components:
  button-primario:
    backgroundColor: "{colors.destaque-cobalto}"
    textColor: "#ffffff"
    rounded: "{rounded.controle}"
    padding: "9px 18px"
  button-padrao:
    backgroundColor: "{colors.painel-2}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.controle}"
    padding: "8px 14px"
  button-perigo:
    backgroundColor: "{colors.painel-2}"
    textColor: "{colors.estado-agora}"
    rounded: "{rounded.controle}"
    padding: "8px 14px"
  aba:
    backgroundColor: "transparent"
    textColor: "{colors.tinta-suave}"
    rounded: "{rounded.controle}"
    padding: "7px 14px"
  aba-ativa:
    backgroundColor: "{colors.painel-2}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.controle}"
    padding: "7px 14px"
  campo:
    backgroundColor: "{colors.noite}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.controle}"
    padding: "6px 8px"
  caixa-declaracoes:
    backgroundColor: "{colors.noite}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.caixa}"
    padding: "12px 14px"
  bloco-post:
    backgroundColor: "{colors.painel-2}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.bloco}"
    padding: "9px"
  barra-topo:
    backgroundColor: "{colors.noite}"
    textColor: "{colors.tinta}"
    height: "68px"
    padding: "0 20px"
---

# Design System: Ritmora

## Overview

**Creative North Star: "A Grade Acesa na Noite"**

O Ritmora é um painel noturno vivo: um chão azul quase preto, painéis grafite azulados por cima, e uma aurora na cor de destaque pintada só atrás da grade da semana e do mascote. A semana é uma grade de programação, com cada rede como um canal (linha) e cada dia como uma coluna; os posts são blocos acesos no seu horário. O mascote Rito, um cubinho com tela de LED, mostra no rosto o estado da agenda antes de qualquer texto.

A personalidade vem de três materiais próprios: a matriz de pontos (LED 5x7) para números e cabeçalhos, a aurora radial que segue a cor de destaque escolhida pela pessoa, e o Rito. Todo o resto é Qt nativo e contido: Segoe UI, cantos de 8 px, fios de 1 px, nenhuma sombra. A densidade é de ferramenta de trabalho: a gaveta de revisão e aprovação fica sempre visível abaixo da grade.

A identidade é separada do canal Escala de Poder: o amarelo e preto do canal não entram no Ritmora. O painel SaaS cinza e sem personalidade é a anti-referência confirmada.

**Key Characteristics:**
- Chão noturno (noite) com painéis em dois tons de grafite azulado e fios de 1 px.
- Aurora radial na cor de destaque, só atrás da grade e do Rito.
- LED em matriz de pontos para logotipo, relógio, dias e números de destaque; Segoe UI para todo o resto.
- Cada estado de post tem cor e forma próprias, legível sem depender da cor.
- Cor de destaque escolhida pela pessoa (Cobalto, Índigo, Gelo, Grafite); tudo que brilha segue ela.
- Plano, sem sombras: profundidade por tom, aurora e brilho de LED.

## Colors

Uma noite azul fria com quatro famílias de cor separadas por função: destaque (marca e interação), estado (o que o post precisa), rede (de onde o post é) e neutros noturnos.

### Primary
- **Cobalto** (destaque-cobalto, com destaque-cobalto-claro): destaque padrão. O forte preenche o botão primário (Importar fila, Aprovar e agendar), a seleção de texto e o item ativo de menu, e tinge a aurora da grade e a barra de 2 px sob o dia de hoje. O claro acende o relógio em LED, o dia de hoje no cabeçalho, o anel de seleção do bloco, o foco dos campos e botões, os rádios e os links. O hover do primário é o forte clareado 15%.
- **Alternativas selecionáveis** (Configurações > Cor do Ritmora): Índigo (destaque-indigo / -claro), Gelo (destaque-gelo / -claro) e Grafite (destaque-grafite / -claro). Cada uma é um par forte + claro que substitui o Cobalto em todos os papéis acima; nenhuma outra cor muda.

### Secondary
- **Cores de estado**: Vermelho do Agora (estado-agora) para "na hora", erro, a linha e o ponto do agora, e o botão Reprovar. Âmbar (estado-ambar, com estado-ambar-fundo, estado-ambar-listra e estado-ambar-tinta) para "aguardando aprovação" e para a caixa de declarações que falta marcar. Verde Spark (estado-verde) para "publicado" e para "Tudo em dia".

### Tertiary
- **Cores de rede**: Coral YouTube (rede-youtube), Céu TikTok (rede-tiktok), Aurora Instagram (rede-instagram). Marcam a faixa vertical de 6 px de cada canal na grade, o nome da rede nos metadados da Fila, o contorno dos blocos aprovados/agendados e o preenchimento do bloco "na hora".

### Neutral
- **Noite** (noite): o chão da janela, a barra superior, o fundo dos campos e da caixa de declarações, e o texto sobre blocos preenchidos (publicado, na hora).
- **Painel** (painel): a grade e a gaveta; **Painel 2** (painel-2): botões, aba ativa, coluna de hoje no cabeçalho, blocos com contorno, item selecionado de lista, menus e dicas.
- **Cabeçalho** (cabecalho): faixa dos dias e da coluna CANAL, bloco reprovado, fundo da capa vazia. **Hoje** (hoje): véu de 60/255 sobre a coluna do dia atual e hover de lista.
- **Fio** (fio): toda linha de 1 px (grade, divisórias, barra de status). **Borda** (borda): contorno de botões, campos, molduras e alça da rolagem.
- **Tinta** (tinta): texto principal e logotipo em LED. **Tinta suave** (tinta-suave): metadados, rótulos, dias que não são hoje.
- **LED apagado** (led-apagado): os pontos desligados do relógio e do dia de hoje, que deixam a matriz visível.

### Named Rules
**The Estado Tem Forma Rule.** Cada estado de post tem cor E forma próprias, e a forma sozinha precisa bastar: aguardando = listras diagonais âmbar com contorno tracejado e marca de meio círculo; na agenda = contorno de 2 px na cor da rede e círculo vazio; agendado na rede = contorno na cor da rede e círculo com ponto; na hora = bloco cheio na cor da rede com borda vermelha de 3 px e triângulo cheio; publicado = bloco verde cheio e círculo com visto; erro = contorno vermelho tracejado e X; reprovado = bloco apagado, texto riscado e círculo cortado. Um estado novo só entra com cor e forma novas.

**The Destaque Distante Rule.** Toda cor de destaque fica a cerca de 40° de matiz ou mais das cores de estado (âmbar, verde, vermelho) e das cores de rede (coral, céu, aurora). O destaque marca a interface; ele nunca pode ser lido como um estado ou como uma rede.

**The Tudo Que Brilha Segue o Destaque Rule.** Aurora, relógio, dia de hoje, anel de seleção, foco e botão primário usam o par de destaque ativo, nunca um azul fixo.

## Typography

**Display Font:** LED 5x7 em matriz de pontos (fonte própria desenhada com QPainter em ritmora/led.py)
**Body Font:** Segoe UI (com sans-serif do sistema)
**Label/Mono Font:** Segoe UI com algarismos tabulares (tnum) e espaçamento de 103%

**Character:** A matriz de pontos é a voz da máquina que conta o tempo: horas, dias e contagens acendem como um painel de LED. A Segoe UI é a voz da pessoa: títulos, legendas, rótulos e botões, nativa e calma.

### Hierarchy
- **Display** (LED, passo 3.0 px, 21 px de altura): o logotipo RITMORA na barra superior. O relógio usa passo 3.2 com os pontos apagados à mostra.
- **LED cabeçalho** (passo 2.6, cerca de 18 px de altura): os dias da grade (QUI 26) e CANAL.
- **LED número** (passo 1.55 a 1.6, cerca de 11 px): a hora dentro do bloco e a contagem de posts por canal.
- **Headline** (600, 14pt): título do post na gaveta.
- **Title** (600, 13pt): título da aba (Semana de 26/11 a 02/12/2026); nome do canal na grade em 600, 12.5pt; título no bloco em 600, 11pt.
- **Body** (400, 10pt): texto da interface, campos, botões, legendas.
- **Meta** (400 ou 600, 8.5 a 9pt, tnum, 103%): formato (SHORT, LONGO), metadados da Fila em caixa alta.
- **Label** (600, 9pt, 1px de espaçamento, CAIXA ALTA): rótulos de campo da gaveta (PUBLICAR EM, DESCRIÇÃO E LEGENDA).

### Named Rules
**The LED Conta, Segoe Fala Rule.** LED é para números e cabeçalhos que ficam sozinhos (logotipo, relógio, dias, horas de bloco, contagens). Todo o resto é Segoe UI, inclusive números dentro de frases ("Próximo post em 3 h 54 min"), que usam algarismos tabulares. A fonte LED só tem A-Z, 0-9 e : / - .; acentos viram a letra base.

## Layout

Janela de no mínimo 1100 x 640, aberta em 1440 x 900. Três faixas verticais: barra superior de 68 px (margem lateral de 20 px, espaço de 10 px entre itens), miolo com a grade e gaveta embaixo, separadas por um divisor de 1 px que não colapsa. A gaveta tem sempre a altura da sua sugestão; a grade fica com o resto.

A grade reserva 150 px à esquerda para a coluna CANAL, 44 px de cabeçalho, sete colunas iguais e três faixas iguais (YouTube, TikTok, Instagram). Os blocos entram com 8 px de recuo dentro da célula e 6 px entre si; abaixo de 44 px de altura o bloco vira uma linha só.

A gaveta tem três colunas com 20 px entre elas: capa de 90 x 160 com Assistir e Mostrar arquivo, o texto editável no meio (peso 3) e a coluna de decisão fixa em 330 px (data, declarações, Aprovar e agendar, ações secundárias, histórico). Abaixo de 1400 px de largura o nome do canal some da barra superior.

Ritmo de espaçamento observado: 6, 8, 14 e 20 px.

## Elevation & Depth

Plano, sem nenhuma sombra. A profundidade vem do tom (noite < painel < painel-2), dos fios de 1 px e de luz: a aurora radial da grade (três poços na cor de destaque, o maior centrado na linha do agora com opacidade 150/255, os outros com 70 e 45, cada um caindo para 35% na metade do raio) e o halo radial atrás do Rito. Luz é o que eleva; sombra não existe.

### Named Rules
**The Luz, Não Sombra Rule.** Nada recebe sombra projetada. Para destacar algo, use um tom mais claro, um contorno de 2 px ou um brilho radial na cor de destaque.

## Shapes

Cantos suaves em escala pequena: 4 px nas miniaturas, 6 px nos blocos da grade, 8 px em botões, campos, abas e moldura da grade, 10 px na caixa de declarações, 12 px nas listas. Contornos são de 1 px em repouso e 2 px no foco, na seleção e nos estados com contorno. O anel de seleção de um bloco fica 4 px para fora, com canto de 8 px. As formas de estado (meio círculo, círculo vazio, círculo com ponto, triângulo, círculo com visto, X, círculo cortado) são desenhadas em 10 px com traço de 1.6 px. O Rito é um cubo de cantos bem arredondados (20% do lado) com uma tela escura de cantos de 10%.

## Components

### Buttons
- **Shape:** cantos suaves (8px).
- **Primário:** fundo no destaque forte, texto branco 700, 9px 18px. Hover: destaque clareado 15%. Desabilitado: painel-2 com texto apagado. Usado só para a ação principal de cada área (Importar fila, Aprovar e agendar, Salvar nas Configurações).
- **Padrão:** painel-2, texto tinta, contorno borda de 1px, 8px 14px. Hover: contorno no destaque claro. Foco: contorno de 2px no destaque claro.
- **Perigo:** texto vermelho do agora com contorno vinho escuro; hover acende o contorno em vermelho. Só para Reprovar.
- **Semana (Anterior, Hoje, Próxima):** transparente com contorno borda, 5px 10px.

### Navigation
- **Abas da barra superior** (Grade da semana, Fila (n), Publicados): sem contorno, texto tinta suave 10.5pt, 7px 14px. Hover e ativa: fundo painel-2 e texto tinta; a ativa em 600.
- **Motivo:** ao lado do logotipo, um botão de texto que diz o que pede atenção agora e leva até o post: vermelho para "na hora"/erro, âmbar-tinta para pendente, verde para "Tudo em dia"; hover desenha o contorno na mesma cor.

### Inputs / Fields
- **Style:** fundo noite, contorno borda de 1px, cantos 8px, 6px 8px.
- **Focus:** contorno de 2px no destaque claro; seleção de texto no destaque forte com texto branco.
- **Rádios:** anel de 2px no destaque claro sobre noite; marcado ganha um ponto central claro.

### Cards / Containers
- **Caixa de declarações:** fundo noite, contorno borda de 1px, cantos 10px, recuo de 12px 14px, título "DECLARAÇÕES · VOCÊ MARCA". Quando falta marcar, o contorno vira âmbar de 2px e aparece "Marque para poder aprovar." em âmbar-tinta.
- **Gaveta:** fundo painel com fio superior; recuo 20px nas laterais.
- **Lista da Fila:** fundo painel, contorno fio, cantos 12px, itens de 76px com fio inferior; miniatura 64 x 36 (longo) ou 34 x 60 (vertical), título 600 10.5pt, linha de meta com o nome da rede na cor da rede, e a marca de estado com o nome do estado na cor do estado. Ordem: na hora, erro, aguardando, aprovado, agendado na rede, reprovado.

### Grade da semana (signature)
Desenhada à mão. Fundo painel com a aurora; cabeçalho de dias em LED sobre cabeçalho, com o dia de hoje em painel-2, LED no destaque claro com pontos apagados visíveis e barra de 2px no destaque forte embaixo. Coluna CANAL com faixa de 6px na cor da rede, nome em Segoe 600 e contagem em LED. A linha do agora é vermelha de 2px, por baixo dos blocos, com um ponto de 4px de raio no cabeçalho. Blocos seguem a regra Estado Tem Forma; hover desenha um contorno borda 3px para fora, seleção um anel destaque claro 4px para fora. Semana vazia: Rito dormindo no centro com a instrução de importar a fila.

### Rito (signature)
Folhinha de calendário de mesa em papel claro (degradê #f4f6fd a #c9cfe4, contorno branco), com duas argolas no topo, faixa do mês na cor de destaque, ponta de baixo à direita dobrada (#9aa3c4) e, embaixo dos olhos, uma fileira de 7 quadradinhos dos dias com o do meio aceso no destaque. O ícone do app é o mesmo Rito sobre um quadrado noturno com brilho azul. Os olhos são uma matriz de pontos 4x6 por olho, em tinta #141a34 com os pontos apagados visíveis em baixa opacidade (alerta em #ff4d5e). Expressões: atento (padrão), feliz (tudo em dia, aprovado, publicado), pendente (esperando aprovação), alerta (na hora ou erro), dormindo (fila vazia, reprovado). Pisca dois quadros a cada cerca de 4,3 s, exceto dormindo. Aparece com halo na barra superior (48px) e sem halo ao lado do título na gaveta (44px).

## Do's and Don'ts

### Do:
- **Do** dar a cada estado de post uma cor e uma forma próprias; a forma sozinha precisa identificar o estado.
- **Do** manter toda cor de destaque a cerca de 40° de matiz ou mais das cores de estado e de rede.
- **Do** usar LED para números e cabeçalhos que ficam sozinhos, e Segoe UI para todo o resto.
- **Do** fazer tudo que brilha (aurora, relógio, hoje, seleção, foco, primário) seguir o par de destaque ativo.
- **Do** mostrar o estado da agenda no rosto do Rito e no Motivo antes de qualquer outra coisa.
- **Do** usar fios de 1px na cor fio e contornos de 1px na cor borda; 2px só para foco, seleção e estados.

### Don't:
- **Don't** usar o amarelo e preto do canal Escala de Poder no Ritmora.
- **Don't** usar sombra projetada; profundidade é tom e luz.
- **Don't** pintar aurora fora da grade e do Rito.
- **Don't** escrever frases, títulos ou botões em LED.
- **Don't** usar uma cor de estado ou de rede como destaque, nem um destaque que se confunda com elas.
