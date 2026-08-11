import inspect
from app import main
app = main.app
with open('route_inspect_output.txt', 'w', encoding='utf-8') as fh:
    fh.write(f'ROUTES={len(app.routes)}\n')
    for route in app.routes:
        fh.write('---\n')
        fh.write(f'path={getattr(route, "path", None)}\n')
        fh.write(f'name={getattr(route, "name", None)}\n')
        fh.write(f'methods={getattr(route, "methods", None)}\n')
        endpoint = getattr(route, 'endpoint', None)
        fh.write(f'endpoint={endpoint}\n')
        if endpoint is not None:
            try:
                sig = inspect.signature(endpoint)
                fh.write(f'sig={sig}\n')
                for name, p in sig.parameters.items():
                    fh.write(f'  param={name} ann={p.annotation!r} default={p.default!r}\n')
            except Exception as exc:
                fh.write(f'inspect-failed: {exc}\n')
