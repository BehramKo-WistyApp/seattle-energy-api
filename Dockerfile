FROM python:3.11-slim

WORKDIR /app

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY service_complete.py .

# Copier les modèles
COPY models_export/ /app/models_export/

# Le port sera fourni par Render via $PORT
ENV PORT=3000
EXPOSE 3000

# Script de démarrage en une seule commande
CMD cd /app/models_export && \
    for model in *.bentomodel; do \
        echo "Importing $model..." && \
        bentoml models import "$model" || true; \
    done && \
    cd /app && \
    bentoml serve service_complete:EnergyPredictionService --host 0.0.0.0 --port $PORT