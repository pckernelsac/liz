#!/usr/bin/env python3
"""
Script para limpiar premios duplicados existentes
Ejecutar UNA SOLA VEZ después del fix
"""

import sqlite3
from pathlib import Path

def limpiar_premios_duplicados():
    """Limpiar premios duplicados existentes en la base de datos"""
    
    db_path = 'sorteo.db'
    if not Path(db_path).exists():
        print("❌ Base de datos no encontrada")
        return
    
    print("🔧 LIMPIANDO PREMIOS DUPLICADOS")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar estado inicial
        total_antes = conn.execute('SELECT COUNT(*) as count FROM premios WHERE activo = 1').fetchone()['count']
        print(f"📊 Total premios antes: {total_antes}")
        
        # Encontrar duplicados por nombre
        duplicados = conn.execute('''
            SELECT nombre, COUNT(*) as count, GROUP_CONCAT(id ORDER BY id) as ids
            FROM premios 
            WHERE activo = 1 
            GROUP BY nombre 
            HAVING count > 1
            ORDER BY nombre
        ''').fetchall()
        
        if not duplicados:
            print("✅ No se encontraron premios duplicados")
            conn.close()
            return
        
        print(f"⚠️  Encontrados {len(duplicados)} premios con duplicados:")
        
        premios_desactivados = 0
        
        for duplicado in duplicados:
            nombre = duplicado['nombre']
            count = duplicado['count']
            ids = duplicado['ids'].split(',')
            
            print(f"\n📋 {nombre}: {count} copias (IDs: {', '.join(ids)})")
            
            # Mantener solo el último ID (más reciente), desactivar los demás
            for i, id_premio in enumerate(ids[:-1]):  # Todos excepto el último
                cursor.execute('UPDATE premios SET activo = 0 WHERE id = ?', (int(id_premio),))
                print(f"   🗑️  Desactivado ID {id_premio}")
                premios_desactivados += 1
            
            print(f"   ✅ Mantenido ID {ids[-1]} (más reciente)")
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar estado final
        total_despues = conn.execute('SELECT COUNT(*) as count FROM premios WHERE activo = 1').fetchone()['count']
        
        print("\n" + "=" * 40)
        print("🎉 LIMPIEZA COMPLETADA")
        print(f"📊 Premios antes: {total_antes}")
        print(f"📊 Premios después: {total_despues}")
        print(f"🗑️  Premios desactivados: {premios_desactivados}")
        
        # Mostrar premios activos finales
        premios_activos = conn.execute('''
            SELECT id, nombre, orden 
            FROM premios 
            WHERE activo = 1 
            ORDER BY orden
        ''').fetchall()
        
        print(f"\n🏆 PREMIOS ACTIVOS FINALES ({len(premios_activos)}):")
        for premio in premios_activos:
            print(f"   {premio['orden']}. {premio['nombre']} (ID: {premio['id']})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def verificar_estado():
    """Solo verificar sin hacer cambios"""
    db_path = 'sorteo.db'
    if not Path(db_path).exists():
        print("❌ Base de datos no encontrada")
        return
    
    print("🔍 VERIFICANDO ESTADO ACTUAL")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Total de premios
        total = conn.execute('SELECT COUNT(*) as count FROM premios WHERE activo = 1').fetchone()['count']
        print(f"📊 Total premios activos: {total}")
        
        # Verificar duplicados
        duplicados = conn.execute('''
            SELECT nombre, COUNT(*) as count 
            FROM premios 
            WHERE activo = 1 
            GROUP BY nombre 
            HAVING count > 1
        ''').fetchall()
        
        if duplicados:
            print(f"⚠️  {len(duplicados)} premios tienen duplicados:")
            for dup in duplicados:
                print(f"   - {dup['nombre']}: {dup['count']} copias")
        else:
            print("✅ No hay duplicados")
        
        # Mostrar todos los premios activos
        premios = conn.execute('''
            SELECT id, nombre, orden, created_at
            FROM premios 
            WHERE activo = 1 
            ORDER BY orden, id
        ''').fetchall()
        
        print(f"\n🏆 TODOS LOS PREMIOS ACTIVOS ({len(premios)}):")
        for premio in premios:
            fecha = premio['created_at'][:19] if premio['created_at'] else 'N/A'
            print(f"   ID:{premio['id']} | Orden:{premio['orden']} | {premio['nombre']} | {fecha}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error al verificar: {e}")

if __name__ == "__main__":
    print("🎯 SISTEMA DE SORTEOS - LIMPIADOR DE DUPLICADOS")
    print("=" * 50)
    
    opcion = input("""
¿Qué deseas hacer?

1. 🔧 Limpiar duplicados (RECOMENDADO)
2. 🔍 Solo verificar estado
3. ❌ Salir

Elige una opción (1-3): """).strip()
    
    if opcion == '1':
        print("\n⚠️  IMPORTANTE: Este proceso desactivará premios duplicados")
        print("   Solo se mantendrá la copia más reciente de cada premio")
        
        confirmar = input("\n¿Continuar? (s/N): ").strip().lower()
        
        if confirmar in ['s', 'si', 'y', 'yes']:
            limpiar_premios_duplicados()
        else:
            print("👋 Operación cancelada")
    
    elif opcion == '2':
        verificar_estado()
    
    else:
        print("👋 Saliendo...")
