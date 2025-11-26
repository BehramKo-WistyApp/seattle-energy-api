FROM python:3.11-slim

WORKDIR /app

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY service_complete.py .

# Copier les modèles (on ne les importe PAS ici)
COPY models_export/ /app/models_export/



# Le port sera fourni par Render via $PORT
ENV PORT=3000
EXPOSE 3000

# Créer un script de démarrage
RUN echo '#!/bin/bash\n\
echo "Importing BentoML models..."\n\
cd /app/models_export\n\
for model in *.bentomodel; do\n\
    if [ -f "$model" ]; then\n\
        echo "Importing $model..."\n\
        bentoml models import "$model" || echo "Warning: Failed to import $model"\n\
    fi\n\
done\n\
echo "Starting BentoML service..."\n\
bentoml serve service_complete:EnergyPredictionService --host 0.0.0.0 --port $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Démarrer avec le script
CMD ["/app/start.sh"]
