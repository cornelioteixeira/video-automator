"""Estrategia 80/20 Shorts/Longs: pilares, ganchos, plano semanal a partir de analytics."""
import json
import os

PILARES = [
    "sinais",
    "mecanismo-dopamina",
    "criancas-games",
    "desafio-detox",
    "pais-sem-briga",
]

HOOKS = [
    "Este erro idiota está apodrecendo seu cérebro e você nem percebeu",
    "Pare de rolar por 27 segundos — seu foco depende disso",
    "Seu filho ama Tralalero? O perigo não é o personagem",
    "Fiz 7 dias sem shorts e isso aconteceu com meu sono",
    "Gritar LARGA O CELULAR piora o vício — faça isso",
]

STATE = "channel_state.json"


def carregar_estado() -> dict:
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"publicados": [], "ultima_analise": None}


def salvar_estado(estado: dict) -> None:
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def plano_semanal(analise: dict | None = None) -> list[dict]:
    """Gera 14 shorts + 2 longos. Se analise mostra queda 0-3s, prioriza ganchos novos;
    se CTR baixo, prioriza títulos contra-senso. Sem dados, faz rodízio dos pilares."""
    analise = analise or {}
    queda_inicio = analise.get("queda_0_3s", False)
    ctr_baixo = analise.get("ctr_baixo", False)
    plano = []
    for i in range(14):
        pilar = PILARES[i % len(PILARES)]
        hook = HOOKS[i % len(HOOKS)]
        if queda_inicio:
            hook = f"NON-HOOK TESTE: {hook} (variação agressiva)"
        titulo = hook[:90]
        plano.append({"tipo": "shorts", "pilar": pilar, "hook": hook,
                      "titulo": titulo, "ctr_teste": ctr_baixo})
    plano.append({"tipo": "longo", "pilar": "desafio-detox",
                  "titulo": "7 DIAS Para DESAPODRECER Seu Cérebro (guia completo)"})
    plano.append({"tipo": "longo", "pilar": "pais-sem-briga",
                  "titulo": "Filho GRUDADO no Celular? O guia sem briga"})
    return plano
