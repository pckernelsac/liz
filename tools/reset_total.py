"""Reset total: vacía participantes/ganadores/historiales y borra uploads + PDFs/XLSX de test.

USO:
    python tools/reset_total.py            # modo DRY-RUN (muestra lo que borraría)
    python tools/reset_total.py --apply    # ejecuta de verdad (hace backup antes)

Preserva: premios, sorteos, departamentos.
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import psycopg2
from app import config  # reutiliza DATABASE_URL

TABLES_TO_WIPE = [
    # orden respeta FKs: dependientes primero
    "ganadores",
    "historial_ediciones",
    "historial_validaciones",
    "participantes",
]

UPLOADS_DIR = ROOT / "uploads"
STATIC_DIR = ROOT / "static"

# Patrones de archivos generados en static/ que se consideran artefactos
STATIC_ARTIFACT_GLOBS = [
    "tickets_preview_*.pdf",
    "tickets_preview.pdf",
    "tickets_participantes.pdf",
    "tickets_sorteo_*.pdf",
    "participantes_*.xlsx",
    "validaciones_*.xlsx",
    "historial_ediciones_*.xlsx",
]

BACKUP_DIR = ROOT / "backups"


def inventory():
    print("=" * 72)
    print("INVENTARIO — lo que se vería afectado")
    print("=" * 72)
    print(f"\nDB: {config.DATABASE_URL}")
    with psycopg2.connect(config.DATABASE_URL) as conn:
        with conn.cursor() as cur:
            print("\nTablas a vaciar:")
            for t in TABLES_TO_WIPE:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                n = cur.fetchone()[0]
                print(f"  - {t}: {n} filas")
            print("\nTablas que se PRESERVAN:")
            for t in ("premios", "sorteos", "departamentos"):
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                n = cur.fetchone()[0]
                print(f"  - {t}: {n} filas (intactas)")

    # uploads
    uploads = list(UPLOADS_DIR.glob("*")) if UPLOADS_DIR.exists() else []
    print(f"\nArchivos en uploads/: {len(uploads)}")
    for p in uploads[:5]:
        print(f"  - {p.name}")
    if len(uploads) > 5:
        print(f"  ... y {len(uploads) - 5} más")

    # static artefactos
    artifacts = []
    for pat in STATIC_ARTIFACT_GLOBS:
        artifacts.extend(STATIC_DIR.glob(pat))
    print(f"\nArtefactos en static/ (PDFs/XLSX generados): {len(artifacts)}")
    for p in artifacts:
        print(f"  - {p.name}")


def backup_db() -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"sorteo_pre_reset_{ts}.sql"

    # Usar pg_dump si está en PATH, si no, fallback a COPY via psycopg2
    try:
        subprocess.run(
            ["pg_dump", "--dbname", config.DATABASE_URL, "-f", str(backup_path)],
            check=True,
            capture_output=True,
        )
        print(f"  Backup SQL: {backup_path} ({backup_path.stat().st_size // 1024} KB)")
        return backup_path
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        # Fallback: dump a CSV por tabla
        print(f"  pg_dump no disponible ({e.__class__.__name__}) — usando fallback CSV")
        csv_dir = BACKUP_DIR / f"csv_pre_reset_{ts}"
        csv_dir.mkdir(exist_ok=True)
        with psycopg2.connect(config.DATABASE_URL) as conn:
            with conn.cursor() as cur:
                for t in TABLES_TO_WIPE + ["premios", "sorteos", "departamentos"]:
                    out = csv_dir / f"{t}.csv"
                    with open(out, "wb") as f:
                        cur.copy_expert(
                            f"COPY {t} TO STDOUT WITH CSV HEADER", f
                        )
                    print(f"  Backup CSV: {out} ({out.stat().st_size} bytes)")
        return csv_dir


def wipe_db():
    with psycopg2.connect(config.DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # TRUNCATE CASCADE borra respetando FKs
            tables = ", ".join(TABLES_TO_WIPE)
            cur.execute(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE")
        conn.commit()
    print(f"  Tablas vaciadas: {', '.join(TABLES_TO_WIPE)}")


def wipe_uploads():
    if not UPLOADS_DIR.exists():
        return 0
    n = 0
    for p in UPLOADS_DIR.iterdir():
        if p.is_file():
            p.unlink()
            n += 1
        elif p.is_dir():
            shutil.rmtree(p)
    print(f"  Uploads eliminados: {n}")
    return n


def wipe_static_artifacts():
    n = 0
    for pat in STATIC_ARTIFACT_GLOBS:
        for p in STATIC_DIR.glob(pat):
            try:
                p.unlink()
                n += 1
            except PermissionError as e:
                print(f"  ! No se pudo borrar (en uso): {p.name} — {e}")
    print(f"  Artefactos static/ eliminados: {n}")
    return n


def main():
    apply = "--apply" in sys.argv

    inventory()

    if not apply:
        print("\n" + "=" * 72)
        print("DRY-RUN — no se modificó nada. Ejecuta con --apply para aplicar.")
        print("=" * 72)
        return 0

    print("\n" + "=" * 72)
    print("APLICANDO RESET TOTAL")
    print("=" * 72)

    print("\n[1/4] Backup de BD...")
    backup_path = backup_db()

    print("\n[2/4] Vaciando tablas...")
    wipe_db()

    print("\n[3/4] Limpiando uploads/...")
    wipe_uploads()

    print("\n[4/4] Limpiando artefactos de static/...")
    wipe_static_artifacts()

    print("\n" + "=" * 72)
    print("RESET COMPLETADO")
    print(f"Backup guardado en: {backup_path}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
