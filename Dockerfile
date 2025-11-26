FROM python:3.11-slim

WORKDIR /app

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY service_complete.py .

# Copier et importer les modèles
COPY models_export/ ./models_export/

# Importer les modèles dans BentoML
RUN for model in ./models_export/*.bentomodel; do \
        if [ -f "$model" ]; then \
            echo "Importing $model..." && \
            bentoml models import "$model"; \
        fi \
    done

# Le port sera fourni par Render via $PORT
ENV PORT=3000
EXPOSE 3000

# Démarrer le service
CMD bentoml serve service_complete:EnergyPredictionService --host 0.0.0.0 --port $PORT
