import random
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
import csv

load_dotenv()

@dataclass
class Usuario:
    idUser: int
    usuario: str
    curp: str

@dataclass
class Habilidad:
    idHabilidad: int
    habilidad: str

@dataclass
class Reactivo:
    idReactivo: int
    reactivo: str

@dataclass
class Evaluacion:
    idEvaluacion: int
    idUser: int
    idHabilidad: int
    idReactivo: int
    calificacion: float
    fechaEvaluacion: datetime
    tiempoRespuesta: int

class MySQLManager:
    """Gestor de conexión a MySQL"""
    
    def __init__(self):
        """Inicializa la conexión a MySQL usando variables de entorno"""
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establece la conexión a MySQL"""
        try:
            # Obtener configuración del archivo .env
            host = os.getenv('DB_HOST', 'localhost')
            user = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            database = os.getenv('DB_NAME')
            port = int(os.getenv('DB_PORT', 3306))
            
            # Validar que las variables críticas estén definidas
            if not all([user, password, database]):
                raise ValueError("Faltan variables de entorno críticas. Verifica DB_USER, DB_PASSWORD y DB_NAME en el archivo .env")
            
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                autocommit=True
            )
            
            print(f"✅ Conexión establecida exitosamente con MySQL")            
        except mysql.connector.Error as e:
            print(f"❌ Error de MySQL: {e}")
            raise
        except Exception as e:
            print(f"❌ Error al conectar con MySQL: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Ejecuta una consulta y retorna los resultados"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except mysql.connector.Error as e:
            print(f"❌ Error ejecutando consulta MySQL: {e}")
            print(f"Query: {query}")
            raise
        except Exception as e:
            print(f"❌ Error ejecutando consulta: {e}")
            print(f"Query: {query}")
            raise
    
    def get_evaluaciones_por_habilidad(self, id_habilidad: int) -> List[Evaluacion]:
        """Obtiene todas las evaluaciones de una habilidad específica"""
        query = """
        SELECT idEvaluacion, idUser, idHabilidad, idReactivo, 
               calificacion, fechaEvaluacion, tiempoRespuesta
        FROM Evaluacion 
        WHERE idHabilidad = %s
        ORDER BY calificacion ASC
        """
        
        results = self.execute_query(query, (id_habilidad,))
        
        evaluaciones = []
        for row in results:
            # Manejar fecha
            fecha_eval = row[5]
            if isinstance(fecha_eval, str):
                try:
                    fecha_eval = datetime.strptime(fecha_eval, "%Y-%m-%d %H:%M:%S")
                except:
                    fecha_eval = datetime.now()
            
            evaluacion = Evaluacion(
                idEvaluacion=row[0],
                idUser=row[1],
                idHabilidad=row[2],
                idReactivo=row[3],
                calificacion=float(row[4]),
                fechaEvaluacion=fecha_eval,
                tiempoRespuesta=row[6]
            )
            evaluaciones.append(evaluacion)
        
        return evaluaciones
    
    def get_todas_las_habilidades(self) -> List[Habilidad]:
        """Obtiene todas las habilidades de la base de datos"""
        query = "SELECT idHabilidad, habilidad FROM Habilidad ORDER BY idHabilidad"
        results = self.execute_query(query)
        
        habilidades = []
        for row in results:
            habilidad = Habilidad(
                idHabilidad=row[0],
                habilidad=row[1]
            )
            habilidades.append(habilidad)
        
        return habilidades
    
    def get_usuario_by_id(self, id_user: int) -> Optional[Usuario]:
        """Obtiene un usuario por su ID"""
        query = "SELECT idUser, usuario, curp FROM Usuario WHERE idUser = %s"
        results = self.execute_query(query, (id_user,))
        
        if results:
            row = results[0]
            return Usuario(
                idUser=row[0],
                usuario=row[1],
                curp=row[2]
            )
        return None
    
    def get_reactivo_by_id(self, id_reactivo: int) -> Optional[Reactivo]:
        """Obtiene un reactivo por su ID"""
        query = "SELECT idReactivo, reactivo FROM Reactivo WHERE idReactivo = %s"
        results = self.execute_query(query, (id_reactivo,))
        
        if results:
            row = results[0]
            return Reactivo(
                idReactivo=row[0],
                reactivo=row[1]
            )
        return None
    
    def get_estadisticas_generales(self) -> Dict:
        """Obtiene estadísticas generales de la base de datos"""
        stats = {}
        
        try:
            result = self.execute_query("SELECT COUNT(*) FROM Usuario")
            stats['total_usuarios'] = result[0][0]
            
            # Contar habilidades
            result = self.execute_query("SELECT COUNT(*) FROM Habilidad")
            stats['total_habilidades'] = result[0][0]
            
            # Contar reactivos
            result = self.execute_query("SELECT COUNT(*) FROM Reactivo")
            stats['total_reactivos'] = result[0][0]
            
            # Contar evaluaciones
            result = self.execute_query("SELECT COUNT(*) FROM Evaluacion")
            stats['total_evaluaciones'] = result[0][0]
            
            # Rango de calificaciones
            result = self.execute_query("SELECT MIN(calificacion), MAX(calificacion), AVG(calificacion) FROM Evaluacion")
            if result[0][0] is not None:
                stats['calificacion_minima'] = float(result[0][0])
                stats['calificacion_maxima'] = float(result[0][1])
                stats['calificacion_promedio'] = round(float(result[0][2]), 2)
            
            # Fecha más antigua y más reciente
            result = self.execute_query("SELECT MIN(fechaEvaluacion), MAX(fechaEvaluacion) FROM Evaluacion")
            if result[0][0] is not None:
                stats['fecha_primera_evaluacion'] = result[0][0]
                stats['fecha_ultima_evaluacion'] = result[0][1]
                
        except Exception as e:
            print(f"⚠️ Error obteniendo estadísticas: {e}")
        
        return stats
    
    def test_conexion(self) -> bool:
        """Prueba la conexión y estructura de la base de datos"""
        try:
            print("\n🔍 Probando conexión y estructura de la base de datos...")
            
            # Verificar tablas principales
            tablas_requeridas = ['Usuario', 'Habilidad', 'Reactivo', 'Evaluacion']
            
            for tabla in tablas_requeridas:
                try:
                    query = f"SHOW TABLES LIKE '{tabla}'"
                    result = self.execute_query(query)
                    if result:
                        print(f"  ✅ Tabla {tabla} encontrada")
                    else:
                        print(f"  ❌ Tabla {tabla} NO encontrada")
                        return False
                        
                except Exception as e:
                    print(f"  ❌ Error verificando tabla {tabla}: {e}")
                    return False
            
            # Obtener estadísticas
            stats = self.get_estadisticas_generales()
            print(f"\n📊 Estadísticas de la base de datos:")
            for key, value in stats.items():
                key_formatted = key.replace('_', ' ').title()
                print(f"  • {key_formatted}: {value}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en test de conexión: {e}")
            return False
    
    def verificar_integridad_datos(self) -> bool:
        """Verifica la integridad referencial de los datos"""
        try:
            print("\n🔍 Verificando integridad de datos...")
            
            query = """
            SELECT COUNT(*) FROM Evaluacion e 
            LEFT JOIN Usuario u ON e.idUser = u.idUser 
            WHERE u.idUser IS NULL
            """
            result = self.execute_query(query)
            huerfanas_usuario = result[0][0]
            
            query = """
            SELECT COUNT(*) FROM Evaluacion e 
            LEFT JOIN Habilidad h ON e.idHabilidad = h.idHabilidad 
            WHERE h.idHabilidad IS NULL
            """
            result = self.execute_query(query)
            huerfanas_habilidad = result[0][0]
            
            query = """
            SELECT COUNT(*) FROM Evaluacion e 
            LEFT JOIN Reactivo r ON e.idReactivo = r.idReactivo 
            WHERE r.idReactivo IS NULL
            """
            result = self.execute_query(query)
            huerfanas_reactivo = result[0][0]
            
            if huerfanas_usuario == 0 and huerfanas_habilidad == 0 and huerfanas_reactivo == 0:
                print("  ✅ Integridad referencial correcta")
                return True
            else:
                print(f"  ⚠️ Problemas de integridad encontrados:")
                if huerfanas_usuario > 0:
                    print(f"    • {huerfanas_usuario} evaluaciones con usuarios inexistentes")
                if huerfanas_habilidad > 0:
                    print(f"    • {huerfanas_habilidad} evaluaciones con habilidades inexistentes")
                if huerfanas_reactivo > 0:
                    print(f"    • {huerfanas_reactivo} evaluaciones con reactivos inexistentes")
                return False
                
        except Exception as e:
            print(f"❌ Error verificando integridad: {e}")
            return False
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 Conexión cerrada")

class PeorResultadoIndividuo:
    """Representa un individuo en el algoritmo genético"""
    
    def __init__(self, evaluaciones: List[Evaluacion], habilidad_id: int):
        self.habilidad_id = habilidad_id
        self.evaluaciones = evaluaciones
        self.genes = self._generar_genes_aleatorios()
        self.fitness = 0
        self.peores_resultados = []
    
    def _generar_genes_aleatorios(self) -> List[int]:
        """Genera genes aleatorios (índices de evaluaciones)"""
        if not self.evaluaciones:
            return []
        
        # Seleccionar entre 3 y 7 evaluaciones (o todas si hay menos)
        num_genes = min(random.randint(3, 7), len(self.evaluaciones))
        return random.sample(range(len(self.evaluaciones)), num_genes)
    
    def calcular_fitness(self):
        """Calcula el fitness basado en qué tan malos son los resultados seleccionados"""
        if not self.genes or not self.evaluaciones:
            self.fitness = float('inf')
            return
        
        try:
            calificaciones_seleccionadas = [self.evaluaciones[i].calificacion for i in self.genes]
            usuarios_seleccionados = set(self.evaluaciones[i].idUser for i in self.genes)
            
            # Penalizar si hay muchos resultados del mismo usuario (falta de diversidad)
            penalty_diversidad = len(self.genes) - len(usuarios_seleccionados)
            
            # Fitness: promedio bajo de calificaciones + penalización por falta de diversidad
            promedio_calificaciones = sum(calificaciones_seleccionadas) / len(calificaciones_seleccionadas)
            self.fitness = promedio_calificaciones + (penalty_diversidad * 0.5)
            
            # Guardar los peores resultados para reporte
            self.peores_resultados = [(self.evaluaciones[i], self.evaluaciones[i].calificacion) 
                                     for i in self.genes]
            self.peores_resultados.sort(key=lambda x: x[1])  # Ordenar por calificación
            
        except Exception as e:
            print(f"⚠️ Error calculando fitness: {e}")
            self.fitness = float('inf')

class AlgoritmoGenetico:
    """Algoritmo genético para encontrar los peores resultados por habilidad"""
    
    def __init__(self, db_manager: MySQLManager, poblacion_size=50, 
                 generaciones=100, tasa_mutacion=0.1, tasa_cruzamiento=0.8):
        self.db_manager = db_manager
        self.poblacion_size = poblacion_size
        self.generaciones = generaciones
        self.tasa_mutacion = tasa_mutacion
        self.tasa_cruzamiento = tasa_cruzamiento
        self.resultados_por_habilidad = {}
    
    def ejecutar_para_todas_las_habilidades(self):
        """Ejecuta el algoritmo genético para cada habilidad"""
        habilidades = self.db_manager.get_todas_las_habilidades()
        
        if not habilidades:
            print("❌ No se encontraron habilidades en la base de datos")
            return
        
        print(f"\n🎯 Analizando {len(habilidades)} habilidades...")
        
        for i, habilidad in enumerate(habilidades, 1):
            print(f"\n[{i}/{len(habilidades)}] 🔍 Analizando: {habilidad.habilidad}")
            evaluaciones = self.db_manager.get_evaluaciones_por_habilidad(habilidad.idHabilidad)
            
            if not evaluaciones:
                print(f"  ⚠️ No hay evaluaciones para la habilidad {habilidad.habilidad}")
                continue
            
            if len(evaluaciones) < 5:
                print(f"  ⚠️ Pocas evaluaciones ({len(evaluaciones)}) para la habilidad {habilidad.habilidad}")
                # Aún así procesamos, pero con advertencia
            
            mejor_individuo = self._ejecutar_algoritmo_genetico(evaluaciones, habilidad.idHabilidad)
            self.resultados_por_habilidad[habilidad.idHabilidad] = {
                'habilidad': habilidad,
                'mejor_individuo': mejor_individuo,
                'peores_resultados': mejor_individuo.peores_resultados,
                'total_evaluaciones': len(evaluaciones)
            }
    
    def _ejecutar_algoritmo_genetico(self, evaluaciones: List[Evaluacion], habilidad_id: int):
        """Ejecuta el algoritmo genético para una habilidad específica"""
        
        # Inicializar población
        poblacion = []
        for _ in range(self.poblacion_size):
            individuo = PeorResultadoIndividuo(evaluaciones, habilidad_id)
            individuo.calcular_fitness()
            poblacion.append(individuo)
        
        mejor_fitness_historico = float('inf')
        mejor_individuo = None
        sin_mejora = 0
        
        for generacion in range(self.generaciones):
            # Selección, cruzamiento y mutación
            nueva_poblacion = []
            
            while len(nueva_poblacion) < self.poblacion_size:
                # Seleccionar padres
                padre1 = self._seleccion_torneo(poblacion)
                padre2 = self._seleccion_torneo(poblacion)
                
                # Cruzamiento
                if random.random() < self.tasa_cruzamiento:
                    hijo1, hijo2 = self._cruzamiento(padre1, padre2, evaluaciones, habilidad_id)
                else:
                    hijo1 = PeorResultadoIndividuo(evaluaciones, habilidad_id)
                    hijo1.genes = padre1.genes.copy()
                    hijo2 = PeorResultadoIndividuo(evaluaciones, habilidad_id)
                    hijo2.genes = padre2.genes.copy()
                
                # Mutación
                if random.random() < self.tasa_mutacion:
                    self._mutar(hijo1, evaluaciones)
                if random.random() < self.tasa_mutacion:
                    self._mutar(hijo2, evaluaciones)
                
                # Evaluar fitness de los hijos
                hijo1.calcular_fitness()
                hijo2.calcular_fitness()
                
                nueva_poblacion.extend([hijo1, hijo2])
            
            # Mantener solo el tamaño de población deseado
            poblacion = nueva_poblacion[:self.poblacion_size]
            
            # Encontrar el mejor individuo de esta generación
            mejor_actual = min(poblacion, key=lambda x: x.fitness)
            
            if mejor_actual.fitness < mejor_fitness_historico:
                mejor_fitness_historico = mejor_actual.fitness
                mejor_individuo = mejor_actual
                sin_mejora = 0
            else:
                sin_mejora += 1
            
            # Mostrar progreso cada 25 generaciones
            if generacion % 25 == 0:
                print(f"    Gen {generacion}: Mejor fitness = {mejor_fitness_historico:.3f}")
            
            # Parada temprana si no hay mejora en 30 generaciones
            if sin_mejora >= 30:
                print(f"    Parada temprana en generación {generacion} (sin mejora)")
                break
        
        return mejor_individuo
    
    def _seleccion_torneo(self, poblacion: List[PeorResultadoIndividuo], 
                         tournament_size=3) -> PeorResultadoIndividuo:
        """Selección por torneo"""
        torneo = random.sample(poblacion, min(tournament_size, len(poblacion)))
        return min(torneo, key=lambda x: x.fitness)
    
    def _cruzamiento(self, padre1: PeorResultadoIndividuo, padre2: PeorResultadoIndividuo,
                    evaluaciones: List[Evaluacion], habilidad_id: int) -> Tuple[PeorResultadoIndividuo, PeorResultadoIndividuo]:
        """Cruzamiento de un punto"""
        hijo1 = PeorResultadoIndividuo(evaluaciones, habilidad_id)
        hijo2 = PeorResultadoIndividuo(evaluaciones, habilidad_id)
        
        if len(padre1.genes) > 1 and len(padre2.genes) > 1:
            punto_cruce = random.randint(1, min(len(padre1.genes), len(padre2.genes)) - 1)
            
            hijo1.genes = padre1.genes[:punto_cruce] + padre2.genes[punto_cruce:]
            hijo2.genes = padre2.genes[:punto_cruce] + padre1.genes[punto_cruce:]
            
            # Eliminar duplicados y mantener dentro del rango válido
            hijo1.genes = list(set(g for g in hijo1.genes if 0 <= g < len(evaluaciones)))[:7]
            hijo2.genes = list(set(g for g in hijo2.genes if 0 <= g < len(evaluaciones)))[:7]
        else:
            hijo1.genes = padre1.genes.copy()
            hijo2.genes = padre2.genes.copy()
        
        return hijo1, hijo2
    
    def _mutar(self, individuo: PeorResultadoIndividuo, evaluaciones: List[Evaluacion]):
        """Mutación: cambiar aleatoriamente algunos genes"""
        if not individuo.genes or not evaluaciones:
            return
        
        for i in range(len(individuo.genes)):
            if random.random() < 0.3:  # 30% de probabilidad de mutar cada gen
                individuo.genes[i] = random.randint(0, len(evaluaciones) - 1)
        
        # Eliminar duplicados
        individuo.genes = list(set(individuo.genes))
        
        # Asegurar que tengamos al menos un gen
        if not individuo.genes:
            individuo.genes = [random.randint(0, len(evaluaciones) - 1)]
    
    def generar_reporte(self):
        """Genera un reporte detallado de los resultados"""
        print("\n" + "="*80)
        print("🎯 REPORTE: PEORES RESULTADOS POR HABILIDAD")
        print("="*80)
        
        if not self.resultados_por_habilidad:
            print("❌ No hay resultados para mostrar")
            return
        
        for habilidad_id, resultado in self.resultados_por_habilidad.items():
            habilidad = resultado['habilidad']
            peores = resultado['peores_resultados']
            total_evals = resultado['total_evaluaciones']
            
            print(f"\n📊 HABILIDAD: {habilidad.habilidad}")
            print("-" * 60)
            print(f"Total de evaluaciones analizadas: {total_evals}")
            print(f"Fitness del mejor individuo: {resultado['mejor_individuo'].fitness:.3f}")
            print(f"Número de peores resultados encontrados: {len(peores)}")
            
            if peores:
                print(f"\n🔻 PEORES RESULTADOS:")
                for i, (evaluacion, calificacion) in enumerate(peores, 1):
                    usuario = self.db_manager.get_usuario_by_id(evaluacion.idUser)
                    reactivo = self.db_manager.get_reactivo_by_id(evaluacion.idReactivo)
                    
                    usuario_nombre = usuario.usuario if usuario else f"ID:{evaluacion.idUser}"
                    reactivo_nombre = reactivo.reactivo if reactivo else f"ID:{evaluacion.idReactivo}"
                    
                    print(f"  {i}. Usuario: {usuario_nombre} | "
                          f"Calificación: {calificacion:.2f} | "
                          f"Reactivo: {reactivo_nombre} | "
                          f"Tiempo: {evaluacion.tiempoRespuesta}s | "
                          f"Fecha: {evaluacion.fechaEvaluacion.strftime('%Y-%m-%d %H:%M')}")
                
                # Estadísticas
                calificaciones = [cal for _, cal in peores]
                print(f"\n📈 ESTADÍSTICAS:")
                print(f"  • Calificación promedio: {np.mean(calificaciones):.2f}")
                print(f"  • Calificación más baja: {min(calificaciones):.2f}")
                print(f"  • Calificación más alta: {max(calificaciones):.2f}")
                print(f"  • Desviación estándar: {np.std(calificaciones):.2f}")
    
    def exportar_resultados_csv(self, filename: str = "peores_resultados.csv"):
        """Exporta los resultados a un archivo CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Habilidad', 'Usuario', 'CURP', 'Calificacion', 'Reactivo', 
                             'TiempoRespuesta', 'FechaEvaluacion', 'Ranking']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for habilidad_id, resultado in self.resultados_por_habilidad.items():
                    habilidad = resultado['habilidad']
                    peores = resultado['peores_resultados']
                    
                    for i, (evaluacion, calificacion) in enumerate(peores, 1):
                        usuario = self.db_manager.get_usuario_by_id(evaluacion.idUser)
                        reactivo = self.db_manager.get_reactivo_by_id(evaluacion.idReactivo)
                        
                        writer.writerow({
                            'Habilidad': habilidad.habilidad,
                            'Usuario': usuario.usuario if usuario else f"ID:{evaluacion.idUser}",
                            'CURP': usuario.curp if usuario else "N/A",
                            'Calificacion': calificacion,
                            'Reactivo': reactivo.reactivo if reactivo else f"ID:{evaluacion.idReactivo}",
                            'TiempoRespuesta': evaluacion.tiempoRespuesta,
                            'FechaEvaluacion': evaluacion.fechaEvaluacion.strftime('%Y-%m-%d %H:%M:%S'),
                            'Ranking': i
                        })
            
            print(f"📁 Resultados exportados a: {filename}")
            
        except Exception as e:
            print(f"❌ Error exportando resultados: {e}")


