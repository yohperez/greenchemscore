# 🧪 GreenChem Score

**Pipeline ETL para Clasificación Química Sostenible**

Aplicación Streamlit que extrae datos de compuestos químicos, los enriquece con información de la API de PubChem (PUG REST), y genera visualizaciones interactivas para evaluar la sostenibilidad [...]

---

## 📊 Composición del Proyecto

Este proyecto está construido principalmente con:
- **Python** (92.1%) — Lógica principal, ETL y análisis
- **Dockerfile** (4.7%) — Containerización
- **Makefile** (3.2%) — Automatización de tareas

---

## 🚀 Demo en Vivo

👉 [Ver aplicación en Streamlit Cloud](https://greenchemscore.streamlit.app/)

---

## 🛠️ Tecnologías

| Librería | Icono | Descripción | Uso |
|----------|-------|-------------|-----|
| **Streamlit** | 🎈 | Framework para apps de datos | Interface principal de la app |
| **Plotly** | 📈 | Visualizaciones interactivas | Gráficos, heatmaps, radar charts |
| **Folium** | 🗺️ | Mapas geográficos | Visualización de ubicaciones industriales |
| **Pandas** | 🐼 | Manipulación de datos | ETL y procesamiento de datasets |
| **Requests + BeautifulSoup** | 🌐 | HTTP y parsing HTML | Scraping y APIs REST |
| **SQLite3** | 💾 | Base de datos ligera | Persistencia de datos |
| **Docker** | 🐳 | Containerización | Despliegue reproducible |

---

## 🐳 Uso Rápido con Docker

La forma más fácil de ejecutar la app localmente es usando Docker. No necesitas instalar Python ni dependencias.

### Requisito único: Docker instalado

- **Windows/Mac**: [Descargar Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: `sudo apt install docker.io`

### Ejecución rápida

```bash
docker run -p 8501:8501 yohperez/greenchemscore:latest
```

Abre **http://localhost:8501** en tu navegador. ¡Listo!

### Opciones de ejecución

| Modo | Comando | Uso |
|------|---------|-----|
| **Interactivo** | `docker run -p 8501:8501 yohperez/greenchemscore:latest` | Para probar, ver logs en terminal |
| **Background** | `docker run -d -p 8501:8501 --name greenchem yohperez/greenchemscore:latest` | Segundo plano, siempre disponible |
| **Con nombre** | `docker run -p 8501:8501 --name greenchem yohperez/greenchemscore:latest` | Fácil de detener: `docker stop greenchem` |

### Docker Compose (Recomendado para uso continuo)

Crea un archivo `docker-compose.yml`:

```yaml
version: "3.9"

services:
  greenchemscore:
    image: yohperez/greenchemscore:latest
    container_name: greenchemscore
    ports:
      - "8501:8501"
    restart: unless-stopped
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
```

Ejecuta con:
```bash
docker-compose up -d
```

### Con persistencia de datos

Para guardar los CSV y SQLite generados en tu PC:

```bash
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  --name greenchem \
  yohperez/greenchemscore:latest
```

Los archivos se guardarán en la carpeta `data/` local.

---

## 🌐 Desplegar en Otras Plataformas

Tu imagen Docker está lista para desplegar en cualquier plataforma que soporte contenedores:

### Railway (Gratuito)
```bash
npm install -g @railway-cli
railway login
railway init
railway up
```

### Render (Gratuito)
1. Ve a [render.com](https://render.com)
2. New Web Service → Existing Image
3. Image URL: `docker.io/yohperez/greenchemscore:latest`
4. Port: `8501`

### AWS / Azure / Google Cloud
Usa la imagen `yohperez/greenchemscore:latest` directamente en cualquier servicio de contenedores.

### VPS Propio (DigitalOcean, Linode, etc.)
```bash
docker run -d -p 80:8501 --restart always yohperez/greenchemscore:latest
```

---

## 🖥️ Desarrollo Local

### Requisitos
- Python 3.11+
- Git

### Instalación

```bash
# Clonar repo
git clone https://github.com/yohperez/greenchemscore.git
cd greenchemscore

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

La app estará en `http://localhost:8501`.

---

## 📋 Características

| Página | Funcionalidad |
|--------|---------------|
| 🏠 **Inicio** | Descripción del pipeline y métricas del Green Score |
| 🔬 **Pipeline ETL** | Ejecuta extracción, enriquecimiento PubChem y persistencia CSV/SQLite |
| 📊 **Dashboard** | 6 visualizaciones Plotly: heatmap, radar, distribuciones, H-statements, pictogramas |
| 🗺️ **Mapa Geográfico** | Mapa Folium con ubicaciones industriales ficticias |
| 🧪 **Simulador de Sustitución** | Compara químico original vs. sustituto (conceptual) |
| ⚖️ **Alertas Regulatorias** | Sistema conceptual de monitoreo REACH/EPA |
| 📥 **Descargas** | Exporta datos en CSV, Excel y SQLite |

---

## 🏗️ Estructura del Repositorio

```
greenchemscore/
├── app.py                 # Aplicación Streamlit principal
├── requirements.txt       # Dependencias Python
├── Dockerfile             # Imagen Docker para producción
├── .dockerignore          # Exclusiones de Docker
├── .gitignore             # Exclusiones de Git
├── docker-compose.yml     # Compose para desarrollo local
├── Makefile               # Comandos útiles
├── README.md              # Este archivo
├── LICENSE                # MIT License
├── .streamlit/
│   ├── config.toml        # Configuración de Streamlit
│   └── secrets.toml       # Secrets (template, NO commitear)
└── .github/workflows/
    ├── docker-push.yml    # CI/CD para Docker Hub
    └── streamlit-deploy.yml # Verificación de build
```

---

## 🚀 Makefile

El proyecto incluye un `Makefile` para automatizar tareas comunes:

```bash
make help      # Mostrar comandos disponibles
make install   # Instalar dependencias
make run       # Ejecutar aplicación local
make build     # Construir imagen Docker
make docker    # Ejecutar contenedor Docker
```

---

## ☁️ Despliegue en Streamlit Cloud

1. **Crear repositorio en GitHub** y subir este código.
2. Ir a [share.streamlit.io](https://share.streamlit.io) e iniciar sesión con GitHub.
3. Hacer clic en **"New app"** → seleccionar tu repositorio.
4. Configurar:
   - **Repository:** `yohperez/greenchemscore`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Clic en **"Deploy"**.

### Secrets en Streamlit Cloud

Si necesitas API keys u otros secrets:
1. En Streamlit Cloud, ve a tu app → **Settings** → **Secrets**.
2. Agregar los secrets en formato TOML:
   ```toml
   [api_keys]
   pubchem_api_key = "tu_key"
   ```

---

## 🐳 Docker Hub (CI/CD Automático)

El repositorio incluye un workflow de GitHub Actions que construye y empuja la imagen Docker a Docker Hub automáticamente en cada push a `main`.

### Configuración necesaria

1. **Crear cuenta en Docker Hub:** [hub.docker.com](https://hub.docker.com)
2. **Generar Access Token:**
   - Ir a **Account Settings** → **Security** → **New Access Token**
   - Permisos: **Read, Write, Delete**
   - Copiar el token generado.
3. **Configurar secrets en GitHub:**
   - Ir a tu repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Agregar:
     - `DOCKERHUB_TOKEN` — el access token generado
     - `DOCKERHUB_USERNAME` — tu usuario de Docker Hub

### Pull de la imagen

```bash
docker pull yohperez/greenchemscore:latest
```

### Ejecutar desde Docker Hub

```bash
docker run -p 8501:8501 yohperez/greenchemscore:latest
```

---

## 🛡️ Gobernanza Ética

- **User-Agent realista** identifica el bot como navegador legítimo.
- **Delay de cortesía** de 1.5s entre peticiones a PubChem.
- **Manejo robusto de errores:** compuestos no encontrados se registran pero no detienen el pipeline.
- **Trazabilidad completa** con timestamps y logging estructurado.

---

## 📊 Base del Green Score

Los códigos H extraídos permiten calcular un score de sostenibilidad:

| Código | Descripción | Impacto |
|--------|-------------|---------|
| H400-H413 | Toxicidad acuática | 🔴 Crítico para ecosistemas |
| H300-H372 | Toxicidad aguda/crónica | 🔴 Riesgo para salud humana |
| Sin códigos | Compuestos seguros | 🟢 Puntuación alta de verde |

---

## 📄 Licencia

MIT License — ver [LICENSE](LICENSE) para más detalles.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Abre un issue o un pull request.

---

**Desarrollado con 🌿 por [yohperez](https://github.com/yohperez)**
