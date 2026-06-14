# 🧪 GreenChem Score

**Pipeline ETL para Clasificación Química Sostenible**

Aplicación Streamlit que extrae datos de compuestos químicos, los enriquece con información de la API de PubChem (PUG REST), y genera visualizaciones interactivas para evaluar la sostenibilidad y toxicidad de químicos industriales.

---

## 🚀 Demo en Vivo

👉 [Ver aplicación en Streamlit Cloud](https://tu-app.streamlit.app) *(reemplazar con tu URL)*

---

## 📋 Características

| Fase | Descripción | Tecnología |
|------|-------------|------------|
| **Extracción** | Lista semilla de químicos industriales y cosméticos | Python + Requests |
| **Enriquecimiento** | Consulta a PubChem PUG REST: CID, fórmula, peso, SMILES, GHS H-statements | REST API |
| **Persistencia** | Exportación dual a CSV y SQLite con esquema indexado | Pandas + SQLite3 |
| **Visualización** | Dashboard interactivo con Plotly, Folium y Streamlit | Streamlit + Plotly |
| **Simulación** | Simulador conceptual de sustitución de químicos | Python |
| **Alertas** | Sistema conceptual de alertas regulatorias | Python |

---

## 🛠️ Tecnologías

- **Streamlit** — Framework para apps de datos
- **Plotly** — Visualizaciones interactivas
- **Folium** — Mapas geográficos
- **Pandas** — Manipulación de datos
- **Requests + BeautifulSoup** — HTTP y parsing HTML
- **SQLite3** — Base de datos ligera

---

## 🏗️ Estructura del Repositorio

```
greenchemscore/
├── app.py                 # Aplicación Streamlit principal
├── requirements.txt       # Dependencias Python
├── Dockerfile             # Imagen Docker para producción
├── .dockerignore          # Exclusiones de Docker
├── .gitignore             # Exclusiones de Git
├── .streamlit/
│   ├── config.toml        # Configuración de Streamlit
│   └── secrets.toml       # Secrets (template, NO commitear)
├── .github/
│   └── workflows/
│       └── docker-push.yml # CI/CD para Docker Hub
└── README.md              # Este archivo
```

---

## 🖥️ Ejecución Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/greenchemscore.git
cd greenchemscore
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate   # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

La app estará disponible en `http://localhost:8501`.

---

## 🐳 Docker (Local)

### Construir imagen

```bash
docker build -t greenchemscore:latest .
```

### Ejecutar contenedor

```bash
docker run -p 8501:8501 greenchemscore:latest
```

La app estará disponible en `http://localhost:8501`.

---

## ☁️ Despliegue en Streamlit Cloud

1. **Crear repositorio en GitHub** y subir este código.
2. Ir a [share.streamlit.io](https://share.streamlit.io) e iniciar sesión con GitHub.
3. Hacer clic en **"New app"** → seleccionar tu repositorio.
4. Configurar:
   - **Repository:** `tu-usuario/greenchemscore`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Hacer clic en **"Deploy"**.

### Secrets en Streamlit Cloud

Si necesitas API keys u otros secrets:
1. En Streamlit Cloud, ir a tu app → **Settings** → **Secrets**.
2. Agregar los secrets en formato TOML:
   ```toml
   [api_keys]
   pubchem_api_key = "tu_key"
   ```
3. En el código, acceder con `st.secrets["api_keys"]["pubchem_api_key"]`.

---

## 🐳 Docker Hub (CI/CD con GitHub Actions)

El repositorio incluye un workflow de GitHub Actions que construye y empuja la imagen Docker a Docker Hub automáticamente en cada push a `main`.

### Configuración necesaria

1. **Crear cuenta en Docker Hub:** [hub.docker.com](https://hub.docker.com)
2. **Generar Access Token:**
   - Ir a **Account Settings** → **Security** → **New Access Token**
   - Copiar el token generado.
3. **Configurar secrets en GitHub:**
   - Ir a tu repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Agregar:
     - `DOCKERHUB_USERNAME` — tu usuario de Docker Hub
     - `DOCKERHUB_TOKEN` — el access token generado
     - `DOCKERHUB_REPO_NAME` — nombre del repo en Docker Hub (ej: `greenchemscore`)

### Workflow

El archivo `.github/workflows/docker-push.yml` se ejecuta automáticamente:
- En cada push a `main`
- Construye la imagen multi-plataforma (`linux/amd64`, `linux/arm64`)
- Etiqueta con `latest` y el SHA corto del commit
- Empuja a Docker Hub

### Pull de la imagen

```bash
docker pull tu-usuario/greenchemscore:latest
```

### Ejecutar desde Docker Hub

```bash
docker run -p 8501:8501 tu-usuario/greenchemscore:latest
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

**Desarrollado con 🌿 por [Tu Nombre](https://github.com/tu-usuario)**
