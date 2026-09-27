"""A6 AUDITORIA_CONSISTENCIA_FRONT - Extractor de URLs del front vs app.openapi().

Cruza todas las rutas /v1/... citadas en `static/js/**` y `templates/**` contra los
paths registrados en FastAPI (`app.openapi()['paths']`), detectando rutas que el
front llama y NO existen en el backend (o con verbo no soportado).

Uso:
    python _tools/check_consistencia_frontend.py           # tabla resumida (exit 1 si hay faltantes)
    python _tools/check_consistencia_frontend.py --json    # dump de toda la tabla (debug)
"""
import argparse
import re
import sys
from pathlib import Path

from fastapi.routing import APIRouter

ROOT = Path(__file__).resolve().parents[1]
FRONT_DIRS = [ROOT / "static" / "js", ROOT / "templates"]
URL_RE = re.compile(r"""/v1/[A-Za-z0-9_\-{}.$]+(?:/[A-Za-z0-9_\-{}.$]+)*""")
WS_RE = re.compile(r"""/ws/[A-Za-z0-9_\-{}.$]+(?:/[A-Za-z0-9_\-{}.$]+)*""")


def scan_urls() -> list:
    found = []
    for base in FRONT_DIRS:
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in {".js", ".html"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            for pat in (URL_RE, WS_RE):
                for m in pat.finditer(text):
                    raw = m.group(0)
                    found.append((rel, raw))
    return found


def front_path_to_api(raw: str) -> str:
    """De '/v1/user/reservations/{reservation_id}' (o '${id}') -> '/v1/user/reservations/{_}'."""
    return re.sub(r"\$\{[^}]+\}|\{[^}]+\}", "{_}", raw)


def load_openapi_paths():
    sys.path.insert(0, str(ROOT))
    from main import app

    spec = app.openapi()
    return spec.get("paths", {})


def _is_websocket(route) -> bool:
    return "WebSocket" in type(route).__name__ or getattr(route, "websocket", False)


def _walk_routes(router, prefix=""):
    """Recorre rutas incluidas (`_IncludedRouter`/autorouter custom) acumulando prefijos."""
    routes = getattr(router, "routes", None)
    if routes is None:
        return
    for r in routes:
        if type(r).__name__ == "_IncludedRouter":
            ctx = getattr(r, "include_context", None)
            sub = getattr(ctx, "prefix", "") or ""
            inner = getattr(r, "original_router", None)
            if inner is not None:
                yield from _walk_routes(inner, prefix + sub)
        elif isinstance(r, APIRouter):
            yield from _walk_routes(r, prefix + (r.prefix or ""))
        else:
            yield prefix + getattr(r, "path", ""), r


def load_app():
    sys.path.insert(0, str(ROOT))
    from main import app

    return app


def method_supported(openapi_methods: dict, verb: str) -> bool:
    return verb in openapi_methods


def main():
    parser = argparse.ArgumentParser(description="Extractor de consistencia front/backend (A6).")
    parser.add_argument("--json", action="store_true", help="Volcado detallado por ocurrencia.")
    parser.add_argument("--dump-openapi", help="Vuelca app.openapi() completo a un archivo JSON.")
    args = parser.parse_args()

    found = scan_urls()
    api_paths = load_openapi_paths()
    if args.dump_openapi:
        import json

        from pathlib import Path as _P

        _P(args.dump_openapi).write_text(
            json.dumps(api_paths, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"OpenAPI dump -> {args.dump_openapi}")
    # Descartar solapamientos: si una ocurrencia está contenida en otra más larga, queda la larga.
    found = [
        (rel, raw)
        for rel, raw in found
        if not any(raw != other and (raw in other or other.endswith(raw)) for _, other in found)
    ]
    api_paths = load_openapi_paths()
    # Normalizar los paths del OpenAPI de la misma forma ({var} -> {_})
    api_norm = {re.sub(r"\$\{[^}]+\}|\{[^}]+\}", "{_}", p): list(op.keys()) for p, op in api_paths.items()}

    # Websockets registrados en la app (no figuran en openapi()['paths'])
    app = load_app()
    ws_norm = {
        re.sub(r"\$\{[^}]+\}|\{[^}]+\}", "{_}", path): route
        for path, route in _walk_routes(app, "")
        if _is_websocket(route)
    }

    rows = []
    for rel, raw in found:
        path = front_path_to_api(raw)
        if "/ws" in path:
            verbs = ["websocket"] if path in ws_norm else None
        else:
            verbs = api_norm.get(path)
        state = "OK" if verbs else "FALTANTE"
        rows.append((raw, rel, path, verbs, state))

    # Tabla: ruta única (raw simplificado) -> métodos disponibles
    unique = {}
    for raw, rel, path, verbs, state in rows:
        key = path
        if key not in unique:
            unique[key] = {"raw": raw, "verbs": verbs, "state": state, "refs": []}
        unique[key]["refs"].append(rel)

    print("=== Consistencia Frontend/Backend (A6) ===")
    print(f"Ocurrencias /v1|/ws en front: {len(rows)} | rutas unicas: {len(unique)}\n")

    if args.json:
        for k, v in sorted(unique.items()):
            print(f"[{v['state']:>8}] {v['raw']}")
            print(f"        verbos backend: {v['verbs'] or 'N/A'}")
            print(f"        refs: {', '.join(sorted(set(v['refs'])))}")
        print("\n--- Ocurrencias crudas ---")
        for raw, rel, path, verbs, state in rows:
            print(f"[{state:>8}] {raw}  ({rel})")

    missing = {k: v for k, v in unique.items() if v["state"] != "OK"}
    print(f"\nRutas que el front llama y el backend NO registra: {len(missing)}")
    for k, v in sorted(missing.items()):
        print(f"  - {v['raw']}")
        for ref in sorted(set(v["refs"])):
            print(f"      -> {ref}")

    # response_model de las rutas front con datos (GET que el JS consume)
    print("\n--- response_model de rutas consumidas por el front ---")
    for k in sorted(unique):
        v = unique[k]
        if v["state"] != "OK":
            continue
        api_info = None
        api_path_key = None
        for p, o in api_paths.items():
            if front_path_to_api(p) == k:
                api_info = o
                api_path_key = p
                break
        if not api_info:
            continue
        for verb, data in api_info.items():
            content = data.get("responses", {}).get("200", {}).get("content", {})
            schema = None
            if "application/json" in content:
                schema = content["application/json"].get("schema")
            print(f"  {verb.upper():>6} {api_path_key}  ->  {schema}")

    print(f"\nTotal rutas backend registradas (openapi): {len(api_paths)}")
    if missing:
        print("\nERRORES (consistencia front/backend):")
        for k, v in missing.items():
            print(f"  - {v['raw']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())