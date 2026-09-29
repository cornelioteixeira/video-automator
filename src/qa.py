"""QA antes de publicar: gancho, sincronia, repetição Pexels, CTA p/ longo.
Retorna {aprovado, falhas[]}. Nunca aprova no automático se gancho fraco ou repetição.
"""
import json
import os

DESPEDIDAS = ("foi isso", "obrigado por assistir", "se inscreva", "inscreva-se",
              "até o próximo", "ate o proximo", "tchau")


def checar(roteiro: dict, clips_info: list[dict], usados_global: set) -> dict:
    falhas = []
    falas = [r.get("fala", "") for r in roteiro.get("roteiro", [])]
    primeira = (falas[0] if falas else "").lower()
    ultima = (falas[-1] if falas else "").lower()

    # 1. Gancho 0-3s: curto, sem saudação, com tensão/pergunta
    if len(primeira.split()) > 18:
        falhas.append("GANCHO_FRACO: primeira fala >18 palavras (corte para ~10)")
    if primeira.startswith(("ola", "olá", "bem-vindo", "bem vindo", "hoje vou")):
        falhas.append("GANCHO_FRACO: começa com saudação — entre direto no pico")
    if "?" not in " ".join(falas[:2]) and "!" not in " ".join(falas[:2]) \
            and not any(w in primeira for w in ("pare", "nunca", "erro", "perigo", "segredo",
                                                "verdade", "destru", "vicio", "viciado", "programado",
                                                "idiota", "apodrec", "sono", "tralalero", "cérebro", "cerebro")):
        falhas.append("GANCHO_FRACO: sem pergunta/suspense/palavra de impacto nos 3s")

    # 2. Loop final sem despedida
    if any(d in ultima for d in DESPEDIDAS):
        falhas.append("LOOP_QUEBRADO: final com despedida/CTA inscrito — reconecte ao gancho")

    # 3. Repetição Pexels
    ids = [c.get("id") for c in clips_info if c.get("id") is not None]
    if len(ids) != len(set(ids)):
        falhas.append("REPETICAO: mesmo clipe 2x dentro do shorts")
    repetidos = [i for i in ids if i in usados_global]
    if repetidos:
        falhas.append(f"REPETICAO_GLOBAL: IDs já usados antes: {repetidos}")

    # 4. Casamento cena-fala: visual_query genérica = reprovado
    for i, r in enumerate(roteiro.get("roteiro", [])):
        q = (r.get("visual_query", "") or "").lower()
        kws = r.get("palavras_chave_visuais", [])
        if q in ("portrait-friendly", "english portrait-friendly", ""):
            falhas.append(f"CASAMENTO_RUIM cena {i}: visual_query genérica")
        if len(kws) < 3:
            falhas.append(f"CASAMENTO_RUIM cena {i}: exige 3 palavras_chave_visuais")

    # 5. CTA p/ longo (no corpo2, não no final)
    meio = " ".join(falas[1:-1]).lower()
    if "video" not in meio and "longo" not in meio and "completo" not in meio:
        falhas.append("SEM_PONTE: corpo não cita o vídeo longo relacionado")

    return {"aprovado": len(falhas) == 0, "falhas": falhas}
