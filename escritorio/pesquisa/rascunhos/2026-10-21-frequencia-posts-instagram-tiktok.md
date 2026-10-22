# Frequência e horário de publicação para perfis pequenos (até 10 mil seguidores) no Instagram e no TikTok em 2026

## Pergunta
Qual a frequência e o horário de publicação recomendados em 2026 para perfis pequenos (até 10 mil seguidores) no Instagram e no TikTok, e o que os dados mostram sobre a relação entre frequência e alcance? Nível usado: padrão (rodada de verificação).

## Resumo executivo
Nenhuma das duas plataformas publica número oficial fixo; o TikTok orienta uma meta diária sustentável (página não lida) e o Instagram não deu número verificável. Estudos de vendors lidos apontam 3 a 5 posts/semana no Instagram (Buffer: +12% de alcance por post de 1-2 para 3-5) e 2 a 5/semana no TikTok (Buffer: +17% de views por post vs 1/semana), com retorno decrescente; no TikTok a mediana fica estável (~500 views) e postar mais eleva a chance de um hit. O Metricool 2023 (outro vendor, 1,9 milhão de vídeos) vê mais views por vídeo com mais frequência e 3 vídeos/semana como ótimo, o que dá apoio direcional independente do Buffer, mas sem controle por conta. Em contrapartida, o Metricool 2025 vs 2024 mostra alcance por post em queda com mais volume (contas de 2 a 10 mil: -32% de alcance com +16% de frequência, só em cobertura secundária). A Tailwind (22/mar/2017) está desatualizada. Horário do Instagram (Buffer, lido): quinta 9h, quarta 12h e 18h, em horário local de quem posta; testar na própria audiência. Incertezas: [1] e [15] não puderam ser lidas; faixa 2 a 10 mil e -32% só em cobertura secundária; nenhuma fonte independente com controle por conta para TikTok.

## Achados

Nota de método: nesta rodada as páginas foram lidas com `ler_pagina.py`. Marca [verificado] = li o número na página. As leituras do script são limitadas a ~4.000 caracteres por página, então alguns trechos podem ter ficado de fora.

### Recomendação oficial: TikTok
- A página do TikTok Creator Academy sobre cadência [1] voltou vazia (montada por JavaScript, 0 caracteres). O que se atribui a ela (não há resposta única, publicar várias vezes ao dia ajuda, meta diária cumprível) vem de resumo de busca anterior. [não verificado]
- Blogs de terceiros atribuem ao TikTok 1 a 4 posts por dia, sem texto oficial confirmado [12]. [não verificado]

### Recomendação oficial: Instagram
- Não encontrei número oficial de posts por semana em fonte do Instagram. O explicador "Instagram Ranking Explained" [15] descreve sinais de ranking, não volume. A página oficial retornou HTTP 400 no leitor e não foi lida. [não verificado]
- Data de [15], confirmada em cobertura lida: o Social Media Today, "Published May 31, 2023", relata o post de Mosseri e diz que ele deu explicação similar em 2021 [25]. Portanto [15] é de 31/mai/2023 (data via fonte secundária lida; a primária não foi aberta). A cobertura cita a frase de Mosseri de que o Instagram não tem um algoritmo único e que cada área (Feed, Stories, Explore, Reels, Search) usa o seu [25]. [verificado em [25]]
- Atribuições a Adam Mosseri ("não há regra de ouro", "postar mais tende a trazer mais seguidores") circulam só em blogs secundários [10][11]; sem fonte primária, não as uso como achado. Um Q&A de ago/2026 da Kontentino segue como referência secundária de fonte única [9].

### Dados sobre frequência x alcance: Instagram
- Buffer [2], lida: publicada em 13/ago/2025, título atual "in 2026". Analisa 2,1 milhões de posts de 102 mil contas (só feed). 3 a 5 posts/semana é o ponto ideal; o maior salto de alcance por post, ~12%, ocorre de 1-2 para 3-5 posts/semana; taxa de crescimento de seguidores: +0,12% (1-2), +0,26% (3-5), +0,44% (6-9), +0,66% (10+). Usa análise por conta contra ela mesma (z-score) porque a correlação simples pode ser confundida pelo fato de contas grandes postarem mais; o próprio Buffer ressalva que a relação "may not tell us the full story". [verificado] Os números de "3,7x" e "5,5x" também estão na página. [verificado]
- Tailwind [8], lida (parcialmente, 4.000 de ~5.400 caracteres): estudo de 22/mar/2017, mais de 100 mil posts de um período de três meses; contas em faixas de até 10 mil, 10-100 mil e 100 mil+, mas os resultados foram agregados porque as diferenças por tamanho eram pequenas; contas que postam mais de uma vez ao dia tiveram engajamento de 7% contra 8% de quem posta menos de uma vez por semana, e a própria Tailwind explica que isso é confundimento por tamanho (contas grandes postam mais e engajam menos); ao comparar as mesmas contas ao longo do tempo, o engajamento sobe com mais frequência. Só 5% das contas postavam diariamente. O número de contas não aparece no trecho lido. Dado de 2017, desatualizado: não uso como evidência para 2026. [verificado]

