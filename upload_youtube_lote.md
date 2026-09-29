# Upload YouTube — Lote Brainrot Conscientização (5 vídeos)

> Status do projeto: upload AUTOMÁTICO pela API **não configurado** (decisão anterior: manual em youtube.com/upload, sem YouTube Data API).
> Abaixo está tudo pronto para copiar/colar. Se quiser automático, veja o final.

## Ordem de publicação sugerida (1 por dia para não canibalizar)
1. video01_sinais → descoberta
2. video02_dopamina → causa
3. video03_criancas → emociona pais + pega busca Tralalero/Steal a Brainrot
4. video04_desafio → desafio compartilhável
5. video05_pais → fideliza pais

Arquivos:
- output/video01_sinais.mp4 (85.7 MB)
- output/video02_dopamina.mp4 (52.2 MB)
- output/video03_criancas.mp4 (80.3 MB)
- output/video04_desafio.mp4 (74.1 MB)
- output/video05_pais.mp4 (101.4 MB)
- Textos completos em work/videoXX_*/meta_youtube.txt (já otimizados)

## Como subir (3 min por vídeo)
1. Abra youtube.com/upload, arraste o mp4
2. Cole TITULO, DESCRICAO, TAGS (tags vão em Detalhes → Mostrar mais → Tags)
3. Playlist: crie "Brain Rot: Apodrecimento Cerebral e Como Sair"
4. Público: marque "Não é conteúdo para crianças" (mesmo o vídeo 3 e 5, pois falam COM pais, não PARA crianças — evita limitação do YouTube Kids)
5. Tela final: adicione próximo vídeo da série + inscrever-se
6. Comentário fixado (copie da DESCRICAO a pergunta final)
7. Publique como Não listado, revise, depois Público 1/dia 18h-20h BRT

## Textos prontos (espelho dos meta_youtube.txt)

### 1 — output/video01_sinais.mp4
TITULO: SEU CÉREBRO ESTÁ APODRECENDO? 5 Sinais de Brain Rot Que Ninguém Te Conta
DESCRIÇÃO e TAGS: ver work/video01_sinais/meta_youtube.txt
Pergunta fixada: quantas horas de tela você fez ontem?

### 2 — output/video02_dopamina.mp4
TITULO: Você NÃO É Viciado, FOI PROGRAMADO: A Armadilha da Dopamina
DESCRIÇÃO e TAGS: ver work/video02_dopamina/meta_youtube.txt
Pergunta fixada: qual é a sua maior armadilha digital?

### 3 — output/video03_criancas.mp4
TITULO: Por Que Seu Filho AMA Tralalero e Steal a Brainrot? O Perigo Que Pais Ignoram
DESCRIÇÃO e TAGS: ver work/video03_criancas/meta_youtube.txt
Pergunta fixada: comenta a IDADE do seu filho

### 4 — output/video04_desafio.mp4
TITULO: 7 DIAS Para DESAPODRECER Seu Cérebro (Detox Sem Shorts Que Funciona)
DESCRIÇÃO e TAGS: ver work/video04_desafio/meta_youtube.txt
Pergunta fixada: comenta DIA 1

### 5 — output/video05_pais.mp4
TITULO: Filho GRUDADO no Celular? Faça ISSO em Vez de Brigar (Funciona)
DESCRIÇÃO e TAGS: ver work/video05_pais/meta_youtube.txt
Pergunta fixada: qual sua batalha mais difícil com a tela?

## Para ativar upload automático (se quiser no futuro)
O auto-upload exige:
1. Projeto no Google Cloud com YouTube Data API v3 ativada
2. OAuth Client ID (Desktop) → baixar client_secrets.json
3. `pip install google-api-python-client google-auth-oauthlib`
4. Script que eu posso criar: `upload_youtube.py --arquivo output/....mp4 --meta work/.../meta_youtube.txt`

Sem o client_secrets + login Google no seu PC, eu não consigo subir sozinho — por segurança o YouTube exige seu consentimento.
Me envie o client_secrets ou confirme que quer o modo manual, e eu sigo.
