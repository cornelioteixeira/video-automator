# video-automator — gestor do canal até monetização | Shorts 9:16 + Longos 16:9 | Pexels

Gestão 80/20: **Shorts 2-3/dia (20-35s)** para explosão + **longos 2/semana (3-8min)** para converter em inscritos. Ver `estrategia.md`. Estado em `channel_state.json`.

## Por que este fluxo passa em 4GB RAM

1. **Groq (nuvem)** gera roteiro JSON — 0 RAM local
2. **Pexels** entrega mp4 prontos landscape medium (720p/1080p, nunca 4K)
3. **edge-tts (nuvem)** narracao — RAM ~zero. Offline opcional: Kokoro-82M GGUF (~200MB)
4. **faster-whisper `base` cpu int8** — ~500MB
5. **ffmpeg `ultrafast + threads=2 + concat demuxer`** — sem xfade/transicoes (xfade dobra RAM). Apenas fade in/out 0.5s + legendas queimadas.

## Setup

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
# edite .env: GROQ_API_KEY, PEXELS_API_KEY
```

Chaves (.env ja configurado):
- Groq model: `openai/gpt-oss-20b` (raciocina antes de responder: usa `max_tokens=6000` + `reasoning_effort=low`)
- Pexels: https://www.pexels.com/api/
- Upload: manual em youtube.com/upload (sem YouTube Data API por sua decisao)

ffmpeg: nao precisa instalar — `imageio-ffmpeg` baixa binario automatico. Se tiver ffmpeg sistema, ele usa o sistema.

## Gestor do canal (novo)

```powershell
python manage_channel.py status
python manage_channel.py planejar --csv work/analytics.csv
python manage_channel.py gerar-shorts --tema "sinal de brain rot" --hook "Seu cerebro esta apodrecendo e voce nem percebeu" --saida output/shorts01.mp4 --work work/shorts01
python manage_channel.py postar --arquivo output/shorts01.mp4 --meta work/shorts01/meta_youtube.txt --privacidade public
```

Loop: analisa (CSV do Studio ou API) → planeja 14 shorts + 2 longos → gera → posta. Roteiro shorts = gancho 0-3s + promessa + open loops + loop final sem despedida. Pexels portrait sem repetir IDs. Analytics exige re-auth com escopos readonly (apague token_youtube.pickle 1x).

## Uso (longos)

```powershell
# so roteiro (gratis, testa Groq)
python main.py --tema "como o sono afeta a memoria" --dry-run

# pipeline completo 2.5min
python main.py --tema "como o sono afeta a memoria" --segundos 150

# sem legendas (mais rapido, menos RAM)
python main.py --tema "historia do cafe no brasil" --skip-legendas
```

Saidas em `work/run_atual/` (roteiro.json, assets/, audio/, subs.srt, meta_youtube.txt) e `output/final.mp4` pronto p/ YouTube 1080p24 + faststart. Suba manualmente em youtube.com/upload usando `meta_youtube.txt` (titulo/descricao/tags).

## Anti-demonetizacao (YouTube 2026 Inauthentic Content)

O roteiro ja exige `intro_pessoal`, `outro_pessoal` e `opiniao_central` em 1a pessoa. Antes de publicar:
1. Reescreva intro/outro com caso real seu.
2. Grave 10s com sua voz ou apareca 10s (sinal forte de transformacao humana).
3. Descricao + comentario fixado com sua opiniao, nao so resumo IA.

Lote "imagem + voz robo" = desmonetizado. Pexels real + opiniao sua + narracao revisada = seguro.
