# Configuración del Sistema de Sorteos

# Información del sorteo
SORTEO_NOMBRE = "PREMIOS LORENZO"
FECHA_SORTEO = "martes 30 de septiembre a las 5:00 p.m"
FACEBOOK_PAGE = "PREMIOS LORENZO"

# Configuración de archivos
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'pdf']

# Configuración de la aplicación
DEBUG_MODE = True
HOST = '0.0.0.0'
PORT = 5000

# WhatsApp de contacto
WHATSAPP_CONTACT = "1234567890"

# Mensajes del sistema
MENSAJES = {
    'registro_exitoso': '¡Registro exitoso! Tu número de participación es: ',
    'documento_duplicado': 'Este documento ya está registrado',
    'campos_obligatorios': 'Todos los campos son obligatorios',
    'acepta_terminos': 'Debe aceptar los términos y condiciones',
    'mayor_edad': 'Solo válido para mayores de edad +18',
    'participacion_responsable': 'Participa de manera responsable'
}

# Colores del tema (Tailwind CSS)
COLORES = {
    'primario': 'orange-500',
    'secundario': 'purple-600',
    'exito': 'green-500',
    'error': 'red-500',
    'warning': 'yellow-500',
    'info': 'blue-500'
}
