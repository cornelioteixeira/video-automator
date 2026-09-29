"""Pexels como banco de videos. Apenas landscape, tamanho medio (economia RAM/CPU).
Regra anti-repeticao: nunca reutiliza o mesmo ID Pexels — nem dentro do mesmo video,
nem entre videos (controle global em work/pexels_usados.json)."""
import json
import os
import requests
from tqdm import tqdm

API = "https://api.pexels.com/videos/search"
USADOS_DEFAULT = os.path.join("work", "pexels_usados.json")

def _headers(api_key: str) -> dict:
    return {"Authorization": api_key}

def buscar_video(query: str, api_key: str, per_page: int = 15, page: int = 1,
                 orientation: str = "landscape") -> list[dict]:
    r = requests.get(API, headers=_headers(api_key), params={
        "query": query,
        "orientation": orientation,
        "size": "medium",
        "per_page": per_page,
        "page": page,
    }, timeout=30)
    r.raise_for_status()
    return r.json().get("videos", [])


def _carregar_usados(path: str) -> set:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data if isinstance(data, list) else data.get("ids", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _salvar_usados(path: str, ids: set) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, ensure_ascii=False, indent=2)

def _melhor_arquivo(video: dict) -> dict | None:
    # Prefere 1280x720 ou 1920x1080 mp4, evita 4K (pesa CPU/RAM) e evita <720p
    files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"]
    if not files:
        return None
    def score(f):
        w, h = f.get("width", 0), f.get("height", 0)
        if w >= 3840:
            return 999  # penaliza 4K
        if h < 720:
            return 500
        # prefere 720p-1080p
        return abs(h - 720)
    return sorted(files, key=score)[0]

def baixar_para_blocos(blocos: list[dict], api_key: str, dest_dir: str,
                       usados_path: str = USADOS_DEFAULT,
                       orientation: str = "landscape") -> list[str]:
    """Um video por bloco, SEM repetir IDs (nem no video atual, nem em videos passados).
    Retorna caminhos locais na ordem dos blocos. Grava sidecar .pexels.json por clip."""
    os.makedirs(dest_dir, exist_ok=True)
    usados = _carregar_usados(usados_path)
    usados_local: set = set()
    # Se o work e novo mas clips ja existiam em cache, registra os sidecars antigos
    saidas = []
    for i, b in enumerate(blocos):
        out = os.path.join(dest_dir, f"clip_{i:02d}.mp4")
        sidecar = os.path.join(dest_dir, f"clip_{i:02d}.pexels.json")
        if os.path.exists(out) and os.path.getsize(out) > 100_000 and os.path.exists(sidecar):
            try:
                with open(sidecar, "r", encoding="utf-8") as f:
                    info = json.load(f)
                    vid = info.get("id")
                    if vid is not None:
                        usados.add(vid)
                        usados_local.add(vid)
                saidas.append(out)
                continue
            except (json.JSONDecodeError, OSError):
                pass
        q = b.get("visual_query", "nature landscape")
        escolhido = None
        escolhido_query = q
        # Tenta query original (pag 1 e 2) + fallbacks, sempre pulando IDs ja usados
        tentativas = [q, q + " cinematic", "aerial landscape cinematic"]
        for tq in tentativas:
            for page in (1, 2):
                try:
                    videos = buscar_video(tq, api_key, per_page=15, page=page,
                                          orientation=orientation)
                except Exception:
                    continue
                for v in videos:
                    vid = v.get("id")
                    if vid in usados or vid in usados_local:
                        continue
                    if _melhor_arquivo(v) is None:
                        continue
                    escolhido = v
                    escolhido_query = tq
                    break
                if escolhido is not None:
                    break
            if escolhido is not None:
                break
        if escolhido is None:
            raise RuntimeError(
                f"Pexels sem video NOVO para: {q} (todos os resultados ja usados). "
                f"Tente visual_query mais especifica.")
        arq = _melhor_arquivo(escolhido)
        assert arq is not None
        url = arq["link"]
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(out, "wb") as f, tqdm(total=total, unit="B", unit_scale=True,
                                           desc=f"pexels {escolhido_query[:25]} id={escolhido.get('id')}") as bar:
                for chunk in r.iter_content(1 << 20):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
        vid = escolhido.get("id")
        usados.add(vid)
        usados_local.add(vid)
        _salvar_usados(usados_path, usados)
        with open(sidecar, "w", encoding="utf-8") as f:
            json.dump({"id": vid, "query": escolhido_query,
                       "url": escolhido.get("url", "")}, f, ensure_ascii=False, indent=2)
        saidas.append(out)
    return saidas
