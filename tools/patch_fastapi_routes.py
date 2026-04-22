"""Replace Flask @app.route decorators with FastAPI HTTP method decorators."""
from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app.py"
text = APP.read_text(encoding="utf-8")

replacements: list[tuple[str, str]] = [
    ("@app.route('/')\n", "@app.get('/')\n"),
    ("@app.route('/registrar', methods=['POST'])\n", "@app.post('/registrar')\n"),
    ("@app.route('/premios')\n", "@app.get('/premios')\n"),
    ("@app.route('/mis-tickets')\n", "@app.get('/mis-tickets')\n"),
    ("@app.route('/consultar-ticket', methods=['POST'])\n", "@app.post('/consultar-ticket')\n"),
    ("@app.route('/admin/login', methods=['GET', 'POST'])\n", "@app.get('/admin/login')\n",),  # POST split handled manually
    ("@app.route('/admin/logout')\n", "@app.get('/admin/logout')\n"),
    ("@app.route('/admin')\n", "@app.get('/admin')\n"),
    ("@app.route('/admin/participantes-recientes')\n", "@app.get('/admin/participantes-recientes')\n"),
    ("@app.route('/realizar-sorteo', methods=['POST'])\n", "@app.post('/realizar-sorteo')\n"),
    ("@app.route('/validar-comprobante', methods=['POST'])\n", "@app.post('/validar-comprobante')\n"),
    ("@app.route('/validar-comprobantes-lote', methods=['POST'])\n", "@app.post('/validar-comprobantes-lote')\n"),
    ("@app.route('/estadisticas-validaciones')\n", "@app.get('/estadisticas-validaciones')\n"),
    ("@app.route('/ver-comprobante/<path:filename>')\n", "@app.get('/ver-comprobante/{filename:path}')\n"),
    ("@app.route('/comprobantes-pendientes')\n", "@app.get('/comprobantes-pendientes')\n"),
    ("@app.route('/exportar-participantes')\n", "@app.get('/exportar-participantes')\n"),
    ("@app.route('/exportar-validaciones')\n", "@app.get('/exportar-validaciones')\n"),
    ("@app.route('/historial-validaciones')\n", "@app.get('/historial-validaciones')\n"),
    ("@app.route('/admin/validacion-documentos')\n", "@app.get('/admin/validacion-documentos')\n"),
    ("@app.route('/admin/gestion-sorteos')\n", "@app.get('/admin/gestion-sorteos')\n"),
    ("@app.route('/admin/premio', methods=['POST'])\n", "@app.post('/admin/premio')\n"),
    ("@app.route('/admin/premios', methods=['GET'])\n", "@app.get('/admin/premios')\n"),
    ("@app.route('/admin/premio/<int:premio_id>', methods=['GET'])\n", "@app.get('/admin/premio/{premio_id}')\n"),
    ("@app.route('/admin/premio/<int:premio_id>', methods=['PUT'])\n", "@app.put('/admin/premio/{premio_id}')\n"),
    ("@app.route('/admin/premio/<int:premio_id>', methods=['DELETE'])\n", "@app.delete('/admin/premio/{premio_id}')\n"),
    ("@app.route('/admin/premio/<int:premio_id>/imagen', methods=['POST'])\n", "@app.post('/admin/premio/{premio_id}/imagen')\n"),
    ("@app.route('/generar-tickets-pdf', methods=['POST', 'GET'])\n", "@app.api_route('/generar-tickets-pdf', methods=['GET', 'POST'])\n"),
    ("@app.route('/descargar-tickets-pdf')\n", "@app.get('/descargar-tickets-pdf')\n"),
    ("@app.route('/admin/asignar-tickets', methods=['POST'])\n", "@app.post('/admin/asignar-tickets')\n"),
    ("@app.route('/admin/sorteos')\n", "@app.get('/admin/sorteos')\n"),
    ("@app.route('/admin/sorteo-activo')\n", "@app.get('/admin/sorteo-activo')\n"),
    ("@app.route('/admin/sorteo/<int:sorteo_id>/cerrar', methods=['POST'])\n", "@app.post('/admin/sorteo/{sorteo_id}/cerrar')\n"),
    ("@app.route('/admin/sorteo/nuevo', methods=['POST'])\n", "@app.post('/admin/sorteo/nuevo')\n"),
    ("@app.route('/admin/sorteo/<int:sorteo_id>/eliminar', methods=['DELETE'])\n", "@app.delete('/admin/sorteo/{sorteo_id}/eliminar')\n"),
    ("@app.route('/admin/sorteos/limpiar-antiguos', methods=['POST'])\n", "@app.post('/admin/sorteos/limpiar-antiguos')\n"),
    ("@app.route('/admin/sorteo/<int:sorteo_id>/registrar-ganadores', methods=['GET'])\n", "@app.get('/admin/sorteo/{sorteo_id}/registrar-ganadores')\n"),
    ("@app.route('/admin/sorteo/<int:sorteo_id>/registrar-ganadores', methods=['POST'])\n", "@app.post('/admin/sorteo/{sorteo_id}/registrar-ganadores')\n"),
    ("@app.route('/admin/sorteo/<int:sorteo_id>/ganadores')\n", "@app.get('/admin/sorteo/{sorteo_id}/ganadores')\n"),
    ("@app.route('/sorteos')\n", "@app.get('/sorteos')\n"),
    ("@app.route('/sorteos/<int:sorteo_id>/ganadores/ver')\n", "@app.get('/sorteos/{sorteo_id}/ganadores/ver')\n"),
    ("@app.route('/admin/registrar-compra-adicional', methods=['POST'])\n", "@app.post('/admin/registrar-compra-adicional')\n"),
    ("@app.route('/admin/participante/<int:participante_id>/editar', methods=['PUT'])\n", "@app.put('/admin/participante/{participante_id}/editar')\n"),
    ("@app.route('/admin/participante/<int:participante_id>/historial-ediciones')\n", "@app.get('/admin/participante/{participante_id}/historial-ediciones')\n"),
    ("@app.route('/admin/historial-ediciones-general')\n", "@app.get('/admin/historial-ediciones-general')\n"),
    ("@app.route('/admin/exportar-historial-ediciones')\n", "@app.get('/admin/exportar-historial-ediciones')\n"),
    ("@app.route('/sorteos/<int:sorteo_id>/ganadores', methods=['GET'])\n", "@app.get('/sorteos/{sorteo_id}/ganadores')\n"),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f"Missing pattern:\n{old!r}")
    text = text.replace(old, new, 1)

# Remove duplicate second route for ganadores/ver (keep first occurrence only)
dup = "@app.get('/sorteos/{sorteo_id}/ganadores/ver')\n"
first = text.find(dup)
if first != -1:
    second = text.find(dup, first + 1)
    if second != -1:
        # Find end of function: next @app. or def at module level after decorators
        rest = text[second:]
        m = re.search(r"\n(@app\.|def [a-z_])", rest[1:])
        # remove duplicate block from second @app.get to next def's end - fragile
        # simpler: remove second decorator line + following duplicate function until next @app
        end = rest.find("\n@app.", 1)
        if end == -1:
            end = len(rest)
        text = text[:second] + text[second + end :]

APP.write_text(text, encoding="utf-8")
print("Patched decorators")
