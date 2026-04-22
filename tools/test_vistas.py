"""Test senior de todas las vistas del sistema.

Verifica:
- Status HTTP
- Tiempo de respuesta
- Tipo de contenido
- Marcadores esperados en el HTML (títulos, bloques clave)
- Que el enlace "En vivo" YA NO aparezca en el menú
- Que las rutas admin requieran login (302 sin sesión)
- Que las rutas admin respondan 200 con sesión
"""
from __future__ import annotations

import io
import sys
import time
import urllib.parse

# Forzar UTF-8 en stdout (Windows cp1252 rompe con símbolos)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from dataclasses import dataclass, field
from typing import Optional

import requests

BASE = "http://localhost:5000"
TIMEOUT = 10

# Credenciales del admin (app.py: ADMIN_CREDENTIALS)
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

PASS = "\033[92mOK\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"
RESET = "\033[0m"


@dataclass
class TestCase:
    name: str
    method: str
    path: str
    auth: bool = False
    expected_status: tuple[int, ...] = (200,)
    expect_markers: list[str] = field(default_factory=list)
    forbid_markers: list[str] = field(default_factory=list)
    allow_404: bool = False  # para rutas que dependen de IDs/estado


PUBLIC_CASES: list[TestCase] = [
    TestCase("Inicio (index)", "GET", "/",
             expect_markers=["RAPI RIFA", "Mis tickets", "Ganadores"],
             forbid_markers=["En vivo</span>"]),
    TestCase("Premios", "GET", "/premios"),
    TestCase("Mis tickets (form)", "GET", "/mis-tickets",
             expect_markers=["Mis Tickets", "documento"]),
    TestCase("Lista sorteos pública", "GET", "/sorteos"),
    TestCase("Login admin (GET)", "GET", "/admin/login",
             expect_markers=["login", "password"]),
    TestCase("Participantes en vivo (ruta expuesta)", "GET", "/participantes-vivo",
             expect_markers=["Participantes en vivo"]),
    TestCase("API participantes-vivo", "GET", "/api/participantes-vivo",
             expect_markers=["["]),
    TestCase("404 ruta inexistente", "GET", "/no-existe-esta-ruta",
             expected_status=(404,)),
]

ADMIN_CASES_NO_AUTH: list[TestCase] = [
    # Sin sesión, todos deben redirigir (302) a /admin/login
    TestCase("Admin dashboard (sin auth → 302)", "GET", "/admin",
             expected_status=(302, 307)),
    TestCase("Admin validación docs (sin auth → 302)", "GET", "/admin/validacion-documentos",
             expected_status=(302, 307)),
    TestCase("Admin gestión sorteos (sin auth → 302)", "GET", "/admin/gestion-sorteos",
             expected_status=(302, 307)),
    TestCase("Admin sorteos (sin auth → 302)", "GET", "/admin/sorteos",
             expected_status=(302, 307)),
    TestCase("Admin sorteo activo (sin auth → 302)", "GET", "/admin/sorteo-activo",
             expected_status=(302, 307)),
    TestCase("Admin premios (sin auth → 302)", "GET", "/admin/premios",
             expected_status=(302, 307)),
    TestCase("Historial ediciones (sin auth → 302)", "GET", "/admin/historial-ediciones-general",
             expected_status=(302, 307)),
]

ADMIN_CASES_AUTH: list[TestCase] = [
    TestCase("Admin dashboard", "GET", "/admin", auth=True,
             expect_markers=["admin", "Panel"]),
    TestCase("Validación documentos", "GET", "/admin/validacion-documentos", auth=True),
    TestCase("Gestión sorteos", "GET", "/admin/gestion-sorteos", auth=True),
    TestCase("Sorteos (API admin)", "GET", "/admin/sorteos", auth=True),
    TestCase("Sorteo activo (API)", "GET", "/admin/sorteo-activo", auth=True),
    TestCase("Participantes recientes", "GET", "/admin/participantes-recientes", auth=True),
    TestCase("Comprobantes pendientes", "GET", "/comprobantes-pendientes", auth=True),
    TestCase("Estadísticas validaciones", "GET", "/estadisticas-validaciones", auth=True),
    TestCase("Historial validaciones", "GET", "/historial-validaciones", auth=True),
    TestCase("Historial ediciones general", "GET", "/admin/historial-ediciones-general", auth=True),
    TestCase("Premios (API)", "GET", "/admin/premios", auth=True),
    TestCase("Exportar participantes (Excel)", "GET", "/exportar-participantes", auth=True,
             allow_404=True),
    TestCase("Exportar validaciones (Excel)", "GET", "/exportar-validaciones", auth=True,
             allow_404=True),
    TestCase("Exportar historial ediciones", "GET", "/admin/exportar-historial-ediciones", auth=True,
             allow_404=True),
    TestCase("Descargar tickets PDF", "GET", "/descargar-tickets-pdf", auth=True,
             allow_404=True),
]