### Dados sobre frequência x alcance: TikTok
- Buffer [3], lida: 11,4 milhões de posts de mais de 150 mil contas. Em relação a 1 post/semana: 2 a 5 posts, até 17% mais views por post; 6 a 10, até 29%; 11+, até 34%. A mediana de views fica em torno de ~500 e até cai um pouco em cadências altas; o ganho vem do topo (p90/mediana 7,6x vs 31,4x). Buffer recomenda 2 a 5 posts/semana. O trecho lido não mostra a data de publicação nem a discussão de contas pequenas (seção "what about smaller accounts" truncada); a data de 8/out/2025 vem de busca anterior. [verificado, exceto a data]
- Fonte independente do Buffer (lacuna (b)): o Metricool "TikTok Study 2023" [26], lido, analisou 1.907.846 vídeos de 48.591 contas em 180 dias. Diz que, tomando 3 vídeos/semana como padrão, quanto maior a frequência, maiores as interações ou views por vídeo, embora o engajamento não tenha diferença significativa; que 3 vídeos/semana é uma frequência ótima; e que a diferença nas métricas começa a aparecer após cerca de 2 semanas de frequência alta. É outro vendor e outra amostra, mas é de 2023, não controla por conta (contas maiores postam mais: ~2 vídeos/dia nas Huge contra ~1 a cada 2 dias nas Tiny) e é um estudo de vendor, não acadêmico. Uma busca por estudos independentes não achou replicação; Social Media Today, SEJ, Routenote e NetInfluencer repetem o Buffer [27]. Metricool 2024 [23], RivalIQ [24] e Socialinsider [28] medem só volume e não foram lidas. [verificado em [26] para o que foi lido]

### Horário de publicação
- Instagram, Buffer [7], lida: a página (URL atual em buffer.com/resources/when-is-the-best-time-to-post-on-instagram/) está "Published Sep 23, 2026" (título "Updated Sep 2026"); o link anterior (14/mai e 14/jul/2026) corresponde a versões anteriores. Amostra: 9,6 milhões de posts de Instagram, parte do relatório State of Social Engagement 2026 (52 milhões de posts, 10 plataformas, mais de 200 mil contas, jan/2024 a dez/2025). Fuso: os horários foram normalizados e valem para o horário local de quem posta ("Times apply to your local timezone"). Melhores horários: quinta 9h, quarta 12h e quarta 18h; quarta é o melhor dia, seguida de quinta e terça; noites (18h a 23h) lideram na maioria dos dias, exceto quinta, em que a manhã vence; sexta e sábado são os piores dias. [verificado] A afirmação anterior de que quarta 12h e 18h seria o recorte "por alcance" não se sustenta: a métrica é engajamento.
- Later aponta ~5h no fuso da audiência; SocialPilot usa horários sem fuso [18][10]. Divergência parece metodológica. [não verificado]
- A fala de Mosseri sobre horário foi removida por falta de fonte primária; a Planoly é a única fonte e é secundária [21].
- TikTok: Metricool 2026 [5], lido, confirma 2.314.756 posts de mais de 92 mil contas, jan-fev/2025 vs jan-fev/2026, e que os melhores horários estão no estudo completo (não na página); o pico das 18h a 21h (20h) vem da página [6], não lida. [não verificado] Buffer TikTok (7,1 milhões de posts, domingo 9h) é citado na página [3] só como chamada, sem o resultado [não verificado]; Sprout via terceiros e PostFast [19] não verificados.
- Consenso: usar o fuso da própria audiência e os painéis nativos [19].

