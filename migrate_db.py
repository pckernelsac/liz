import sqlite3
import shutil
from pathlib import Path
import time

def migrate_database():
    """Migrar la base de datos para soportar múltiples tickets con el mismo DNI."""
    db_path = Path('sorteo.db')
    
    if not db_path.exists():
        print("❌ Base de datos no encontrada.")
        return False
    
    try:
        # Hacer backup
        backup_path = f"sorteo.db.backup_{int(time.time())}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup creado: {backup_path}")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🔧 Iniciando migración...")
        
        # Crear nueva tabla sin UNIQUE constraint
        cursor.execute('''
            CREATE TABLE participantes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_documento TEXT NOT NULL CHECK(tipo_documento IN ('DNI', 'CE')),
                numero_documento TEXT NOT NULL,
                nombres TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                whatsapp TEXT NOT NULL,
                departamento TEXT NOT NULL,
                comprobante_path TEXT,
                comprobante_estado TEXT DEFAULT 'pendiente' CHECK(comprobante_estado IN ('pendiente', 'aprobado', 'rechazado')),
                comprobante_observaciones TEXT,
                validado_por TEXT,
                fecha_validacion DATETIME,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Copiar datos limpiando sufijos
        cursor.execute('SELECT * FROM participantes')
        rows = cursor.fetchall()
        
        for row in rows:
            # Limpiar documento de sufijos _T2, _T3, etc.
            numero_documento = str(row[2])
            if '_T' in numero_documento:
                numero_documento = numero_documento.split('_T')[0]
            
            # Insertar en nueva tabla
            cursor.execute('''
                INSERT INTO participantes_new 
                (id, tipo_documento, numero_documento, nombres, apellidos, whatsapp, departamento, 
                 comprobante_path, comprobante_estado, comprobante_observaciones, validado_por, 
                 fecha_validacion, fecha_registro, activo, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row[0], row[1], numero_documento, row[3], row[4], row[5], row[6], 
                  row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15]))
        
        # Reemplazar tabla
        cursor.execute('DROP TABLE participantes')
        cursor.execute('ALTER TABLE participantes_new RENAME TO participantes')
        
        # Crear índices
        cursor.execute('CREATE INDEX idx_participantes_documento ON participantes(numero_documento)')
        cursor.execute('CREATE INDEX idx_participantes_activo ON participantes(activo)')
        
        conn.commit()
        conn.close()
        
        print(f"🎉 Migración completada! {len(rows)} registros procesados")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    migrate_database()