def log(status: str, name: str, detail: str = "") -> None:
    tag = {"PASS": PASS, "FAIL": FAIL, "WARN": WARN}.get(status, status)
    print(f"  [{tag}] {name}{(' — ' + detail) if detail else ''}")


def probe(session: requests.Session, tc: TestCase) -> bool:
    url = BASE + tc.path
    t0 = time.perf_counter()
    try:
        resp = session.request(tc.method, url, allow_redirects=False, timeout=TIMEOUT)
    except requests.RequestException as e:
        log("FAIL", tc.name, f"excepción: {e}")
        return False
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Status esperado
    expected = set(tc.expected_status)
    if tc.allow_404:
        expected.add(404)

    status_ok = resp.status_code in expected
    body = resp.text if resp.headers.get("content-type", "").startswith(("text/", "application/json")) else ""

    # Markers
    marker_fail: Optional[str] = None
    for m in tc.expect_markers:
        if m not in body:
            marker_fail = f"falta marker '{m}'"
            break
    if not marker_fail:
        for m in tc.forbid_markers:
            if m in body:
                marker_fail = f"marker prohibido presente '{m}'"
                break

    # Juicio final
    detail = f"HTTP {resp.status_code} · {elapsed_ms:.0f} ms"
    if not status_ok:
        detail += f" (esperaba {sorted(expected)})"
        log("FAIL", tc.name, detail)
        return False
    if marker_fail:
        log("FAIL", tc.name, f"{detail} · {marker_fail}")
        return False
    if resp.status_code == 404 and tc.allow_404:
        log("WARN", tc.name, f"{detail} (404 aceptable, posible sin datos)")
        return True
    if elapsed_ms > 2000:
        log("WARN", tc.name, f"{detail} (lento > 2s)")
        return True
    log("PASS", tc.name, detail)
    return True


def login(session: requests.Session) -> bool:
    print("\n> Login admin")
    t0 = time.perf_counter()
    resp = session.post(
        BASE + "/admin/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=TIMEOUT,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if resp.status_code == 200 and resp.json().get("success"):
        log("PASS", f"login {ADMIN_USER}", f"HTTP 200 · {elapsed_ms:.0f} ms · cookie={list(session.cookies.keys())}")
        return True
    log("FAIL", f"login {ADMIN_USER}", f"HTTP {resp.status_code} · body={resp.text[:120]}")
    return False


def main() -> int:
    print("=" * 72)
    print("TEST SENIOR DE VISTAS — Sistema Sorteos")
    print("=" * 72)

    results: list[tuple[str, bool]] = []

    # 1) Rutas públicas
    print("\n> Rutas públicas")
    sess_public = requests.Session()
    for tc in PUBLIC_CASES:
        results.append((tc.name, probe(sess_public, tc)))

    # 2) Rutas admin sin autenticación → deben redirigir
    print("\n> Rutas admin SIN sesión (deben redirigir 302)")
    sess_no_auth = requests.Session()
    for tc in ADMIN_CASES_NO_AUTH:
        results.append((tc.name, probe(sess_no_auth, tc)))

    # 3) Login y rutas admin con sesión
    sess_auth = requests.Session()
    if not login(sess_auth):
        print("\n❌ No se pudo iniciar sesión. Aborto pruebas admin.")
        return 1
    results.append(("login admin", True))

    print("\n> Rutas admin CON sesión")
    for tc in ADMIN_CASES_AUTH:
        results.append((tc.name, probe(sess_auth, tc)))

    # Resumen
    total = len(results)
    passed = sum(1 for _, ok in results if ok)
    failed = total - passed
    print("\n" + "=" * 72)
    print(f"RESUMEN: {passed}/{total} OK  ·  {failed} FAIL")
    if failed:
        print("\nFallos:")
        for name, ok in results:
            if not ok:
                print(f"  - {name}")
    print("=" * 72)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
