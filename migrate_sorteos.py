"""
Script de migración para agregar sistema de sorteos múltiples.
Ejecutar una sola vez para actualizar la base de datos existente.
"""

import sqlite3
from datetime import datetime

def migrate_database():
    """Migra la base de datos para soportar múltiples sorteos."""
    conn = sqlite3.connect('sorteo.db')
    cursor = conn.cursor()
    
    print("🔄 Iniciando migración de base de datos...")
    
    try:
        # 1. Agregar columna sorteo_id a participantes si no existe
        print("\n📊 Verificando estructura de tabla participantes...")
        cursor.execute("PRAGMA table_info(participantes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sorteo_id' not in columns:
            print("   ➕ Agregando columna sorteo_id a participantes...")
            cursor.execute('ALTER TABLE participantes ADD COLUMN sorteo_id INTEGER')
            conn.commit()
            print("   ✅ Columna sorteo_id agregada")
        else:
            print("   ℹ️  Columna sorteo_id ya existe")
        
        # 2. Verificar si existe sorteo activo
        print("\n🎯 Verificando sorteos activos...")
        cursor.execute("SELECT * FROM sorteos WHERE estado = 'activo' LIMIT 1")
        sorteo_activo = cursor.fetchone()
        
        if not sorteo_activo:
            print("   ➕ Creando sorteo inicial...")
            cursor.execute('''
                INSERT INTO sorteos (nombre, fecha_sorteo, descripcion, estado)
                VALUES (?, ?, ?, ?)
            ''', (
                'Sorteo Inicial',
                datetime.now().isoformat(),
                'Sorteo creado automáticamente por el sistema',
                'activo'
            ))
            sorteo_id = cursor.lastrowid
            conn.commit()
            print(f"   ✅ Sorteo activo creado con ID: {sorteo_id}")
        else:
            sorteo_id = sorteo_activo[0]
            print(f"   ℹ️  Ya existe sorteo activo con ID: {sorteo_id}")
        
        # 3. Asignar participantes existentes al sorteo activo
        print("\n👥 Asignando participantes existentes al sorteo activo...")
        cursor.execute('SELECT COUNT(*) FROM participantes WHERE sorteo_id IS NULL')
        sin_asignar = cursor.fetchone()[0]
        
        if sin_asignar > 0:
            print(f"   ➕ Asignando {sin_asignar} participantes...")
            cursor.execute('UPDATE participantes SET sorteo_id = ? WHERE sorteo_id IS NULL', (sorteo_id,))
            conn.commit()
            print(f"   ✅ {sin_asignar} participantes asignados al sorteo activo")
        else:
            print("   ℹ️  Todos los participantes ya están asignados")
        
        # 4. Agregar índice para mejorar rendimiento
        print("\n⚡ Optimizando índices...")
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_participantes_sorteo ON participantes(sorteo_id)')
            conn.commit()
            print("   ✅ Índice creado exitosamente")
        except Exception as e:
            print(f"   ⚠️  Índice ya existe: {e}")
        
        # 5. Verificar estructura final
        print("\n✅ Verificando estructura final...")
        cursor.execute('''
            SELECT 
                COUNT(*) as total_participantes,
                sorteo_id
            FROM participantes 
            GROUP BY sorteo_id
        ''')
        resultados = cursor.fetchall()
        
        for row in resultados:
            print(f"   📊 Sorteo ID {row[1]}: {row[0]} participantes")
        
        print("\n" + "="*60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\n🚀 Puedes reiniciar el servidor ahora: python app.py")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la migración: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════╗
║         MIGRACIÓN: SISTEMA DE SORTEOS MÚLTIPLES          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    respuesta = input("¿Deseas continuar con la migración? (si/no): ").lower()
    
    if respuesta in ['si', 's', 'yes', 'y']:
        migrate_database()
    else:
        print("\n❌ Migración cancelada por el usuario")
