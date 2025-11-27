# Use a base image with Python 3.11
FROM python:3.11-slim-bookworm

# Set working directory inside the container
WORKDIR /app

# Install BentoML and other dependencies
# Make sure to keep bentoml version in sync with your local environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your BentoML service file
COPY service_complete.py .
COPY bentofile.yaml .

# Copy your exported BentoML models
# You need to manually create a 'models' directory in your project folder
# and place the .bentomodel files inside it.
# For example: seattle-energy-api/models/energy_consumption_model.bentomodel
COPY models/ /home/bentoml/models/

# Restore the models into BentoML's local store within the container
# This step is crucial for BentoML to find your models at runtime
RUN bentoml models import /home/bentoml/models/energy_consumption_model.bentomodel
RUN bentoml models import /home/bentoml/models/energy_scaler.bentomodel
RUN bentoml models import /home/bentoml/models/energy_encoder.bentomodel
RUN bentoml models import /home/bentoml/models/feature_info.bentomodel
RUN bentoml models import /home/bentoml/models/categorical_mappings.bentomodel

# Expose the port that BentoML service listens on
EXPOSE 3000

# Command to run the BentoML service
# Ensure the service name matches the one in bentofile.yaml (EnergyPredictionService)
CMD ["bentoml", "serve", "service_complete:EnergyPredictionService", "--host", "0.0.0.0", "--port", "3000"]