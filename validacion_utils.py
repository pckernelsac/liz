"""
Utilidades adicionales para el sistema de validación de documentos.
Funciones complementarias para el sistema de sorteos.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import json


class ValidacionManager:
    """Gestor avanzado para validación de documentos."""
    
    def __init__(self, db_path: str = 'sorteo.db'):
        self.db_path = db_path
    
    def get_connection(self):
        """Obtener conexión a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_estadisticas_validacion(self) -> Dict[str, Any]:
        """Obtener estadísticas detalladas de validación."""
        with self.get_connection() as conn:
            # Estadísticas básicas
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_comprobantes,
                    COUNT(CASE WHEN comprobante_estado = 'pendiente' THEN 1 END) as pendientes,
                    COUNT(CASE WHEN comprobante_estado = 'aprobado' THEN 1 END) as aprobados,
                    COUNT(CASE WHEN comprobante_estado = 'rechazado' THEN 1 END) as rechazados,
                    COUNT(CASE WHEN comprobante_path IS NULL THEN 1 END) as sin_comprobante
                FROM participantes 
                WHERE activo = 1
            ''').fetchone()
            
            # Estadísticas por departamento
            stats_depto = conn.execute('''
                SELECT 
                    departamento,
                    COUNT(*) as total,
                    COUNT(CASE WHEN comprobante_estado = 'aprobado' THEN 1 END) as aprobados,
                    COUNT(CASE WHEN comprobante_estado = 'rechazado' THEN 1 END) as rechazados,
                    COUNT(CASE WHEN comprobante_estado = 'pendiente' THEN 1 END) as pendientes
                FROM participantes 
                WHERE activo = 1 AND comprobante_path IS NOT NULL
                GROUP BY departamento
                ORDER BY total DESC
            ''').fetchall()
            
            # Estadísticas por día (últimos 7 días)
            stats_diarias = conn.execute('''
                SELECT 
                    date(fecha_registro) as fecha,
                    COUNT(*) as registros,
                    COUNT(CASE WHEN comprobante_path IS NOT NULL THEN 1 END) as con_comprobante
                FROM participantes 
                WHERE activo = 1 AND fecha_registro >= date('now', '-7 days')
                GROUP BY date(fecha_registro)
                ORDER BY fecha DESC
            ''').fetchall()
            
            # Validaciones recientes
            validaciones_recientes = conn.execute('''
                SELECT 
                    p.id,
                    p.nombres,
                    p.apellidos,
                    p.numero_documento,
                    p.comprobante_estado,
                    p.validado_por,
                    p.fecha_validacion,
                    p.comprobante_observaciones
                FROM participantes p
                WHERE p.fecha_validacion IS NOT NULL
                ORDER BY p.fecha_validacion DESC
                LIMIT 10
            ''').fetchall()
            
            return {
                'basicas': dict(stats),
                'por_departamento': [dict(row) for row in stats_depto],
                'diarias': [dict(row) for row in stats_diarias],
                'validaciones_recientes': [dict(row) for row in validaciones_recientes]
            }
    
    def get_comprobantes_filtrados(self, filtro: str = 'todos', 
                                 departamento: str = None,
                                 fecha_inicio: str = None,
                                 fecha_fin: str = None) -> List[Dict]:
        """Obtener comprobantes con filtros avanzados."""
        with self.get_connection() as conn:
            query = '''
                SELECT p.*, 
                       CASE 
                           WHEN p.comprobante_estado = 'pendiente' THEN 'Pendiente'
                           WHEN p.comprobante_estado = 'aprobado' THEN 'Aprobado' 
                           WHEN p.comprobante_estado = 'rechazado' THEN 'Rechazado'
                       END as estado_texto
                FROM participantes p 
                WHERE p.activo = 1
            '''
            params = []
            
            # Filtro por estado
            if filtro == 'con_comprobante':
                query += " AND p.comprobante_path IS NOT NULL"
            elif filtro == 'sin_comprobante':
                query += " AND p.comprobante_path IS NULL"
            elif filtro in ['pendiente', 'aprobado', 'rechazado']:
                query += " AND p.comprobante_estado = ?"
                params.append(filtro)
            
            # Filtro por departamento
            if departamento:
                query += " AND p.departamento = ?"
                params.append(departamento)
            
            # Filtro por fecha
            if fecha_inicio:
                query += " AND date(p.fecha_registro) >= ?"
                params.append(fecha_inicio)
            
            if fecha_fin:
                query += " AND date(p.fecha_registro) <= ?"
                params.append(fecha_fin)
            
            query += '''
                ORDER BY 
                    CASE WHEN p.comprobante_estado = 'pendiente' THEN 1 ELSE 2 END,
                    p.fecha_registro DESC
            '''
            
            comprobantes = conn.execute(query, params).fetchall()
            return [dict(c) for c in comprobantes]
    
    def get_detalle_participante(self, participante_id: int) -> Dict[str, Any]:
        """Obtener detalle completo de un participante."""
        with self.get_connection() as conn:
            # Datos del participante
            participante = conn.execute(
                'SELECT * FROM participantes WHERE id = ?', 
                (participante_id,)
            ).fetchone()
            
            if not participante:
                return None
            
            # Historial de validaciones (si existe)
            historial = conn.execute('''
                SELECT 
                    comprobante_estado as estado,
                    validado_por,
                    fecha_validacion,
                    comprobante_observaciones as observaciones
                FROM participantes 
                WHERE id = ? AND fecha_validacion IS NOT NULL
            ''', (participante_id,)).fetchall()
            
            # Verificar si ha ganado premios
            premios_ganados = conn.execute('''
                SELECT g.*, p.nombre as premio_nombre, s.nombre as sorteo_nombre
                FROM ganadores g
                JOIN premios p ON g.premio_id = p.id
                JOIN sorteos s ON g.sorteo_id = s.id
                WHERE g.participante_id = ?
                ORDER BY g.fecha_ganador DESC
            ''', (participante_id,)).fetchall()
            
            return {
                'participante': dict(participante),
                'historial_validacion': [dict(h) for h in historial],
                'premios_ganados': [dict(p) for p in premios_ganados]
            }
    
    def validar_comprobante_lote(self, participante_ids: List[int], 
                               estado: str, validado_por: str,
                               observaciones: str = '') -> Dict[str, Any]:
        """Validar múltiples comprobantes en lote."""
        if estado not in ['aprobado', 'rechazado']:
            return {'success': False, 'message': 'Estado inválido'}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            validados = 0
            errores = []
            
            for participante_id in participante_ids:
                try:
                    # Verificar que el participante existe y tiene comprobante
                    participante = conn.execute(
                        'SELECT * FROM participantes WHERE id = ? AND comprobante_path IS NOT NULL', 
                        (participante_id,)
                    ).fetchone()
                    
                    if participante:
                        cursor.execute('''
                            UPDATE participantes 
                            SET comprobante_estado = ?, 
                                comprobante_observaciones = ?,
                                validado_por = ?,
                                fecha_validacion = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (estado, observaciones, validado_por, participante_id))
                        validados += 1
                    else:
                        errores.append(f"Participante {participante_id} no encontrado o sin comprobante")
                        
                except Exception as e:
                    errores.append(f"Error en participante {participante_id}: {str(e)}")
            
            conn.commit()
            
            return {
                'success': True,
                'validados': validados,
                'errores': errores,
                'message': f'Se validaron {validados} comprobantes como {estado}'
            }
    
    def generar_reporte_validacion(self, formato: str = 'json') -> str:
        """Generar reporte completo de validación."""
        stats = self.get_estadisticas_validacion()
        
        reporte = {
            'fecha_generacion': datetime.now().isoformat(),
            'resumen': {
                'total_participantes': stats['basicas']['total_comprobantes'],
                'con_comprobante': stats['basicas']['total_comprobantes'] - stats['basicas']['sin_comprobante'],
                'sin_comprobante': stats['basicas']['sin_comprobante'],
                'pendientes': stats['basicas']['pendientes'],
                'aprobados': stats['basicas']['aprobados'],
                'rechazados': stats['basicas']['rechazados'],
                'tasa_aprobacion': round(
                    (stats['basicas']['aprobados'] / 
                     max(1, stats['basicas']['aprobados'] + stats['basicas']['rechazados'])) * 100, 2
                )
            },
            'por_departamento': stats['por_departamento'],
            'tendencia_diaria': stats['diarias'],
            'validaciones_recientes': stats['validaciones_recientes']
        }
        
        if formato == 'json':
            return json.dumps(reporte, indent=2, ensure_ascii=False)
        
        # TODO: Implementar otros formatos (Excel, PDF, etc.)
        return json.dumps(reporte, indent=2, ensure_ascii=False)
    
    def cleanup_archivos_huerfanos(self) -> Dict[str, Any]:
        """Limpiar archivos de comprobantes huérfanos."""
        upload_folder = Path('uploads')
        if not upload_folder.exists():
            return {'success': False, 'message': 'Carpeta uploads no existe'}
        
        with self.get_connection() as conn:
            # Obtener todos los paths de comprobantes en la BD
            paths_bd = set()
            comprobantes = conn.execute(
                'SELECT comprobante_path FROM participantes WHERE comprobante_path IS NOT NULL'
            ).fetchall()
            
            for comp in comprobantes:
                if comp['comprobante_path']:
                    paths_bd.add(comp['comprobante_path'])
        
        # Obtener todos los archivos en el directorio
        archivos_disco = {f.name for f in upload_folder.iterdir() if f.is_file()}
        
        # Encontrar archivos huérfanos
        huerfanos = archivos_disco - paths_bd
        
        # Eliminar archivos huérfanos (opcional, por seguridad solo reportar)
        eliminados = []
        for archivo in huerfanos:
            archivo_path = upload_folder / archivo
            try:
                # Por seguridad, solo reportar. Descomentar la siguiente línea para eliminar
                # archivo_path.unlink()
                eliminados.append(archivo)
            except Exception as e:
                continue
        
        return {
            'success': True,
            'total_archivos_disco': len(archivos_disco),
            'total_referencias_bd': len(paths_bd),
            'archivos_huerfanos': list(huerfanos),
            'eliminados': eliminados,
            'message': f'Se encontraron {len(huerfanos)} archivos huérfanos'
        }


