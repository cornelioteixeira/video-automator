"""Analytics: tenta YouTube Analytics API; sem escopo, usa CSV manual do Studio.
Nunca inventa métricas — sem dados, retorna flags vazias e orienta coleta.
Escopos necessários p/ auto: youtube.readonly + yt-analytics.readonly (token atual só tem upload).
"""
import csv
import os

SCOPES_NEEDED = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def analisar_csv(path: str) -> dict:
    """CSV exportado do YouTube Studio (Analytics por vídeo). Colunas mínimas:
    video, views, avd_%, ctr_%, subs_ganhos. Retorna diagnóstico simples."""
    if not os.path.exists(path):
        return {"origem": "sem-dados",
                "aviso": "Sem dados. Exporte Analytics do Studio ou autorize escopos readonly.",
                "queda_0_3s": False, "ctr_baixo": False, "videos": []}
    videos = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                videos.append({
                    "video": row.get("video", "?"),
                    "views": int(float(row.get("views", 0) or 0)),
                    "avd": float((row.get("avd_%", 0) or 0)),
                    "ctr": float((row.get("ctr_%", 0) or 0)),
                    "subs": int(float(row.get("subs_ganhos", 0) or 0)),
                })
            except ValueError:
                continue
    flop = [v for v in videos if v["views"] < 1000]
    return {
        "origem": "csv",
        "total": len(videos),
        "flops": len(flop),
        # Heurística fria: flop generalizado = gancho fraco; CTR médio <3% = título/thumb
        "queda_0_3s": len(flop) > len(videos) / 2 and len(videos) > 0,
        "ctr_baixo": (sum(v["ctr"] for v in videos) / max(len(videos), 1)) < 3.0 if videos else False,
        "videos": sorted(videos, key=lambda v: v["views"], reverse=True)[:10],
    }


def analisar_api() -> dict:
    """Placeholder honesto: token atual não tem readonly. Retorna instrução, não dados falsos."""
    return {"origem": "api-bloqueada",
            "aviso": "Token só tem youtube.upload. Apague token_youtube.pickle e re-autorize com escopos readonly para análise automática.",
            "queda_0_3s": False, "ctr_baixo": False, "videos": []}
