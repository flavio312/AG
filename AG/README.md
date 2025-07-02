# 🚀 Guía Completa de Compilación y Despliegue

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Python**: 3.8 o superior
- **RAM**: 512 MB mínimo, 2 GB recomendado
- **CPU**: 1 core mínimo, 2+ cores recomendado
- **Espacio en disco**: 100 MB para dependencias

### Dependencias del Sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip

# macOS (con Homebrew)
brew install python

# Windows
# Descargar Python desde python.org
```

## 🛠️ Instalación Local

### 1. Preparar el Entorno
```bash
# Crear directorio del proyecto
mkdir sistema-recomendacion
cd sistema-recomendacion

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. Instalar Dependencias
```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias principales
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install pydantic==2.5.0
pip install numpy==1.24.3
pip install python-multipart==0.0.6

# Dependencias adicionales para pruebas
pip install requests matplotlib aiohttp

# O instalar desde requirements.txt
pip install -r requirements.txt
```

### 3. Estructura del Proyecto
```
sistema-recomendacion/
├── main.py                 # Aplicación principal mejorada
├── test_client.py          # Cliente de pruebas mejorado
├── requirements.txt        # Dependencias
├── README.md              # Documentación
├── logs/                  # Directorio para logs (crear)
├── config/                # Configuraciones (opcional)
└── tests/                 # Pruebas adicionales (opcional)
```

## 🏃‍♂️ Ejecución Local

### Desarrollo (con recarga automática)
```bash
# Opción 1: Comando directo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opción 2: Con logging detallado
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Opción 3: Desde Python
python main.py
```

### Producción Local
```bash
# Sin recarga automática, múltiples workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Con configuración de logging
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-config logging.conf
```

### Verificar Instalación
```bash
# Ejecutar pruebas
python test_client.py

# Verificar endpoints manualmente
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Documentación interactiva
```

## 🐳 Despliegue con Docker

### 1. Crear Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 2. Crear docker-compose.yml
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Opcional: Nginx como proxy reverso
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
    restart: unless-stopped
```

### 3. Comandos Docker
```bash
# Construir imagen
docker build -t sistema-recomendacion .

# Ejecutar contenedor
docker run -d -p 8000:8000 --name recomendacion-api sistema-recomendacion

# Con docker-compose
docker-compose up -d

# Ver logs
docker logs sistema-recomendacion
docker-compose logs -f api

# Parar servicios
docker-compose down
```

## ☁️ Despliegue en la Nube

### 1. Heroku
```bash
# Instalar Heroku CLI
# Crear Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT --workers 2" > Procfile

# Crear runtime.txt
echo "python-3.11.0" > runtime.txt

# Comandos Heroku
heroku create sistema-recomendacion-app
heroku config:set PYTHONPATH=.
git push heroku main
```

### 2. DigitalOcean App Platform
```yaml
# .do/app.yaml
name: sistema-recomendacion
services:
- name: api
  source_dir: /
  github:
    repo: tu-usuario/tu-repo
    branch: main
  run_command: uvicorn main:app --host 0.0.0.0 --port 8080 --workers 2
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  health_check:
    http_path: /health
```

### 3. AWS (EC2 + Application Load Balancer)
```bash
# Script de instalación en EC2
#!/bin/bash
sudo yum update -y
sudo yum install python3 python3-pip git -y

# Clonar repositorio
git clone https://github.com/tu-usuario/sistema-recomendacion.git
cd sistema-recomendacion

# Instalar dependencias
pip3 install -r requirements.txt

# Instalar y configurar supervisor
sudo yum install supervisor -y

# Crear configuración supervisor
sudo tee /etc/supervisor/conf.d/recomendacion.conf > /dev/null <<EOF
[program:recomendacion-api]
command=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
directory=/home/ec2-user/sistema-recomendacion
user=ec2-user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/recomendacion.log
EOF

# Iniciar supervisor
sudo systemctl enable supervisord
sudo systemctl start supervisord
sudo supervisorctl reread
sudo supervisorctl update
```

### 4. Google Cloud Platform (Cloud Run)
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/sistema-recomendacion', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/sistema-recomendacion']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'sistema-recomendacion', 
         '--image', 'gcr.io/$PROJECT_ID/sistema-recomendacion', 
         '--platform', 'managed', 
         '--region', 'us-central1',
         '--allow-unauthenticated']
```

```bash
# Comandos GCP
gcloud builds submit --config cloudbuild.yaml
gcloud run deploy sistema-recomendacion \
  --image gcr.io/PROJECT_ID/sistema-recomendacion \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔧 Configuración de Producción

### 1. Variables de Entorno
```bash
# .env (crear este archivo)
LOG_LEVEL=info
WORKERS=4
HOST=0.0.0.0
PORT=8000
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
TIMEOUT_KEEP_ALIVE=5
```

### 2. Configuración de Logging
```python
# logging_config.py
import logging
import sys
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

### 3. Nginx como Proxy Reverso
```nginx
# nginx.conf
upstream api_backend {
    server 127.0.0.1:8000;
    # Para múltiples instancias:
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name tu-dominio.com;

    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    # Configuración SSL
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Configuración de proxy
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Endpoint de salud para load balancer
    location /health {
        proxy_pass http://api_backend/health;
        access_log off;
    }
}
```

## 🔍 Monitoreo y Mantenimiento

### 1. Healthchecks
```python
# Agregadar al main.py
@app.get("/health/detailed")
async def detailed_health():
    import psutil
    import os
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0",
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime": time.time() - psutil.boot_time()
        },
        "process": {
            "pid": os.getpid(),
            "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
        }
    }
```