def main():
    """Función principal para ejecutar el algoritmo genético"""
    print("🧬 ALGORITMO GENÉTICO - BÚSQUEDA DE PEORES RESULTADOS")
    print("="*60)
    print("🔗 Conectando únicamente a MySQL")
    
    # Verificar si existe archivo .env
    if not os.path.exists('.env'):
        print("\n❌ No se encontró archivo .env")
        print("💡 ¿Quieres crear un archivo .env de ejemplo? (s/n): ", end="")
        respuesta = input().strip().lower()
        if respuesta in ['s', 'si', 'y', 'yes']:
            print("\n🛑 Configura el archivo .env y ejecuta el programa nuevamente")
            return
        else:
            print("❌ Se requiere archivo .env para la configuración")
            return
    
    db_manager = None
    try:
        # Inicializar el gestor de MySQL
        db_manager = MySQLManager()
        
        # Probar conexión y estructura
        if not db_manager.test_conexion():
            print("❌ Falló la verificación de la base de datos")
            return
        
        # Verificar integridad de datos
        db_manager.verificar_integridad_datos()
        
        # Configurar y ejecutar el algoritmo genético
        print("\n🧬 Configurando algoritmo genético...")
        ag = AlgoritmoGenetico(
            db_manager=db_manager,
            poblacion_size=40,
            generaciones=80,
            tasa_mutacion=0.15,
            tasa_cruzamiento=0.8
        )
        
        print("🚀 Ejecutando algoritmo genético...")
        ag.ejecutar_para_todas_las_habilidades()
        
        # Generar reporte final
        ag.generar_reporte()
        
        # Exportar resultados
        print("\n💾 ¿Quieres exportar los resultados a CSV? (s/n): ", end="")
        respuesta = input().strip().lower()
        if respuesta in ['s', 'si', 'y', 'yes']:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"peores_resultados_{timestamp}.csv"
            ag.exportar_resultados_csv(filename)
        
        print("\n✅ Análisis completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")
        print("💡 Verifica:")
        print("   • Que el archivo .env esté configurado correctamente")
        print("   • Que MySQL esté ejecutándose")
        print("   • Que la base de datos y tablas existan")
        
    finally:
        if db_manager:
            try:
                db_manager.close()
            except Exception as e:
                print(f"⚠️ Error cerrando conexión: {e}")

if __name__ == "__main__":
    main()