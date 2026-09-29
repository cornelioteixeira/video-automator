"""Roteiro via Groq (nuvem, custo local zero). Saida JSON pronta p/ 2-3min 16:9."""
import json
import re
from config import SETTINGS

SYSTEM = """Voce e um roteirista de YouTube formato medio (2-3 minutos, 16:9).
Responda APENAS com JSON valido, sem markdown, sem explicacao, sem raciocinio visivel.
Inclua transformacao humana obrigatoria: opiniao propria, experiencia, intro e outro pessoais.
Publico: Brasil, portugues claro."""

def _prompt(tema: str, segundos: int = 150) -> str:
    palavras = int(segundos * 2.4)  # ~145ppm pt-BR
    return f"""Tema: {tema}
Duracao alvo: {segundos}s (~{palavras} palavras de narracao).

Retorne JSON com exatamente:
{{
  "titulo": "titulo chamativo <=70 chars, sem clickbait mentiroso",
  "descricao": "2-3 frases + 1 pergunta p/ comentarios",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "intro_pessoal": "1 frase em 1a pessoa (experiencia propria)",
  "blocos": [
    {{"texto": "narracao ~60-80 palavras", "visual_query": "2-4 palavras em ingles p/ Pexels, ex: city night traffic"}},
    {{"texto": "...", "visual_query": "..."}},
    {{"texto": "...", "visual_query": "..."}},
    {{"texto": "...", "visual_query": "..."}},
    {{"texto": "...", "visual_query": "..."}}
  ],
  "outro_pessoal": "conclusao com opiniao propria + CTA inscrever-se",
  "opiniao_central": "tese propria em 1 frase (o que so voce diria)"
}}
Regras: 5 blocos. Soma total {palavras-30}-{palavras+30} palavras (intro+blocos+outro).
visual_query sempre em ingles, landscape-friendly, sem texto na cena.
"""

def _extrair_json(raw: str) -> dict:
    """Extrai o maior bloco {...} e faz parse. Tolera cercas e texto extra."""
    t = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    ini, fim = t.find("{"), t.rfind("}")
    if ini == -1 or fim == -1 or fim <= ini:
        raise ValueError(f"resposta sem JSON (primeiros 300 chars): {t[:300]!r}")
    return json.loads(t[ini:fim + 1])

def gerar_roteiro(tema: str, segundos: int = 150) -> dict:
    if not SETTINGS.groq_api_key:
        raise RuntimeError("GROQ_API_KEY vazio. Copie .env.example -> .env")
    from groq import Groq
    client = Groq(api_key=SETTINGS.groq_api_key)
    # gpt-oss-20b raciocina antes de responder (~2-3k tokens): precisa de margem.
    # reasoning_effort=low reduz esse custo sem piorar roteiro simples.
    kwargs: dict = dict(
        model=SETTINGS.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _prompt(tema, segundos)},
        ],
        temperature=0.7,
        max_tokens=6000,
    )
    try:
        resp = client.chat.completions.create(reasoning_effort="low", **kwargs)  # type: ignore[call-arg]
    except TypeError:
        resp = client.chat.completions.create(**kwargs)
    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        raise RuntimeError("Groq retornou vazio (raciocinio consumiu max_tokens). Aumente max_tokens em src/script_gen.py.")
    data = _extrair_json(raw)
    assert len(data.get("blocos", [])) >= 4, "roteiro curto demais"
    return data

SYSTEM_SHORTS = """Voce e um roteirista de YouTube Shorts 9:16 (20-35s, PT-BR) + diretor visual.
Responda APENAS com JSON valido, sem markdown, sem explicacao.
Estrutura obrigatoria: gancho 0-3s counter-intuitivo + promessa 3-8s + corpo com open loops + final em LOOP (ultima frase conecta com a primeira, sem despedida, sem 'se inscreva').
CASAMENTO PEXELS: cada cena precisa combinar com a fala. NUNCA use tema geral. Para cada fala, entregue 3 palavras_chave_visuais especificas em ingles (objeto+acao+contexto) + clima. Ex: fala 'voce rola o feed na cama de madrugada' -> ["person scrolling phone in bed at night", "close up thumb scrolling screen", "dark bedroom phone glow"].
Ritmo: troca visual a cada 1.5-2.5s. Sem 'ola pessoal'."""

