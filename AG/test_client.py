import requests
import json
import time
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
import asyncio
import aiohttp

# Configuración
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

class TestClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.resultados_pruebas = []

    def test_health(self) -> bool:
        """Prueba el endpoint de salud"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sistema saludable - Versión: {data.get('version', 'N/A')}")
                return True
            else:
                print(f"❌ Sistema no saludable: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ No se pudo conectar al servidor")
            return False

    def test_ejemplo_basico(self) -> Dict:
        """Prueba con el ejemplo básico"""
        test_data = {
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
                },
                {
                    "id_reactivo": 4,
                    "lectura": 0.1,
                    "escritura": 0.8,
                    "memoria": 0.2,
                    "nombre": "Ensayos creativos",
                    "dificultad": 0.6
                },
                {
                    "id_reactivo": 5,
                    "lectura": 0.6,
                    "escritura": 0.1,
                    "memoria": 0.7,
                    "nombre": "Memorización de vocabulario",
                    "dificultad": 0.4
                }
            ]
        }
        
        return self._ejecutar_prueba("Ejemplo Básico", test_data)

    def test_con_parametros_personalizados(self) -> Dict:
        """Prueba con parámetros personalizados del algoritmo genético"""
        test_data = {
            "debilidades": {
                "lectura": 0.8,
                "escritura": 0.3,
                "memoria": 0.9
            },
            "reactivos": [
                {
                    "id_reactivo": i,
                    "lectura": np.random.uniform(0.1, 0.9),
                    "escritura": np.random.uniform(0.1, 0.9),
                    "memoria": np.random.uniform(0.1, 0.9),
                    "nombre": f"Ejercicio {i}",
                    "dificultad": np.random.uniform(0.2, 0.8)
                }
                for i in range(1, 11)  # 10 reactivos
            ],
            "parametros": {
                "poblacion_size": 80,
                "generaciones": 150,
                "num_ejercicios": 4,
                "prob_mutacion": 0.15,
                "elitismo": 0.2
            }
        }
        
        return self._ejecutar_prueba("Parámetros Personalizados", test_data)

    def test_casos_extremos(self) -> List[Dict]:
        """Prueba casos extremos"""
        casos = []
        
        # Caso 1: Usuario sin debilidades
        caso1 = {
            "nombre": "Sin debilidades",
            "data": {
                "debilidades": {"lectura": 0.0, "escritura": 0.0, "memoria": 0.0},
                "reactivos": [
                    {"id_reactivo": 1, "lectura": 0.5, "escritura": 0.5, "memoria": 0.5}
                ]
            }
        }
        
        # Caso 2: Todas las debilidades al máximo
        caso2 = {
            "nombre": "Máximas debilidades",
            "data": {
                "debilidades": {"lectura": 1.0, "escritura": 1.0, "memoria": 1.0},
                "reactivos": [
                    {"id_reactivo": 1, "lectura": 0.3, "escritura": 0.4, "memoria": 0.5},
                    {"id_reactivo": 2, "lectura": 0.6, "escritura": 0.2, "memoria": 0.8}
                ]
            }
        }
        
        # Caso 3: Solo un reactivo disponible
        caso3 = {
            "nombre": "Un solo reactivo",
            "data": {
                "debilidades": {"lectura": 0.5, "escritura": 0.5, "memoria": 0.5},
                "reactivos": [
                    {"id_reactivo": 1, "lectura": 0.7, "escritura": 0.7, "memoria": 0.7}
                ]
            }
        }
        
        resultados = []
        for caso in [caso1, caso2, caso3]:
            resultado = self._ejecutar_prueba(caso["nombre"], caso["data"])
            resultados.append(resultado)
            
        return resultados

    def test_validaciones(self) -> List[Dict]:
        """Prueba las validaciones de entrada"""
        casos_invalidos = []
        
        # Debilidades fuera de rango
        caso1 = {
            "debilidades": {"lectura": 1.5, "escritura": 0.5, "memoria": 0.5},
            "reactivos": [{"id_reactivo": 1, "lectura": 0.5, "escritura": 0.5, "memoria": 0.5}]
        }
        
        # IDs duplicados
        caso2 = {
            "debilidades": {"lectura": 0.5, "escritura": 0.5, "memoria": 0.5},
            "reactivos": [
                {"id_reactivo": 1, "lectura": 0.5, "escritura": 0.5, "memoria": 0.5},
                {"id_reactivo": 1, "lectura": 0.3, "escritura": 0.3, "memoria": 0.3}
            ]
        }
        
        # Sin reactivos
        caso3 = {
            "debilidades": {"lectura": 0.5, "escritura": 0.5, "memoria": 0.5},
            "reactivos": []
        }
        
        resultados = []
        for i, caso in enumerate([caso1, caso2, caso3], 1):
            try:
                response = self.session.post(
                    f"{self.base_url}/recomendar",
                    json=caso,
                    headers=HEADERS
                )
                if response.status_code != 200:
                    resultados.append({
                        "caso": f"Validación {i}",
                        "status": "✅ Validación funcionando",
                        "codigo": response.status_code,
                        "error": response.json().get("detail", "Error desconocido")
                    })
                else:
                    resultados.append({
                        "caso": f"Validación {i}",
                        "status": "❌ Validación fallida",
                        "codigo": response.status_code
                    })
            except Exception as e:
                resultados.append({
                    "caso": f"Validación {i}",
                    "status": "❌ Error de conexión",
                    "error": str(e)
                })
        
        return resultados

    def test_rendimiento(self, num_pruebas: int = 5) -> Dict:
        """Prueba de rendimiento con múltiples ejecuciones"""
        print(f"\n🚀 EJECUTANDO PRUEBA DE RENDIMIENTO ({num_pruebas} iteraciones)")
        
        # Generar datos de prueba más grandes
        reactivos_grandes = [
            {
                "id_reactivo": i,
                "lectura": np.random.uniform(0.1, 0.9),
                "escritura": np.random.uniform(0.1, 0.9),
                "memoria": np.random.uniform(0.1, 0.9),
                "nombre": f"Ejercicio {i}",
                "dificultad": np.random.uniform(0.2, 0.8)
            }
            for i in range(1, 51)  # 50 reactivos
        ]
        
        test_data = {
            "debilidades": {"lectura": 0.6, "escritura": 0.4, "memoria": 0.8},
            "reactivos": reactivos_grandes,
            "parametros": {
                "poblacion_size": 100,
                "generaciones": 200,
                "num_ejercicios": 10
            }
        }
        
        tiempos = []
        fitness_scores = []
        
        for i in range(num_pruebas):
            print(f"  Ejecutando prueba {i+1}/{num_pruebas}...")
            inicio = time.time()
            
            try:
                response = self.session.post(
                    f"{self.base_url}/recomendar",
                    json=test_data,
                    headers=HEADERS,
                    timeout=60  # Timeout de 60 segundos
                )
                
                tiempo_total = time.time() - inicio
                tiempos.append(tiempo_total)
                
                if response.status_code == 200:
                    resultado = response.json()
                    fitness_scores.append(resultado['fitness_score'])
                    print(f"    ✅ Completada en {tiempo_total:.2f}s - Fitness: {resultado['fitness_score']:.4f}")
                else:
                    print(f"    ❌ Error {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                tiempos.append(None)
        
        # Filtrar tiempos válidos
        tiempos_validos = [t for t in tiempos if t is not None]
        fitness_validos = [f for f in fitness_scores if f is not None]
        
        if tiempos_validos:
            estadisticas = {
                "pruebas_exitosas": len(tiempos_validos),
                "tiempo_promedio": np.mean(tiempos_validos),
                "tiempo_min": np.min(tiempos_validos),
                "tiempo_max": np.max(tiempos_validos),
                "desviacion_tiempo": np.std(tiempos_validos),
                "fitness_promedio": np.mean(fitness_validos) if fitness_validos else 0,
                "fitness_consistencia": np.std(fitness_validos) if len(fitness_validos) > 1 else 0
            }
        else:
            estadisticas = {"error": "Todas las pruebas fallaron"}
        
        return estadisticas

    def _ejecutar_prueba(self, nombre: str, test_data: Dict) -> Dict:
        """Ejecuta una prueba individual"""
        print(f"\n🧪 EJECUTANDO: {nombre}")
        print("=" * 50)
        
        try:
            inicio = time.time()
            response = self.session.post(
                f"{self.base_url}/recomendar",
                json=test_data,
                headers=HEADERS
            )
            tiempo_respuesta = time.time() - inicio
            
            if response.status_code == 200:
                resultado = response.json()
                
                print(f"✅ ÉXITO - Tiempo: {tiempo_respuesta:.3f}s")
                print(f"📚 Ejercicios recomendados: {resultado['ejercicios_recomendados']}")
                print(f"📊 Fitness Score: {resultado['fitness_score']}")
                print(f"🧬 Generaciones: {resultado['generacion']}")
                print(f"⚡ Tiempo AG: {resultado['estadisticas']['tiempo_ejecucion']}s")
                print(f"📈 Mejora: {resultado['estadisticas']['mejora_porcentual']:.1f}%")
                
                print(f"\n💪 Mejora esperada por habilidad:")
                for habilidad, mejora in resultado['mejora_esperada'].items():
                    print(f"   • {habilidad.capitalize()}: +{mejora:.3f}")
                
                # Mostrar análisis si está disponible
                if 'analisis' in resultado:
                    analisis = resultado['analisis']
                    if 'recomendaciones_adicionales' in analisis:
                        print(f"\n💡 Recomendaciones adicionales:")
                        for rec in analisis['recomendaciones_adicionales']:
                            print(f"   • {rec}")
                
                return {
                    "nombre": nombre,
                    "status": "exitoso",
                    "tiempo_respuesta": tiempo_respuesta,
                    "resultado": resultado
                }
                
            else:
                print(f"❌ ERROR {response.status_code}: {response.text}")
                return {
                    "nombre": nombre,
                    "status": "error",
                    "codigo": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT - La prueba tardó demasiado")
            return {"nombre": nombre, "status": "timeout"}
        except requests.exceptions.ConnectionError:
            print("❌ ERROR DE CONEXIÓN - Servidor no disponible")
            return {"nombre": nombre, "status": "conexion_error"}
        except Exception as e:
            print(f"❌ ERROR INESPERADO: {str(e)}")
            return {"nombre": nombre, "status": "error_inesperado", "error": str(e)}

    def generar_reporte(self, resultados: List[Dict]) -> None:
        """Genera un reporte de todas las pruebas"""
        print(f"\n📋 REPORTE FINAL DE PRUEBAS")
        print("=" * 60)
        
        exitosas = sum(1 for r in resultados if r.get("status") == "exitoso")
        total = len(resultados)
        
        print(f"📊 Resumen: {exitosas}/{total} pruebas exitosas ({exitosas/total*100:.1f}%)")
        
        if exitosas > 0:
            tiempos = [r["tiempo_respuesta"] for r in resultados if "tiempo_respuesta" in r]
            if tiempos:
                print(f"⚡ Tiempo promedio de respuesta: {np.mean(tiempos):.3f}s")
                print(f"⚡ Tiempo máximo: {np.max(tiempos):.3f}s")
                print(f"⚡ Tiempo mínimo: {np.min(tiempos):.3f}s")
        
        print(f"\n🔍 Detalle por prueba:")
        for resultado in resultados:
            nombre = resultado.get("nombre", "Desconocida")
            status = resultado.get("status", "desconocido")
            if status == "exitoso":
                tiempo = resultado.get("tiempo_respuesta", 0)
                print(f"   ✅ {nombre}: {tiempo:.3f}s")
            else:
                print(f"   ❌ {nombre}: {status}")

def main():
    """Función principal para ejecutar todas las pruebas"""
    print("🚀 INICIANDO SUITE COMPLETA DE PRUEBAS")
    print("=" * 60)
    
    client = TestClient()
    todos_resultados = []
    
    # 1. Verificar salud del sistema
    if not client.test_health():
        print("❌ Sistema no disponible. Verifica que el servidor esté ejecutándose.")
        print("   Comando: uvicorn main:app --reload")
        return
    
    # 2. Pruebas funcionales
    print(f"\n🧪 FASE 1: PRUEBAS FUNCIONALES")
    todos_resultados.append(client.test_ejemplo_basico())
    todos_resultados.append(client.test_con_parametros_personalizados())
    
    # 3. Casos extremos
    print(f"\n🎯 FASE 2: CASOS EXTREMOS")
    resultados_extremos = client.test_casos_extremos()
    todos_resultados.extend(resultados_extremos)
    
    # 4. Validaciones
    print(f"\n🛡️ FASE 3: VALIDACIONES")
    resultados_validaciones = client.test_validaciones()
    for resultado in resultados_validaciones:
        print(f"   {resultado['status']}: {resultado['caso']}")
    
    # 5. Prueba de rendimiento
    print(f"\n⚡ FASE 4: RENDIMIENTO")
    estadisticas_rendimiento = client.test_rendimiento(num_pruebas=3)
    if "error" not in estadisticas_rendimiento:
        print(f"   ✅ Pruebas exitosas: {estadisticas_rendimiento['pruebas_exitosas']}")
        print(f"   ⏱️ Tiempo promedio: {estadisticas_rendimiento['tiempo_promedio']:.2f}s")
        print(f"   📊 Fitness promedio: {estadisticas_rendimiento['fitness_promedio']:.4f}")
    
    # 6. Reporte final
    client.generar_reporte(todos_resultados)
    
    print(f"\n🎉 SUITE DE PRUEBAS COMPLETADA")
    print("💡 Para más pruebas interactivas, visita: http://localhost:8000/docs")

if __name__ == "__main__":
    main()