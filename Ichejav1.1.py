import random
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import mysql.connector
import pyodbc
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
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

class DatabaseManager:
    """Gestor de conexión a base de datos real"""
    
    def __init__(self, db_type: str = "mysql", **kwargs):
        """
        Inicializa la conexión a la base de datos
        
        Parámetros:
        db_type: 'mysql', 'sqlite', 'sqlserver', 'postgresql'
        **kwargs: Parámetros de conexión específicos del tipo de BD
        """
        self.db_type = db_type.lower()
        self.connection = None
        self.connect(**kwargs)
    
    def connect(self, **kwargs):
        """Establece la conexión según el tipo de base de datos"""
        try:
            if self.db_type == "mysql":
                self.connection = mysql.connector.connect(
                    host=kwargs.get('host', os.getenv('DB_HOST', 'localhost')),
                    user=kwargs.get('user', os.getenv('DB_USER')),
                    password=kwargs.get('password', os.getenv('DB_PASSWORD')),
                    database=kwargs.get('database', os.getenv('DB_NAME')),
                    port=kwargs.get('port', int(os.getenv('DB_PORT', 3306)))
                )
                
            elif self.db_type == "sqlite":
                db_path = kwargs.get('database', os.getenv('DB_PATH', 'database.db'))
                self.connection = sqlite3.connect(db_path)
                
            elif self.db_type == "sqlserver":
                server = kwargs.get('server', os.getenv('DB_SERVER'))
                database = kwargs.get('database', os.getenv('DB_NAME'))
                username = kwargs.get('username', os.getenv('DB_USER'))
                password = kwargs.get('password', os.getenv('DB_PASSWORD'))
                
                connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
                self.connection = pyodbc.connect(connection_string)
                
            elif self.db_type == "postgresql":
                import psycopg2
                self.connection = psycopg2.connect(
                    host=kwargs.get('host', os.getenv('DB_HOST', 'localhost')),
                    user=kwargs.get('user', os.getenv('DB_USER')),
                    password=kwargs.get('password', os.getenv('DB_PASSWORD')),
                    database=kwargs.get('database', os.getenv('DB_NAME')),
                    port=kwargs.get('port', int(os.getenv('DB_PORT', 5432)))
                )
            
            print(f"✅ Conexión establecida exitosamente con {self.db_type.upper()}")
            
        except Exception as e:
            print(f"❌ Error al conectar con la base de datos: {e}")
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
        WHERE idHabilidad = ?
        ORDER BY calificacion ASC
        """
        
        # Ajustar el placeholder según el tipo de BD
        if self.db_type in ["mysql", "postgresql"]:
            query = query.replace("?", "%s")
        
        results = self.execute_query(query, (id_habilidad,))
        
        evaluaciones = []
        for row in results:
            # Manejar diferentes formatos de fecha según la BD
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
        query = "SELECT idUser, usuario, curp FROM Usuario WHERE idUser = ?"
        
        if self.db_type in ["mysql", "postgresql"]:
            query = query.replace("?", "%s")
        
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
        query = "SELECT idReactivo, reactivo FROM Reactivo WHERE idReactivo = ?"
        
        if self.db_type in ["mysql", "postgresql"]:
            query = query.replace("?", "%s")
        
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
        
        # Contar usuarios
        result = self.execute_query("SELECT COUNT(*) FROM Usuario")
        stats['total_usuarios'] = result[0][0]
        
        # Contar habilidades
        result = self.execute_query("SELECT COUNT(*) FROM Habilidad")
        stats['total_habilidades'] = result[0][0]
        
        # Contar evaluaciones
        result = self.execute_query("SELECT COUNT(*) FROM Evaluacion")
        stats['total_evaluaciones'] = result[0][0]
        
        # Rango de calificaciones
        result = self.execute_query("SELECT MIN(calificacion), MAX(calificacion), AVG(calificacion) FROM Evaluacion")
        if result[0][0] is not None:
            stats['calificacion_minima'] = float(result[0][0])
            stats['calificacion_maxima'] = float(result[0][1])
            stats['calificacion_promedio'] = float(result[0][2])
        
        return stats
    
    def test_conexion(self) -> bool:
        """Prueba la conexión y estructura de la base de datos"""
        try:
            print("🔍 Probando conexión y estructura de la base de datos...")
            
            # Verificar tablas principales
            tablas_requeridas = ['Usuario', 'Habilidad', 'Reactivo', 'Evaluacion']
            
            for tabla in tablas_requeridas:
                try:
                    if self.db_type == "sqlite":
                        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}'"
                    if self.db_type == "mysql":
                        query = f"SHOW TABLES LIKE '{tabla}'"
                    elif self.db_type == "sqlserver":
                        query = f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{tabla}'"
                    elif self.db_type == "postgresql":
                        query = f"SELECT tablename FROM pg_tables WHERE tablename = '{tabla.lower()}'"
                    
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
                print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en test de conexión: {e}")
            return False
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
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
        # Cada gen representa el índice de una evaluación
        # Seleccionamos aleatoriamente algunas evaluaciones
        num_genes = min(5, len(self.evaluaciones))  # Máximo 5 peores resultados
        return random.sample(range(len(self.evaluaciones)), num_genes)
    
    def calcular_fitness(self):
        """Calcula el fitness basado en qué tan malos son los resultados seleccionados"""
        if not self.genes:
            self.fitness = float('inf')
            return
        
        calificaciones_seleccionadas = [self.evaluaciones[i].calificacion for i in self.genes]
        
        # Fitness es la suma inversa de las calificaciones (queremos los peores)
        # También consideramos la diversidad de usuarios
        usuarios_seleccionados = set(self.evaluaciones[i].idUser for i in self.genes)
        
        # Penalizar si hay muchos resultados del mismo usuario
        penalty_diversidad = len(self.genes) - len(usuarios_seleccionados)
        
        # Fitness: promedio bajo de calificaciones + bonificación por diversidad
        promedio_calificaciones = sum(calificaciones_seleccionadas) / len(calificaciones_seleccionadas)
        self.fitness = promedio_calificaciones + (penalty_diversidad * 0.5)
        
        # Guardar los peores resultados para reporte
        self.peores_resultados = [(self.evaluaciones[i], self.evaluaciones[i].calificacion) 
                                 for i in self.genes]
        self.peores_resultados.sort(key=lambda x: x[1])  # Ordenar por calificación

class AlgoritmoGenetico:
    """Algoritmo genético para encontrar los peores resultados por habilidad"""
    
    def __init__(self, db_manager: DatabaseManager, poblacion_size=50, 
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
        
        for habilidad in habilidades:
            print(f"\n🔍 Analizando habilidad: {habilidad.habilidad}")
            evaluaciones = self.db_manager.get_evaluaciones_por_habilidad(habilidad.idHabilidad)
            
            if not evaluaciones:
                print(f"No hay evaluaciones para la habilidad {habilidad.habilidad}")
                continue
            
            mejor_individuo = self._ejecutar_algoritmo_genetico(evaluaciones, habilidad.idHabilidad)
            self.resultados_por_habilidad[habilidad.idHabilidad] = {
                'habilidad': habilidad,
                'mejor_individuo': mejor_individuo,
                'peores_resultados': mejor_individuo.peores_resultados
            }
    
    def _ejecutar_algoritmo_genetico(self, evaluaciones: List[Evaluacion], habilidad_id: int):
        """Ejecuta el algoritmo genético para una habilidad específica"""
        
        # Inicializar población
        poblacion = [PeorResultadoIndividuo(evaluaciones, habilidad_id) 
                    for _ in range(self.poblacion_size)]
        
        # Evaluar fitness inicial
        for individuo in poblacion:
            individuo.calcular_fitness()
        
        mejor_fitness_historico = float('inf')
        mejor_individuo = None
        
        for generacion in range(self.generaciones):
            # Selección por torneo
            nueva_poblacion = []
            
            while len(nueva_poblacion) < self.poblacion_size:
                # Seleccionar padres
                padre1 = self._seleccion_torneo(poblacion)
                padre2 = self._seleccion_torneo(poblacion)
                
                # Cruzamiento
                if random.random() < self.tasa_cruzamiento:
                    hijo1, hijo2 = self._cruzamiento(padre1, padre2, evaluaciones, habilidad_id)
                else:
                    hijo1, hijo2 = padre1, padre2
                
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
            
            # Mostrar progreso cada 20 generaciones
            if generacion % 20 == 0:
                print(f"  Generación {generacion}: Mejor fitness = {mejor_fitness_historico:.3f}")
        
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
            hijo1.genes = list(set(g for g in hijo1.genes if g < len(evaluaciones)))[:5]
            hijo2.genes = list(set(g for g in hijo2.genes if g < len(evaluaciones)))[:5]
        
        return hijo1, hijo2
    
    def _mutar(self, individuo: PeorResultadoIndividuo, evaluaciones: List[Evaluacion]):
        """Mutación: cambiar aleatoriamente algunos genes"""
        if not individuo.genes:
            return
        
        for i in range(len(individuo.genes)):
            if random.random() < 0.3:  # 30% de probabilidad de mutar cada gen
                individuo.genes[i] = random.randint(0, len(evaluaciones) - 1)
        
        # Eliminar duplicados
        individuo.genes = list(set(individuo.genes))
    
    def generar_reporte(self):
        """Genera un reporte detallado de los resultados"""
        print("\n" + "="*80)
        print("🎯 REPORTE: PEORES RESULTADOS POR HABILIDAD")
        print("="*80)
        
        for habilidad_id, resultado in self.resultados_por_habilidad.items():
            habilidad = resultado['habilidad']
            peores = resultado['peores_resultados']
            
            print(f"\n📊 HABILIDAD: {habilidad.habilidad}")
            print("-" * 50)
            print(f"Fitness del mejor individuo: {resultado['mejor_individuo'].fitness:.3f}")
            print(f"Número de peores resultados encontrados: {len(peores)}")
            
            print("\n🔻 PEORES RESULTADOS:")
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
            
            if peores:
                calificaciones = [cal for _, cal in peores]
                print(f"\n📈 ESTADÍSTICAS:")
                print(f"  • Calificación promedio: {np.mean(calificaciones):.2f}")
                print(f"  • Calificación más baja: {min(calificaciones):.2f}")
                print(f"  • Calificación más alta: {max(calificaciones):.2f}")
                print(f"  • Desviación estándar: {np.std(calificaciones):.2f}")
    
    def exportar_resultados_csv(self, filename: str = "peores_resultados.csv"):
        """Exporta los resultados a un archivo CSV"""
        import csv
        
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

def configurar_base_datos():
    """Función para configurar la conexión a la base de datos"""
    print("🔧 CONFIGURACIÓN DE BASE DE DATOS")
    print("="*40)
    
    # Opción 1: Usar variables de entorno (.env)
    print("\n📝 Opciones de configuración:")
    print("1. Usar archivo .env (recomendado)")
    print("2. Configuración manual")
    print("3. Usar base de datos de prueba (SQLite)")
    
    opcion = input("\nSelecciona una opción (1-3): ").strip()
    
    if opcion == "1":
        print("\n📄 Crea un archivo .env en el directorio del proyecto con:")
        print("""
