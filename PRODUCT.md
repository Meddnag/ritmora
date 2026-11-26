# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop (Windows, PySide6/Qt). Not a web app; the closest Impeccable value would be `web`, but the UI is native Qt widgets.

## Users
Hoje: o dono do canal "Escala de Poder" (um criador solo de vídeos 2.5D sobre personagens de games, animes e quadrinhos), que produz vídeos com ajuda de IA e publica no YouTube (longos 16:9 e Shorts), TikTok e Instagram Reels.
Depois: o dono quer vender o Ritmora para outros criadores de conteúdo que postam nas mesmas três redes.

## Product Purpose
Agendador de posts de vídeo para YouTube, TikTok e Instagram que recebe vídeos prontos de uma fila de produção (automática ou manual), deixa o criador revisar, editar o texto, marcar as declarações obrigatórias (conteúdo gerado por IA, conteúdo para crianças) e aprovar, e então publica ou prepara a publicação no horário certo. Sucesso: nada vai ao ar sem aprovação humana, e nenhum post agendado é esquecido.

## Positioning
Fica entre uma linha de produção automática de vídeos e as redes: a aprovação humana com as declarações de IA é obrigatória e explícita, e quando a rede não libera API, o modo assistido prepara o envio (abre a página, copia a legenda, mostra o arquivo) em vez de fingir automação.

## Operating Context
- Uso misto: sessões de planejamento da semana (montar a agenda inteira) e aprovações rápidas soltas no meio do dia.
- Roda no PC Windows do criador, fica na bandeja do sistema avisando quando chega a hora de um post.
- A fila chega como pastas com post.json, video.mp4 e capa/thumb, produzidas por scripts (Blender, HyperFrames, ElevenLabs).
- Vídeos verticais 9:16 (Shorts, TikTok, Reels) e horizontais 16:9 (YouTube longo) convivem na mesma fila.

## Capabilities and Constraints
- Estados de um post: aguardando aprovação, aprovado (na agenda), agendado na rede, na hora (confirme o envio), publicado, reprovado, erro.
- YouTube: envio automático pela YouTube Data API v3 (agendamento nativo via publishAt) quando o usuário conecta a conta; senão, modo assistido.
- Instagram e TikTok: modo assistido até haver app aprovado pela Meta / auditoria do TikTok.
- O app nunca vê senhas: logins são feitos nas páginas oficiais.
- Interface em português do Brasil.
- Undecided: modelo de venda, licenciamento, suporte a múltiplos canais/contas, sincronização entre computadores.

## Brand Commitments
- Nome: Ritmora (ritmo + hora). Identidade própria, separada do canal Escala de Poder (o amarelo e preto do canal não é a marca do Ritmora).

## Evidence on Hand
- Nenhum depoimento, cliente, preço ou métrica de uso existe ainda; não inventar.
- Conteúdo real para telas: os posts do canal Escala de Poder (ex.: "5 jeitos ridículos de derrotar o Knull").

## Product Principles
1. Nada é publicado sem aprovação explícita de uma pessoa, e as declarações (IA, crianças) são sempre marcadas por ela.
2. O que precisa da atenção agora aparece primeiro: o que está na hora e o que espera aprovação.
3. Honestidade sobre o que é automático e o que é assistido em cada rede.
4. Serve tanto a sessão de planejamento quanto a aprovação de dez segundos.
