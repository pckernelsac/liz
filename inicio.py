#!/usr/bin/env python3
"""
Script de inicio automático para el Sistema de Sorteos PREMIOS LORENZO
Optimizado para Python 3.11+
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Error: Se requiere Python 3.11 o superior")
        print(f"📍 Versión actual: Python {version.major}.{version.minor}.{version.micro}")
        print("📥 Descarga Python 3.11+ desde: https://www.python.org/downloads/")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_and_install_requirements():
    """Verificar e instalar dependencias"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ Error: No se encontró requirements.txt")
        return False
    
    print("📦 Verificando dependencias...")
    
    try:
        # Intentar importar las dependencias principales
        import fastapi
        import uvicorn
        import werkzeug
        import PIL
        import openpyxl
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"⚠️  Dependencia faltante: {e.name}")
        print("📥 Instalando dependencias...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            print("✅ Dependencias instaladas correctamente")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error al instalar dependencias")
            print("💡 Intenta manualmente: pip install -r requirements.txt")
            return False

def create_env_file():
    """Crear archivo .env si no existe"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("⚙️  Creando archivo de configuración...")
        env_file.write_text(env_example.read_text())
        print("✅ Archivo .env creado desde .env.example")
        print("📝 Puedes editar .env para personalizar la configuración")

def check_directories():
    """Verificar y crear directorios necesarios"""
    directories = [
        "uploads",
        "static/img",
        "static/css", 
        "static/js"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directorios verificados")

def display_banner():
    """Mostrar banner de inicio"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║           🎯 SISTEMA DE SORTEOS PREMIOS LORENZO           ║
    ║                                                           ║
    ║           🐍 Python 3.11+ Optimized                      ║
    ║           ⚡ FastAPI + Uvicorn                            ║
    ║           🎨 Tailwind CSS Professional UI                 ║
    ║           🔒 Secure Random Algorithm                      ║
    ║           📱 Responsive Design                            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Función principal del script de inicio"""
    display_banner()
    
    print("🚀 Iniciando verificaciones del sistema...\n")
    
    # Verificar Python
    if not check_python_version():
        input("Presiona Enter para salir...")
        return
    
    # Verificar dependencias
    if not check_and_install_requirements():
        input("Presiona Enter para salir...")
        return
    
    # Crear archivo de configuración
    create_env_file()
    
    # Verificar directorios
    check_directories()
    
    print("\n" + "="*60)
    print("✅ SISTEMA LISTO PARA EJECUTAR")
    print("="*60)
    
    # Información del sistema
    print(f"""
    📋 INFORMACIÓN DEL SISTEMA:
    ─────────────────────────────────
    🐍 Python: {sys.version.split()[0]}
    📁 Directorio: {Path.cwd()}
    🌐 URL Principal: http://localhost:5000
    👤 Panel Admin: http://localhost:5000/admin
    📱 Responsive: Móvil y Desktop
    🔒 Seguridad: Algoritmos seguros
    
    📚 CARACTERÍSTICAS PRINCIPALES:
    ─────────────────────────────────
    ✅ Registro de participantes
    ✅ Subida de comprobantes  
    ✅ Consulta de tickets
    ✅ Sorteo automático seguro
    ✅ Panel administrativo
    ✅ Exportación a Excel
    ✅ Estadísticas en tiempo real
    ✅ Diseño profesional
    
    🎯 CÓMO USAR:
    ─────────────────────────────────
    1. El servidor se iniciará automáticamente
    2. Abre http://localhost:5000 en tu navegador
    3. Los participantes pueden registrarse
    4. Usa /admin para gestionar el sistema
    5. Realiza sorteos desde el panel admin
    """)
    
    print("="*60)
    input("Presiona Enter para iniciar el servidor...")
    
    try:
        # Importar y ejecutar la aplicación
        from app import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