# Funciones de utilidad para templates
def format_fecha(fecha_str: str) -> str:
    """Formatear fecha para mostrar en templates."""
    if not fecha_str:
        return 'N/A'
    
    try:
        dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return fecha_str

def get_estado_color(estado: str) -> str:
    """Obtener color CSS según el estado."""
    colores = {
        'pendiente': 'yellow',
        'aprobado': 'green',
        'rechazado': 'red'
    }
    return colores.get(estado, 'gray')

def calcular_tasa_validacion(aprobados: int, rechazados: int) -> float:
    """Calcular tasa de validación."""
    total = aprobados + rechazados
    if total == 0:
        return 0.0
    return round((aprobados / total) * 100, 2)

def es_archivo_imagen(filename: str) -> bool:
    """Verificar si un archivo es una imagen."""
    if not filename:
        return False
    
    extensiones_imagen = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    return Path(filename).suffix.lower() in extensiones_imagen

def get_icono_archivo(filename: str) -> str:
    """Obtener icono FontAwesome según el tipo de archivo."""
    if not filename:
        return 'fas fa-file'
    
    ext = Path(filename).suffix.lower()
    
    iconos = {
        '.pdf': 'fas fa-file-pdf',
        '.jpg': 'fas fa-file-image',
        '.jpeg': 'fas fa-file-image',
        '.png': 'fas fa-file-image',
        '.gif': 'fas fa-file-image',
        '.webp': 'fas fa-file-image',
        '.doc': 'fas fa-file-word',
        '.docx': 'fas fa-file-word',
        '.xls': 'fas fa-file-excel',
        '.xlsx': 'fas fa-file-excel'
    }
    
    return iconos.get(ext, 'fas fa-file')