def _prompt_shorts(tema: str, hook: str = "", segundos: int = 28) -> str:
    palavras = int(segundos * 2.4)
    return f"""Tema: {tema}
Hook sugerido: {hook or "counter-intuitivo 0-3s"}
Duracao: {segundos}s (~{palavras} palavras).

PROMPT EXATO DO ROTEIRISTA (siga a risca):
1. Quebre o tema em 5 CENAS (gancho, promessa, corpo1, corpo2, loop).
2. Cada cena = 1 fala curta PT-BR + visual especifico daquela fala.
3. visual_query = escolha a MELHOR das 3 palavras_chave_visuais (2-5 palavras em ingles, portrait-friendly, sem texto na cena).
4. visual_query PROIBIDO generico: nunca repita "portrait-friendly" sozinho, nunca reuse a mesma query em 2 cenas.

Retorne JSON exatamente:
{{
  "titulo": "titulo <=70 chars, Curiosidade+Beneficio+Especificidade, sem clickbait mentiroso",
  "descricao": "2 linhas com keyword do titulo + 1 pergunta p/ comentarios + #Shorts",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "roteiro": [
    {{"fala": "GANCHO 0-3s (~10 palavras)",
      "palavras_chave_visuais": ["opcao especifica 1", "opcao especifica 2", "opcao especifica 3"],
      "visual_query": "a melhor das 3, especifica",
      "clima": "tenso|curioso|urgente",
      "seg": 3}},
    {{"fala": "PROMESSA 3-8s (~12 palavras)", "palavras_chave_visuais": ["...", "...", "..."], "visual_query": "...", "clima": "...", "seg": 5}},
    {{"fala": "CORPO 1 com open loop (~20 palavras)", "palavras_chave_visuais": ["...", "...", "..."], "visual_query": "...", "clima": "...", "seg": 7}},
    {{"fala": "CORPO 2 responde parcial + novo loop + CTA p/ video longo (~20 palavras)", "palavras_chave_visuais": ["...", "...", "..."], "visual_query": "...", "clima": "...", "seg": 7}},
    {{"fala": "LOOP FINAL que reconecta ao gancho, sem despedida (~10 palavras)", "palavras_chave_visuais": ["...", "...", "..."], "visual_query": "...", "clima": "...", "seg": 6}}
  ],
  "video_longo_relacionado": "titulo do longo correspondente p/ fixar como related",
  "opiniao_central": "tese propria 1 frase"
}}
Total {palavras-15}-{palavras+15} palavras. visual_query distintas entre cenas.
"""

def gerar_roteiro_shorts(tema: str, hook: str = "", segundos: int = 28) -> dict:
    if not SETTINGS.groq_api_key:
        raise RuntimeError("GROQ_API_KEY vazio. Copie .env.example -> .env")
    from groq import Groq
    client = Groq(api_key=SETTINGS.groq_api_key)
    kwargs: dict = dict(
        model=SETTINGS.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_SHORTS},
            {"role": "user", "content": _prompt_shorts(tema, hook, segundos)},
        ],
        temperature=0.8,
        max_tokens=3000,
    )
    try:
        resp = client.chat.completions.create(reasoning_effort="low", **kwargs)  # type: ignore[call-arg]
    except TypeError:
        resp = client.chat.completions.create(**kwargs)
    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        raise RuntimeError("Groq retornou vazio.")
    data = _extrair_json(raw)
    assert len(data.get("roteiro", [])) >= 4, "roteiro shorts curto demais"
    return data

def narracao_completa(roteiro: dict) -> str:
    partes = [roteiro.get("intro_pessoal", "")]
    partes += [b["texto"] for b in roteiro["blocos"]]
    partes += [roteiro.get("outro_pessoal", "")]
    return "\n\n".join(p for p in partes if p)