## Contrapontos e limitações
- Metricool 2026 Social Media Study [4], página lida: 1.059.949 contas e 39.762.999 posts (dez/2025), mas a página pública é só uma chamada para formulário e não traz a faixa 2 a 10 mil nem o -32%. [verificado só o escopo]
- Cobertura do NetInfluencer [22], lida: contas de 2.000 a 10.000 seguidores tiveram queda de 32% no alcance (10.206 para 6.990) com aumento de 16% na frequência semanal; contas abaixo de 2.000, -26%; contas de 100 mil a 1 milhão, -35%. Cuidado: o trecho está no parágrafo do TikTok (views por post -17% de 34.311 para 28.483, frequência +22% de 2,74 para 3,34 posts/semana, interações -32%), então não está claro se a faixa 2-10 mil é do TikTok ou geral, e o -32% coincide com a queda de interações do TikTok. Faixa e -32% confirmados só em cobertura secundária, plataforma ambígua. Instagram: alcance por post -31% (14.922 para 9.689), Reels -35%. [verificado em [22]; ambiguidade de plataforma não resolvida]
- Metricool TikTok [5], lido: publicado em 12/mai/2026 (não 11/mai); views por post -31,30%, alcance -28,73%, interações -31,17%, vídeos +72,10%; o CEO diz que não se pode contar só com volume. [verificado] Outro estudo Metricool de Instagram 2026 (24,4 milhões de posts, views +27%, interações +19%) segue só em busca anterior [4] [não verificado]. Amostras diferentes, não comparáveis.
- Postar mais não melhora a mediana no TikTok (Buffer) [3] [verificado]. Análise relatada por terceiros: 2 posts/dia dão mais views totais, menos por post, e manter por 90+ dias tende a reduzir qualidade [17]. [não verificado]
- Burnout: pesquisa citada pela Adobe com donos de pequenos negócios, autorrelato: 88% dos que usam o TikTok profissionalmente relataram burnout e 81% sentem pressão diária para postar [17]. Amostra e ano originais não confirmados; indicativo, não causal. [não verificado]
- Quase todos os estudos são de vendors de agendamento, com viés de amostra e métricas distintas. Nenhum estudo independente ou acadêmico encontrado.
- "Mais posts, mais crescimento" não separa causa e efeito: quem cresce tende a postar mais. Buffer e Tailwind tentam controlar comparando a conta com ela mesma, o que reduz mas não elimina o problema.

## Incertezas e lacunas
- (a) Parcial: lidas [2][3][4][5][7][8]; números do Buffer (IG e TikTok), Metricool TikTok e Tailwind conferidos. Não lidas: [1] (página vazia, JavaScript) e [15] (HTTP 400). Fuso do Buffer de horário confirmado (normalizado, vale para o fuso local) e amostra de 9,6 milhões confirmada. Falta a data de publicação do Buffer TikTok na página lida.
- (b) Parcial: não há fonte independente com controle por conta; o Metricool 2023 [26] é um apoio direcional de outro vendor (2023, sem controle). Buffer continua sendo a única evidência de efeitos fixos.
- (c) Parcial: -32% e +16% para 2 a 10 mil confirmados apenas na cobertura do NetInfluencer [22]; plataforma ambígua; relatório do Metricool atrás de formulário. Tailwind: data 22/mar/2017 e amostra (mais de 100 mil posts, 3 meses) confirmadas; número de contas não consta no trecho lido.
- (d) Resolvida por fonte secundária: [15] é de 31/mai/2023 (Social Media Today lida); a página oficial não abriu.
- Sem número oficial do Instagram; metodologia da Sprout e do Hootsuite não encontrada; nenhum dado específico do Brasil; horários do TikTok ([6], Buffer 7,1 milhões) não verificados.
- Datas: Buffer IG 13/ago/2025; Buffer TikTok 8/out/2025 (via busca); Buffer horário IG 23/set/2026; Metricool geral dez/2025; Metricool TikTok 12/mai/2026; Tailwind 22/mar/2017; [15] 31/mai/2023.