# Para MySQL
DB_TYPE=mysql
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=tu_base_datos
DB_PORT=3306

# Para SQL Server
DB_TYPE=sqlserver
DB_SERVER=localhost
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_password

# Para PostgreSQL
DB_TYPE=postgresql
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=tu_base_datos
DB_PORT=5432

# Para SQLite
DB_TYPE=sqlite
DB_PATH=ruta/a/tu/database.db
        """)
        
        db_type = os.getenv('DB_TYPE', 'mysql')
        return DatabaseManager(db_type)
    
    elif opcion == "2":
        print("\n🔧 Configuración manual:")
        db_type = input("Tipo de BD (mysql/sqlserver/postgresql/sqlite): ").strip().lower()
        
        if db_type == "mysql":
            host = input("Host (localhost): ") or "localhost"
            user = input("Usuario: ")
            password = input("Contraseña: ")
            database = input("Nombre de la BD: ")
            port = int(input("Puerto (3306): ") or "3306")
            
            return DatabaseManager(db_type, host=host, user=user, 
                                 password=password, database=database, port=port)
        
        elif db_type == "sqlite":
            database = input("Ruta del archivo SQLite: ")
            return DatabaseManager(db_type, database=database)
        
        # Agregar más tipos según necesidad
        
    elif opcion == "3":
        print("📝 Creando base de datos de prueba...")
        return crear_base_datos_prueba()
    
    else:
        print("❌ Opción inválida")
        return configurar_base_datos()

def crear_base_datos_prueba():
    """Crea una base de datos SQLite de prueba con datos simulados"""
    db_path = "test_database.db"
    
    # Eliminar BD anterior si existe
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tablas
    cursor.execute("""
    CREATE TABLE Usuario (
        idUser INTEGER PRIMARY KEY,
        usuario VARCHAR(40),
        curp VARCHAR(20)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE Habilidad (
        idHabilidad INTEGER PRIMARY KEY,
        habilidad VARCHAR(50)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE Reactivo (
        idReactivo INTEGER PRIMARY KEY,
        reactivo VARCHAR(30)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE Evaluacion (
        idEvaluacion INTEGER PRIMARY KEY,
        idUser INTEGER,
        idHabilidad INTEGER,
        idReactivo INTEGER,
        calificacion DECIMAL(5,2),
        fechaEvaluacion DATETIME,
        tiempoRespuesta INTEGER,
        FOREIGN KEY (idUser) REFERENCES Usuario(idUser),
        FOREIGN KEY (idHabilidad) REFERENCES Habilidad(idHabilidad),
        FOREIGN KEY (idReactivo) REFERENCES Reactivo(idReactivo)
    )
    """)
    
    # Insertar datos de prueba
    # Usuarios
    for i in range(1, 21):
        cursor.execute("INSERT INTO Usuario VALUES (?, ?, ?)", 
                      (i, f"usuario{i}", f"CURP{i:03d}"))
    
    # Habilidades
    habilidades = ["Matemáticas", "Comprensión Lectora", "Lógica", "Ciencias", "Historia"]
    for i, hab in enumerate(habilidades, 1):
        cursor.execute("INSERT INTO Habilidad VALUES (?, ?)", (i, hab))
    
    # Reactivos
    for i in range(1, 51):
        cursor.execute("INSERT INTO Reactivo VALUES (?, ?)", (i, f"Reactivo {i}"))
    
    # Evaluaciones
    eval_id = 1
    for user_id in range(1, 21):
        for hab_id in range(1, 6):
            for _ in range(random.randint(3, 8)):
                reactivo_id = random.randint(1, 50)
                calificacion = round(random.uniform(0, 10), 2)
                tiempo = random.randint(30, 300)
                fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                cursor.execute("""
                INSERT INTO Evaluacion VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (eval_id, user_id, hab_id, reactivo_id, calificacion, fecha, tiempo))
                eval_id += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de datos de prueba creada: {db_path}")
    return DatabaseManager("sqlite", database=db_path)

def main():
    """Función principal para ejecutar el algoritmo genético"""
    print("🧬 ALGORITMO GENÉTICO - BÚSQUEDA DE PEORES RESULTADOS")
    print("="*60)
    
    # Inicializar el gestor de base de datos con datos simulados
    db_manager = DatabaseManager()
    print(f"📁 Base de datos inicializada:")
    print(f"  • Usuarios: {len(db_manager.usuarios)}")
    print(f"  • Habilidades: {len(db_manager.habilidades)}")
    print(f"  • Evaluaciones: {len(db_manager.evaluaciones)}")
    
    # Configurar y ejecutar el algoritmo genético
    ag = AlgoritmoGenetico(
        db_manager=db_manager,
        poblacion_size=30,
        generaciones=50,
        tasa_mutacion=0.15,
        tasa_cruzamiento=0.8
    )
    
    # Ejecutar para todas las habilidades
    ag.ejecutar_para_todas_las_habilidades()
    
    # Generar reporte final
    ag.generar_reporte()
    
    print("\n✅ Análisis completado exitosamente!")

if __name__ == "__main__":
    main()