# ╔══════════════════════════════════════════════════════════════════════╗
# ║  GreenChem Score — Makefile                                          ║
# ║  Comandos útiles para desarrollo y despliegue                       ║
# ╚══════════════════════════════════════════════════════════════════════╝

.PHONY: help install run docker-build docker-run docker-push clean

help: ## Muestra esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  [36m%-15s[0m %s\n", $$1, $$2}'

install: ## Instalar dependencias locales
	python -m pip install -r requirements.txt

run: ## Ejecutar Streamlit localmente
	streamlit run app.py

docker-build: ## Construir imagen Docker
	docker build -t greenchemscore:latest .

docker-run: ## Ejecutar contenedor Docker
	docker run -p 8501:8501 --name greenchemscore-app greenchemscore:latest

docker-push: ## Etiquetar y empujar a Docker Hub (requiere login previo)
	docker tag greenchemscore:latest $(DOCKER_USER)/greenchemscore:latest
	docker push $(DOCKER_USER)/greenchemscore:latest

clean: ## Limpiar archivos generados
	rm -f greenchem_dataset.csv greenchem_db.db
	rm -rf __pycache__ .pytest_cache
	docker rm -f greenchemscore-app 2>/dev/null || true

docker-compose-up: ## Levantar con docker-compose
	docker-compose up --build -d

docker-compose-down: ## Detener docker-compose
	docker-compose down