## Fontes
[1] TikTok Creator Academy, "Posting cadence best practices (publishers)", ano não confirmado, https://www.tiktok.com/creator-academy/en/article/posting-cadence-best-practices-publishers (primária; tentada, página vazia, não lida)
[2] Buffer, "How Often Should You Post on Instagram? Data From 2 Million Posts", 13/08/2025 (título atual "in 2026"), https://buffer.com/resources/how-often-to-post-on-instagram/ (primária) (lida)
[3] Buffer, "How Often Should You Post on TikTok? Data From 11 Million+ Posts", 08/10/2025 (data via busca; título atual "in 2026"), https://buffer.com/resources/how-often-should-you-post-on-tiktok/ (primária) (lida)
[4] Metricool, "Social Media Study 2026", dez/2025, https://metricool.com/social-media-study/ (primária) (lida; só página de chamada)
[5] Metricool, "2026 TikTok Study: 31% drop in video views", 12/05/2026, https://metricool.com/press-release-tiktok-study-2026/ (primária) (lida)
[6] Metricool, "Best time to post on TikTok in 2026", 2026, https://metricool.com/best-time-post-tiktok/ (primária; não lida)
[7] Buffer, "Best Time to Post on Instagram in 2026: 9.6 Million Posts", publicada 23/09/2026, https://buffer.com/resources/when-is-the-best-time-to-post-on-instagram/ (primária) (lida)
[8] Tailwind, "How Often Should I Post to Instagram? Our Study Says Every Day", 22/03/2017, https://tailwindapp.com/blog?p=2603 (primária) (lida)
[9] Kontentino, Q&A sobre frequência no Instagram, ago/2026, https://www.kontentino.com/q-and-a/how-often-to-post-on-instagram/ (secundária)
[10] SocialPilot, "How Often Should You Post On Instagram in 2026?", 2026, https://www.socialpilot.co/instagram-marketing/how-often-to-post-on-instagram (secundária)
[11] Dash Social, "How often should you post on Instagram", 2025/2026, https://www.dashsocial.com/blog/how-often-should-you-post-on-instagram (secundária)
[12] Hypebot, "How often should you post on TikTok", 2025, https://www.hypebot.com/how-often-should-you-post-on-tiktok.md (secundária; repete o Buffer)
[13] Search Engine Journal, "2-5 weekly TikToks deliver biggest view increase", 2025, https://www.searchenginejournal.com/study-shows-2-5-weekly-tiktoks-deliver-biggest-view-increase/558641/ (secundária; repete o Buffer)
[14] Social Media Today, "Study shows posting more on Instagram leads to more reach", 2025, https://www.socialmediatoday.com/news/study-shows-posting-more-instagram-leads-to-more-reach/757633/ (secundária)
[15] Instagram, "Instagram Ranking Explained", 31/05/2023 (data via [25]), https://about.instagram.com/blog/announcements/instagram-ranking-explained (primária; HTTP 400, não lida)
[16] removida (não lida, não citada)
[17] Adobe Express, "How often should you really post?", 2025/2026, https://www.adobe.com/express/learn/blog/how-often-should-you-post-content (secundária; dado de burnout é autorrelato)
[18] Later, "Best time to post on Instagram", 2026, https://later.com/blog/best-time-to-post-on-instagram (secundária)
[19] Teleprompter.com (citando Sprout Social 2026), https://teleprompter.com/blog/best-time-to-post-on-tiktok-for-creators (secundária)
[20] removida (não lida, não citada)
[21] Planoly, "Does it matter what times you post on TikTok & Instagram?", 2025/2026, https://www.planoly.com/blog/what-time-to-post-tiktok-instagram.md (secundária)
[22] NetInfluencer, cobertura do estudo Metricool sobre saturação, 2026, https://www.netinfluencer.com/social-media-saturation-reaches-tipping-point-as-content-volume-outpaces-engagement-study-finds/ (secundária) (lida)
[23] Metricool, "TikTok Study 2024", 2024, https://metricool.com/wp-content/uploads/TikTok-Study-2024-Metricool.pdf (primária; só descreve frequência, não mede views; só resumo de busca)
[24] RivalIQ, benchmark de TikTok para marcas, ano não confirmado, https://www.rivaliq.com/?p=29976 (primária; só resumo de busca)
[27] Social Media Today, "TikTok post frequency improves per-post reach: Buffer", 2025, https://www.socialmediatoday.com/news/tiktok-post-frequency-improves-per-post-reach-report-buffer/802443/ (secundária; repete o Buffer)
[28] Socialinsider, "TikTok Benchmarks 2024", 2024, https://socialinsider.io/data-geeks/Tiktok_Benchmarks_2024.pdf (primária; só volume de posts por marca, não mede views por frequência; só resumo de busca)
[25] Social Media Today, "Instagram Shares New Explainer on How its Feed, Reels and Stories Algorithms Work", 31/05/2023, https://www.socialmediatoday.com/news/instagram-explainer-feed-reels-and-stories-algorithm/651705/ (secundária) (lida)
[26] Metricool, "TikTok Study 2023", 2023, https://metricool.com/tiktok-study-2022/ (primária) (lida)
