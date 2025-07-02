from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Tuple, Optional, Any
import random
import numpy as np
from dataclasses import dataclass
import logging
import time
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando Sistema de Recomendación")
    yield
    logger.info("🛑 Cerrando Sistema de Recomendación")

app = FastAPI(
    title="Sistema de Recomendación con Algoritmo Genético",
    description="API para recomendación inteligente de ejercicios usando algoritmos genéticos",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos mejorados
class Debilidades(BaseModel):
    lectura: float = Field(..., ge=0.0, le=1.0, description="Nivel de debilidad en lectura (0-1)")
    escritura: float = Field(..., ge=0.0, le=1.0, description="Nivel de debilidad en escritura (0-1)")
    memoria: float = Field(..., ge=0.0, le=1.0, description="Nivel de debilidad en memoria (0-1)")
    
    @field_validator('lectura', 'escritura', 'memoria')
    @classmethod
    def validar_rango(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Los valores deben estar entre 0.0 y 1.0')
        return round(v, 3)

class Reactivo(BaseModel):
    id_reactivo: int = Field(..., gt=0, description="ID único del reactivo")
    lectura: float = Field(..., ge=0.0, le=1.0, description="Impacto en lectura")
    escritura: float = Field(..., ge=0.0, le=1.0, description="Impacto en escritura")
    memoria: float = Field(..., ge=0.0, le=1.0, description="Impacto en memoria")
    nombre: Optional[str] = Field(None, description="Nombre descriptivo del reactivo")
    dificultad: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Nivel de dificultad")

class ParametrosAG(BaseModel):
    poblacion_size: int = Field(50, ge=10, le=200, description="Tamaño de la población")
    generaciones: int = Field(100, ge=10, le=500, description="Número de generaciones")
    num_ejercicios: int = Field(5, ge=1, le=20, description="Número de ejercicios a recomendar")
    prob_mutacion: float = Field(0.1, ge=0.0, le=1.0, description="Probabilidad de mutación")
    elitismo: float = Field(0.1, ge=0.0, le=0.5, description="Porcentaje de elitismo")

class InputData(BaseModel):
    debilidades: Debilidades
    reactivos: List[Reactivo] = Field(..., min_length=1, description="Lista de reactivos disponibles")
    parametros: Optional[ParametrosAG] = Field(default_factory=ParametrosAG)
    
    @field_validator('reactivos')
    @classmethod
    def validar_ids_unicos(cls, v):
        ids = [r.id_reactivo for r in v]
        if len(ids) != len(set(ids)):
            raise ValueError('Los IDs de reactivos deben ser únicos')
        return v

class EstadisticasRecomendacion(BaseModel):
    tiempo_ejecucion: float
    fitness_inicial: float
    fitness_final: float
    mejora_porcentual: float
    convergencia_generacion: int

class RecomendacionResponse(BaseModel):
    ejercicios_recomendados: List[int]
    fitness_score: float
    generacion: int
    mejora_esperada: Dict[str, float]
    estadisticas: EstadisticasRecomendacion
    analisis: Dict[str, Any]

@dataclass
class Individuo:
    """Representa un individuo en la población del algoritmo genético"""
    ejercicios: List[int]
    fitness: float = 0.0

class AlgoritmoGeneticoMejorado:
    def __init__(self, debilidades: Dict[str, float], reactivos: List[Dict], 
                 parametros: ParametrosAG):
        self.debilidades = debilidades
        self.reactivos = {r['id_reactivo']: r for r in reactivos}
        self.parametros = parametros
        self.habilidades = ['lectura', 'escritura', 'memoria']
        self.historial_fitness = []
        self.mejor_fitness_inicial = 0.0
        self.generacion_convergencia = 0
        
    def crear_individuo_aleatorio(self) -> Individuo:
        """Crea un individuo aleatorio con estrategias mejoradas"""
        # Estrategia 1: Completamente aleatorio (40%)
        # Estrategia 2: Sesgado hacia ejercicios que abordan debilidades altas (60%)
        
        num_ejercicios = min(self.parametros.num_ejercicios, len(self.reactivos))
        
        if random.random() < 0.4:
            # Selección completamente aleatoria
            ejercicios = random.sample(list(self.reactivos.keys()), num_ejercicios)
        else:
            # Selección sesgada hacia debilidades
            ejercicios = self._seleccion_sesgada(num_ejercicios)
            
        return Individuo(ejercicios=ejercicios)
    
    def _seleccion_sesgada(self, num_ejercicios: int) -> List[int]:
        """Selecciona ejercicios con sesgo hacia las debilidades más altas"""
        pesos = []
        ids_reactivos = list(self.reactivos.keys())
        
        for id_reactivo in ids_reactivos:
            reactivo = self.reactivos[id_reactivo]
            peso = 0
            for habilidad in self.habilidades:
                peso += self.debilidades[habilidad] * reactivo[habilidad]
            pesos.append(peso + 0.1)  # Evitar peso 0
        
        # Selección ponderada sin reemplazo
        seleccionados = []
        ids_disponibles = ids_reactivos.copy()
        pesos_disponibles = pesos.copy()
        
        for _ in range(min(num_ejercicios, len(ids_disponibles))):
            # Normalizar pesos
            suma_pesos = sum(pesos_disponibles)
            probabilidades = [p/suma_pesos for p in pesos_disponibles]
            
            # Seleccionar basado en probabilidades
            seleccionado = np.random.choice(ids_disponibles, p=probabilidades)
            idx = ids_disponibles.index(seleccionado)
            
            seleccionados.append(seleccionado)
            ids_disponibles.pop(idx)
            pesos_disponibles.pop(idx)
            
        return seleccionados
    
    def calcular_fitness(self, individuo: Individuo) -> float:
        """Función de fitness mejorada con múltiples criterios"""
        if not individuo.ejercicios:
            return 0.0
        
        # 1. Fitness por mejora en debilidades (peso: 70%)
        fitness_debilidades = self._fitness_debilidades(individuo)
        
        # 2. Fitness por diversidad (peso: 20%)
        fitness_diversidad = self._fitness_diversidad(individuo)
        
        # 3. Fitness por dificultad balanceada (peso: 10%)
        fitness_dificultad = self._fitness_dificultad(individuo)
        
        fitness_total = (0.7 * fitness_debilidades + 
                        0.2 * fitness_diversidad + 
                        0.1 * fitness_dificultad)
        
        return fitness_total
    
    def _fitness_debilidades(self, individuo: Individuo) -> float:
        """Calcula fitness basado en mejora de debilidades"""
        mejora_total = {'lectura': 0, 'escritura': 0, 'memoria': 0}
        
        for ejercicio_id in individuo.ejercicios:
            if ejercicio_id in self.reactivos:
                reactivo = self.reactivos[ejercicio_id]
                for habilidad in self.habilidades:
                    mejora_total[habilidad] += reactivo[habilidad]
        
        # Fitness ponderado por debilidades
        fitness = 0.0
        for habilidad in self.habilidades:
            peso_debilidad = self.debilidades[habilidad]
            mejora_habilidad = mejora_total[habilidad]
            fitness += peso_debilidad * mejora_habilidad
            
        return fitness
    
    def _fitness_diversidad(self, individuo: Individuo) -> float:
        """Promueve diversidad en tipos de ejercicios"""
        if not individuo.ejercicios:
            return 0.0
            
        # Diversidad por habilidades cubiertas
        habilidades_cubiertas = set()
        for ejercicio_id in individuo.ejercicios:
            if ejercicio_id in self.reactivos:
                reactivo = self.reactivos[ejercicio_id]
                for habilidad in self.habilidades:
                    if reactivo[habilidad] > 0.3:  # Umbral para considerar "cubierta"
                        habilidades_cubiertas.add(habilidad)
        
        diversidad_habilidades = len(habilidades_cubiertas) / len(self.habilidades)
        
        # Penalizar duplicados
        ejercicios_unicos = len(set(individuo.ejercicios))
        diversidad_ejercicios = ejercicios_unicos / len(individuo.ejercicios)
        
        return (diversidad_habilidades + diversidad_ejercicios) / 2
    
    def _fitness_dificultad(self, individuo: Individuo) -> float:
        """Busca un balance en la dificultad de los ejercicios"""
        if not individuo.ejercicios:
            return 0.0
            
        dificultades = []
        for ejercicio_id in individuo.ejercicios:
            if ejercicio_id in self.reactivos:
                dificultad = self.reactivos[ejercicio_id].get('dificultad', 0.5)
                dificultades.append(dificultad)
        
        if not dificultades:
            return 0.0
            
        # Buscar balance (preferir variedad de dificultades)
        dificultad_media = np.mean(dificultades)
        desviacion = np.std(dificultades) if len(dificultades) > 1 else 0
        
        # Fitness alto para dificultad media balanceada con algo de variación
        fitness_medio = 1 - abs(dificultad_media - 0.5) * 2
        fitness_variacion = min(desviacion * 2, 1.0)  # Limitar a 1.0
        
        return (fitness_medio + fitness_variacion) / 2
    
    def seleccion_torneo_mejorada(self, poblacion: List[Individuo], k: int = 3) -> Individuo:
        """Selección por torneo con presión de selección adaptiva"""
        # Ajustar k basado en la diversidad de la población
        fitness_values = [ind.fitness for ind in poblacion]
        diversidad = np.std(fitness_values) if len(fitness_values) > 1 else 1.0
        
        # Mayor presión de selección cuando hay poca diversidad
        k_adaptivo = max(2, int(k * (1 + diversidad)))
        k_adaptivo = min(k_adaptivo, len(poblacion))
        
        torneos = random.sample(poblacion, k_adaptivo)
        return max(torneos, key=lambda x: x.fitness)
    
    def cruzamiento_uniforme(self, padre1: Individuo, padre2: Individuo) -> Tuple[Individuo, Individuo]:
        """Cruzamiento uniforme mejorado"""
        if not padre1.ejercicios or not padre2.ejercicios:
            return padre1, padre2
        
        # Crear pools de ejercicios únicos
        ejercicios_padre1 = set(padre1.ejercicios)
        ejercicios_padre2 = set(padre2.ejercicios)
        ejercicios_comunes = ejercicios_padre1.intersection(ejercicios_padre2)
        ejercicios_unicos1 = ejercicios_padre1 - ejercicios_comunes
        ejercicios_unicos2 = ejercicios_padre2 - ejercicios_comunes
        
        # Crear hijos
        hijo1_ejercicios = list(ejercicios_comunes)
        hijo2_ejercicios = list(ejercicios_comunes)
        
        # Intercambiar ejercicios únicos aleatoriamente
        ejercicios_intercambio = list(ejercicios_unicos1.union(ejercicios_unicos2))
        random.shuffle(ejercicios_intercambio)
        
        medio = len(ejercicios_intercambio) // 2
        hijo1_ejercicios.extend(ejercicios_intercambio[:medio])
        hijo2_ejercicios.extend(ejercicios_intercambio[medio:])
        
        # Ajustar longitud
        max_ejercicios = self.parametros.num_ejercicios
        hijo1_ejercicios = hijo1_ejercicios[:max_ejercicios]
        hijo2_ejercicios = hijo2_ejercicios[:max_ejercicios]
        
        return Individuo(ejercicios=hijo1_ejercicios), Individuo(ejercicios=hijo2_ejercicios)
    
    def mutacion_inteligente(self, individuo: Individuo):
        """Mutación inteligente basada en debilidades"""
        if random.random() >= self.parametros.prob_mutacion or not individuo.ejercicios:
            return
        
        # Decidir tipo de mutación
        tipo_mutacion = random.choice(['sustituir', 'agregar', 'eliminar'])
        
        if tipo_mutacion == 'sustituir' and individuo.ejercicios:
            # Sustituir ejercicio menos útil por uno más útil
            fitness_ejercicios = []
            for ejercicio_id in individuo.ejercicios:
                # Crear individuo temporal con solo este ejercicio
                temp_individuo = Individuo(ejercicios=[ejercicio_id])
                fitness_individual = self._fitness_debilidades(temp_individuo)
                fitness_ejercicios.append((ejercicio_id, fitness_individual))
            
            # Encontrar el ejercicio menos útil
            ejercicio_menos_util = min(fitness_ejercicios, key=lambda x: x[1])[0]
            
            # Reemplazar con ejercicio sesgado hacia debilidades
            nuevos_ejercicios = self._seleccion_sesgada(1)
            if nuevos_ejercicios and nuevos_ejercicios[0] not in individuo.ejercicios:
                idx = individuo.ejercicios.index(ejercicio_menos_util)
                individuo.ejercicios[idx] = nuevos_ejercicios[0]
        
        elif tipo_mutacion == 'agregar' and len(individuo.ejercicios) < self.parametros.num_ejercicios:
            # Agregar ejercicio útil
            ejercicios_disponibles = [id_r for id_r in self.reactivos.keys() 
                                    if id_r not in individuo.ejercicios]
            if ejercicios_disponibles:
                # Seleccionar con sesgo hacia debilidades
                nuevo_ejercicio = self._seleccion_sesgada_desde_lista(ejercicios_disponibles, 1)
                if nuevo_ejercicio:
                    individuo.ejercicios.extend(nuevo_ejercicio)
        
        elif tipo_mutacion == 'eliminar' and len(individuo.ejercicios) > 1:
            # Eliminar ejercicio menos útil
            ejercicio_eliminar = random.choice(individuo.ejercicios)
            individuo.ejercicios.remove(ejercicio_eliminar)
    
    def _seleccion_sesgada_desde_lista(self, ejercicios_disponibles: List[int], cantidad: int) -> List[int]:
        """Selecciona ejercicios de una lista con sesgo hacia debilidades"""
        if not ejercicios_disponibles:
            return []
            
        pesos = []
        for id_reactivo in ejercicios_disponibles:
            reactivo = self.reactivos[id_reactivo]
            peso = sum(self.debilidades[habilidad] * reactivo[habilidad] 
                      for habilidad in self.habilidades)
            pesos.append(peso + 0.1)
        
        suma_pesos = sum(pesos)
        if suma_pesos == 0:
            return random.sample(ejercicios_disponibles, min(cantidad, len(ejercicios_disponibles)))
            
        probabilidades = [p/suma_pesos for p in pesos]
        
        try:
            seleccionados = np.random.choice(
                ejercicios_disponibles, 
                size=min(cantidad, len(ejercicios_disponibles)), 
                replace=False, 
                p=probabilidades
            )
            return seleccionados.tolist()
        except:
            return random.sample(ejercicios_disponibles, min(cantidad, len(ejercicios_disponibles)))
    
    def evolucionar(self) -> Tuple[Individuo, int, EstadisticasRecomendacion]:
        """Ejecuta el algoritmo genético mejorado"""
        inicio_tiempo = time.time()
        
        # Crear población inicial
        poblacion = [self.crear_individuo_aleatorio() for _ in range(self.parametros.poblacion_size)]
        
        # Evaluar fitness inicial
        for individuo in poblacion:
            individuo.fitness = self.calcular_fitness(individuo)
        
        mejor_individuo = max(poblacion, key=lambda x: x.fitness)
        self.mejor_fitness_inicial = mejor_individuo.fitness
        self.historial_fitness.append(mejor_individuo.fitness)
        
        generaciones_sin_mejora = 0
        criterio_convergencia = 10  # Parar si no hay mejora en 10 generaciones
        
        for generacion in range(self.parametros.generaciones):
            nueva_poblacion = []
            
            # Elitismo: mantener los mejores individuos
            num_elite = max(1, int(self.parametros.elitismo * self.parametros.poblacion_size))
            elite = sorted(poblacion, key=lambda x: x.fitness, reverse=True)[:num_elite]
            nueva_poblacion.extend(elite)
            
            # Generar nueva población
            while len(nueva_poblacion) < self.parametros.poblacion_size:
                padre1 = self.seleccion_torneo_mejorada(poblacion)
                padre2 = self.seleccion_torneo_mejorada(poblacion)
                
                hijo1, hijo2 = self.cruzamiento_uniforme(padre1, padre2)
                
                self.mutacion_inteligente(hijo1)
                self.mutacion_inteligente(hijo2)
                
                nueva_poblacion.extend([hijo1, hijo2])
            
            # Ajustar tamaño de población
            nueva_poblacion = nueva_poblacion[:self.parametros.poblacion_size]
            
            # Evaluar fitness
            for individuo in nueva_poblacion:
                individuo.fitness = self.calcular_fitness(individuo)
                individuo.edad += 1
            
            poblacion = nueva_poblacion
            mejor_actual = max(poblacion, key=lambda x: x.fitness)
            
            # Verificar mejora
            if mejor_actual.fitness > mejor_individuo.fitness:
                mejor_individuo = mejor_actual
                generaciones_sin_mejora = 0
                self.generacion_convergencia = generacion + 1
            else:
                generaciones_sin_mejora += 1
            
            self.historial_fitness.append(mejor_individuo.fitness)
            
            # Criterio de parada temprana
            if generaciones_sin_mejora >= criterio_convergencia:
                logger.info(f"Convergencia alcanzada en generación {generacion + 1}")
                break
        
        tiempo_ejecucion = time.time() - inicio_tiempo
        
        # Crear estadísticas
        fitness_final = mejor_individuo.fitness
        mejora_porcentual = ((fitness_final - self.mejor_fitness_inicial) / 
                           max(self.mejor_fitness_inicial, 0.001)) * 100
        
        estadisticas = EstadisticasRecomendacion(
            tiempo_ejecucion=round(tiempo_ejecucion, 3),
            fitness_inicial=round(self.mejor_fitness_inicial, 4),
            fitness_final=round(fitness_final, 4),
            mejora_porcentual=round(mejora_porcentual, 2),
            convergencia_generacion=self.generacion_convergencia
        )
        
        return mejor_individuo, generacion + 1, estadisticas
    
    def calcular_mejora_esperada(self, ejercicios: List[int]) -> Dict[str, float]:
        """Calcula la mejora esperada en cada habilidad"""
        mejora = {'lectura': 0, 'escritura': 0, 'memoria': 0}
        
        for ejercicio_id in ejercicios:
            if ejercicio_id in self.reactivos:
                reactivo = self.reactivos[ejercicio_id]
                for habilidad in self.habilidades:
                    mejora[habilidad] += reactivo[habilidad]
        
        return {k: round(v, 3) for k, v in mejora.items()}
    
    def generar_analisis(self, mejor_solucion: Individuo) -> Dict[str, Any]:
        """Genera análisis detallado de la recomendación"""
        ejercicios_info = []
        for ejercicio_id in mejor_solucion.ejercicios:
            if ejercicio_id in self.reactivos:
                reactivo = self.reactivos[ejercicio_id]
                info = {
                    'id': ejercicio_id,
                    'nombre': reactivo.get('nombre', f'Ejercicio {ejercicio_id}'),
                    'impacto': {
                        'lectura': reactivo['lectura'],
                        'escritura': reactivo['escritura'],
                        'memoria': reactivo['memoria']
                    },
                    'dificultad': reactivo.get('dificultad', 0.5)
                }
                ejercicios_info.append(info)
        
        # Calcular balance de habilidades
        mejora_total = self.calcular_mejora_esperada(mejor_solucion.ejercicios)
        balance_habilidades = {
            habilidad: {
                'debilidad': self.debilidades[habilidad],
                'mejora': mejora_total[habilidad],
                'ratio_mejora': round(mejora_total[habilidad] / max(self.debilidades[habilidad], 0.001), 2)
            }
            for habilidad in self.habilidades
        }
        
        return {
            'ejercicios_detalle': ejercicios_info,
            'balance_habilidades': balance_habilidades,
            'cobertura_debilidades': self._calcular_cobertura_debilidades(mejor_solucion.ejercicios),
            'historial_fitness': self.historial_fitness[-10:],  # Últimas 10 generaciones
            'recomendaciones_adicionales': self._generar_recomendaciones_adicionales(mejor_solucion.ejercicios)
        }
    
    def _calcular_cobertura_debilidades(self, ejercicios: List[int]) -> Dict[str, float]:
        """Calcula qué tan bien se cubren las debilidades"""
        cobertura = {}
        mejora_total = self.calcular_mejora_esperada(ejercicios)
        
        for habilidad in self.habilidades:
            # Cobertura = mejora / debilidad (normalizada)
            debilidad = self.debilidades[habilidad]
            mejora = mejora_total[habilidad]
            
            if debilidad > 0:
                cobertura[habilidad] = min(mejora / debilidad, 1.0)
            else:
                cobertura[habilidad] = 1.0 if mejora > 0 else 0.0
                
        return {k: round(v, 3) for k, v in cobertura.items()}
    
    def _generar_recomendaciones_adicionales(self, ejercicios_actuales: List[int]) -> List[str]:
        """Genera recomendaciones adicionales para el usuario"""
        recomendaciones = []
        
        # Analizar balance de dificultad
        dificultades = []
        for ejercicio_id in ejercicios_actuales:
            if ejercicio_id in self.reactivos:
                dificultad = self.reactivos[ejercicio_id].get('dificultad', 0.5)
                dificultades.append(dificultad)
        
        if dificultades:
            dificultad_promedio = np.mean(dificultades)
            if dificultad_promedio < 0.3:
                recomendaciones.append("Considera agregar ejercicios de mayor dificultad para un mejor desafío")
            elif dificultad_promedio > 0.7:
                recomendaciones.append("Los ejercicios son bastante desafiantes, asegúrate de dominar los conceptos básicos")
        
        # Analizar cobertura de habilidades
        mejora_total = self.calcular_mejora_esperada(ejercicios_actuales)
        habilidad_menos_cubierta = min(mejora_total.items(), key=lambda x: x[1])
        
        if habilidad_menos_cubierta[1] < max(mejora_total.values()) * 0.7:
            recomendaciones.append(f"Considera ejercicios adicionales para fortalecer {habilidad_menos_cubierta[0]}")
        
        # Recomendación de frecuencia
        num_ejercicios = len(ejercicios_actuales)
        if num_ejercicios <= 3:
            recomendaciones.append("Programa sesiones de práctica diarias de 15-20 minutos")
        else:
            recomendaciones.append("Divide los ejercicios en sesiones de 2-3 ejercicios cada una")
        
        return recomendaciones

# Endpoints de la API
@app.post("/recomendar", response_model=RecomendacionResponse)
async def recomendar_ejercicios(data: InputData):
    """
    Endpoint principal que recibe las debilidades y reactivos,
    y retorna recomendaciones usando algoritmo genético mejorado
    """
    try:
        logger.info(f"Procesando recomendación para {len(data.reactivos)} reactivos")
        
        # Convertir datos
        debilidades_dict = data.debilidades.model_dump()
        reactivos_list = [reactivo.model_dump() for reactivo in data.reactivos]
        
        # Validaciones adicionales
        if not reactivos_list:
            raise HTTPException(status_code=400, detail="No se proporcionaron reactivos")
        
        if data.parametros.num_ejercicios > len(reactivos_list):
            data.parametros.num_ejercicios = len(reactivos_list)
            logger.warning(f"Ajustando número de ejercicios a {len(reactivos_list)}")
        
        # Crear y ejecutar algoritmo genético
        ag = AlgoritmoGeneticoMejorado(
            debilidades=debilidades_dict,
            reactivos=reactivos_list,
            parametros=data.parametros
        )
        
        mejor_solucion, generaciones_ejecutadas, estadisticas = ag.evolucionar()
        mejora_esperada = ag.calcular_mejora_esperada(mejor_solucion.ejercicios)
        analisis = ag.generar_analisis(mejor_solucion)
        
        logger.info(f"Recomendación completada en {estadisticas.tiempo_ejecucion}s")
        
        return RecomendacionResponse(
            ejercicios_recomendados=mejor_solucion.ejercicios,
            fitness_score=round(mejor_solucion.fitness, 4),
            generacion=generaciones_ejecutadas,
            mejora_esperada=mejora_esperada,
            estadisticas=estadisticas,
            analisis=analisis
        )
        
    except Exception as e:
        logger.error(f"Error en recomendación: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el algoritmo genético: {str(e)}")

@app.get("/health")
async def health_check():
    """Endpoint de salud"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    return {
        "mensaje": "Sistema de Recomendación con Algoritmo Genético v2.0",
        "version": "2.0.0",
        "mejoras": [
            "Algoritmo genético optimizado",
            "Múltiples criterios de fitness",
            "Análisis detallado de recomendaciones",
            "Validaciones mejoradas",
            "Estadísticas de rendimiento",
            "Convergencia adaptiva",
            "Mutación inteligente"
        ],
        "endpoints": {
            "recomendar": "POST /recomendar - Obtener recomendaciones de ejercicios",
            "health": "GET /health - Estado del sistema",
            "ejemplo": "GET /ejemplo - Ejemplo de uso",
            "docs": "GET /docs - Documentación interactiva"
        }
    }

@app.get("/ejemplo")
async def ejemplo_uso():
    """Retorna un ejemplo de uso del API mejorado"""
    return {
        "ejemplo_basico": {
            "debilidades": {
                "lectura": 0.4,
                "escritura": 0.6,
                "memoria": 0.5
            },
            "reactivos": [
                {
                    "id_reactivo": 1,
                    "lectura": 0.2,
                    "escritura": 0.3,
                    "memoria": 0.5,
                    "nombre": "Comprensión lectora básica",
                    "dificultad": 0.3
                },
                {
                    "id_reactivo": 2,
                    "lectura": 0.3,
                    "escritura": 0.4,
                    "memoria": 0.3,
                    "nombre": "Redacción estructurada",
                    "dificultad": 0.5
                },
                {
                    "id_reactivo": 3,
                    "lectura": 0.5,
                    "escritura": 0.2,
                    "memoria": 0.4,
                    "nombre": "Análisis de textos",
                    "dificultad": 0.7
                }
            ]
        },
        "ejemplo_con_parametros": {
            "debilidades": {
                "lectura": 0.8,
                "escritura": 0.3,
                "memoria": 0.6
            },
            "reactivos": "...",
            "parametros": {
                "poblacion_size": 80,
                "generaciones": 150,
                "num_ejercicios": 4,
                "prob_mutacion": 0.15,
                "elitismo": 0.2
            }
        },
        "uso_curl": """
curl -X POST 'http://localhost:8000/recomendar' \\
-H 'Content-Type: application/json' \\
-d '{
    "debilidades": {"lectura": 0.4, "escritura": 0.6, "memoria": 0.5},
    "reactivos": [{"id_reactivo": 1, "lectura": 0.2, "escritura": 0.3, "memoria": 0.5}]
}'
        """,
        "respuesta_ejemplo": {
            "ejercicios_recomendados": [2, 4, 1],
            "fitness_score": 1.8543,
            "generacion": 45,
            "mejora_esperada": {
                "lectura": 0.9,
                "escritura": 1.2,
                "memoria": 1.4
            },
            "estadisticas": {
                "tiempo_ejecucion": 0.234,
                "fitness_inicial": 1.2,
                "fitness_final": 1.8543,
                "mejora_porcentual": 54.53,
                "convergencia_generacion": 45
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    
    # Configuración para ejecutables
    if getattr(sys, 'frozen', False):
        # Ejecutándose como ejecutable
        uvicorn.run(
            app,  # Usar objeto app directamente en ejecutables
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
    else:
        # Ejecutándose como script normal
        uvicorn.run(
            "main:app",  # Usar string import para desarrollo
            host="0.0.0.0", 
            port=8000,
            log_level="info",
            reload=True
        )