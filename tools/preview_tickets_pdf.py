"""Genera un PDF de muestra para previsualizar el layout de _build_tickets_table."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from app import _build_tickets_table

NOMBRES = ["Juan Carlos", "María Fernanda", "Luis Alberto", "Ana Lucía", "José Miguel",
           "Rosa Elena", "Pedro Antonio", "Carmen Isabel", "Ricardo", "Lucía",
           "Gustavo Adolfo", "Patricia", "Fernando", "Silvia", "Alejandro", "Beatriz"]
APELLIDOS = ["Rodríguez Gómez", "Pérez Castillo", "Sánchez Torres", "Ramírez Vega",
             "Flores Quispe", "Huamán", "Mendoza Ríos", "Vargas", "Castro Díaz", "Paredes"]

def sample_participantes(n: int):
    import random
    random.seed(42)
    out = []
    # Números de ticket de 6 dígitos (100000 en adelante) para simular el caso real
    base = 100000
    for i in range(n):
        out.append({
            "numero_participacion": base + i,
            "nombres": random.choice(NOMBRES),
            "apellidos": random.choice(APELLIDOS),
            "tipo_documento": random.choice(["DNI", "CE"]),
            "numero_documento": f"{random.randint(10000000, 99999999)}",
            "whatsapp": f"9{random.randint(10000000, 99999999)}",
        })
    return out

def main(total: int = 108):
    participantes = sample_participantes(total)
    from datetime import datetime
    stamp = datetime.now().strftime("%H%M%S")
    out_path = ROOT / "static" / f"tickets_preview_{stamp}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("PREVIEW - Listado de Tickets (muestra)", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Total: {total} tickets de ejemplo | 6 por fila × 9 filas = 54 por hoja A4",
                  styles["Normal"]),
        Spacer(1, 12),
        _build_tickets_table(participantes),
    ]
    doc.build(elements)
    print(f"OK: {out_path}")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 108
    main(n)