### 2. Script de Monitoreo
```bash
#!/bin/bash
# monitor.sh

API_URL="http://localhost:8000/health"
LOG_FILE="/var/log/api_monitor.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Verificar salud de la API
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "$TIMESTAMP - API OK" >> $LOG_FILE
    else
        echo "$TIMESTAMP - API ERROR: HTTP $HTTP_CODE" >> $LOG_FILE
        # Enviar alerta (email, slack, etc.)
        # curl -X POST -H 'Content-type: application/json' \
        #   --data '{"text":"API Down!"}' \
        #   YOUR_SLACK_WEBHOOK_URL
    fi
    
    sleep 60  # Verificar cada minuto
done
```

### 3. Backup y Logs
```bash
#!/bin/bash
# backup_logs.sh

LOG_DIR="/app/logs"
BACKUP_DIR="/backup/logs"
DATE=$(date +%Y%m%d)

# Crear backup de logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" "$LOG_DIR"

# Limpiar logs antiguos (más de 30 días)
find "$LOG_DIR" -name "*.log" -mtime +30 -delete

# Limpiar backups antiguos (más de 90 días)
find "$BACKUP_DIR" -name "logs_*.tar.gz" -mtime +90 -delete
```

## 🚀 Comandos Útiles de Despliegue

### Desarrollo Local
```bash
# Desarrollo con recarga automática
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Pruebas
python test_client.py

# Verificar rendimiento
curl -X POST http://localhost:8000/recomendar \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### Producción
```bash
# Inicio optimizado para producción
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --max-requests 1000 \
  --max-requests-jitter 50

# Con Gunicorn (alternativa)
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --max-requests 1000 \
  --timeout 60
```

### Despliegue Automatizado
```bash
#!/bin/bash
# deploy.sh

set -e  # Parar si hay errores

echo "🚀 Iniciando despliegue..."

# 1. Backup de la versión actual
if [ -d "/app/sistema-recomendacion" ]; then
    cp -r /app/sistema-recomendacion /backup/sistema-recomendacion-$(date +%Y%m%d_%H%M%S)
fi

# 2. Actualizar código
cd /app/sistema-recomendacion
git pull origin main

# 3. Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# 4. Ejecutar pruebas
python test_client.py

# 5. Reiniciar servicio
sudo supervisorctl restart recomendacion-api

# 6. Verificar salud
sleep 10
curl -f http://localhost:8000/health || exit 1

echo "✅ Despliegue completado exitosamente"
```

## 📊 Optimizaciones de Rendimiento

### 1. Parámetros del Algoritmo Genético
```python
# Configuración para diferentes escenarios

# Desarrollo/Testing (rápido)
PARAMETROS_DEV = {
    "poblacion_size": 20,
    "generaciones": 30,
    "num_ejercicios": 3
}

# Producción balanceada
PARAMETROS_PROD = {
    "poblacion_size": 50,
    "generaciones": 100,
    "num_ejercicios": 5
}

# Alta precisión (para casos críticos)
PARAMETROS_PRECISION = {
    "poblacion_size": 100,
    "generaciones": 200,
    "num_ejercicios": 8
}
```

### 2. Caching (Redis)
```python
# Agregar al main.py para cache
import redis
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def generar_cache_key(debilidades, reactivos):
    data_str = json.dumps({
        "debilidades": debilidades,
        "reactivos_ids": sorted([r['id_reactivo'] for r in reactivos])
    }, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

# En el endpoint recomendar
cache_key = generar_cache_key(debilidades_dict, reactivos_list)
cached_result = redis_client.get(cache_key)

if cached_result:
    return json.loads(cached_result)
    
# ... ejecutar algoritmo ...

# Guardar en cache (expirar en 1 hora)
redis_client.setex(cache_key, 3600, json.dumps(response))
```

## 🐛 Solución de Problemas Comunes

### Error: "ModuleNotFoundError"
```bash
# Verificar entorno virtual activado
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt

# Verificar Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/your/app"
```

### Error: "Port already in use"
```bash
# Encontrar proceso usando el puerto
lsof -i :8000
# o
netstat -tulpn | grep :8000

# Matar proceso
kill -9 PID_NUMBER

# Usar puerto diferente
uvicorn main:app --port 8001
```

### Memoria insuficiente
```bash
# Reducir workers
uvicorn main:app --workers 1

# Monitorear memoria
htop
# o
ps aux | grep uvicorn
```

### Logs no se generan
```bash
# Crear directorio de logs
mkdir -p logs

# Verificar permisos
chmod 755 logs

# Logs manuales en desarrollo
uvicorn main:app --log-level debug
```

## 📈 Escalabilidad

### Load Balancer con múltiples instancias
```bash
# Ejecutar múltiples instancias
uvicorn main:app --port 8000 &
uvicorn main:app --port 8001 &
uvicorn main:app --port 8002 &

# Configurar Nginx upstream (ver configuración anterior)
```

### Auto-scaling con Docker Swarm
```yaml
# docker-stack.yml
version: '3.8'
services:
  api:
    image: sistema-recomendacion:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    ports:
      - "8000:8000"
    networks:
      - api-network

networks:
  api-network:
    driver: overlay
```

```bash
# Desplegar stack
docker stack deploy -c docker-stack.yml sistema-recomendacion

# Escalar servicios
docker service scale sistema-recomendacion_api=5
```

¡Tu sistema de recomendación ahora está completamente optimizado y listo para producción! 🎉