# Seattle Building Energy Consumption Prediction API

## Project Overview

This project aims to predict the energy consumption (in kBtu) of non-residential buildings in Seattle, Washington, based on their structural characteristics, usage patterns, and geographical location. Developed for the City of Seattle's Data Engineering team, this API provides a valuable tool for identifying buildings with high energy consumption, enabling targeted energy efficiency interventions and supporting the city's goal of becoming carbon-neutral by 2050.

## Key Features

*   **Non-Residential Focus**: The model is specifically tailored for commercial and institutional buildings, excluding residential properties.
*   **Data-Driven Predictions**: Utilizes detailed 2016 building benchmarking data provided by the City of Seattle.
*   **Structural & Usage Analysis**: Predictions are based on factors such as total floor area (`PropertyGFATotal`), number of floors (`NumberofFloors`), year built (`YearBuilt`), building type (`PrimaryPropertyType`), and presence of multiple uses.
*   **Geographical Insights**: Incorporates location data (Latitude, Longitude, Neighborhood) to capture regional consumption patterns.
*   **API-First Design**: The predictive model is encapsulated within a RESTful API using BentoML, allowing for easy integration into other applications.

## Data Source

The project utilizes the `2016_Building_Energy_Benchmarking.csv` dataset, which contains detailed energy usage and structural information for buildings in Seattle.

## Methodology

The development process followed a standard data science workflow:

1.  **Exploratory Data Analysis (EDA)**: Identified key insights, data distributions, and potential issues (e.g., residential buildings, outliers, missing values).
2.  **Data Cleaning & Preprocessing**: 
    *   Filtered out residential buildings.
    *   Handled missing values and removed irrelevant columns.
    *   Corrected inconsistent categorical data (e.g., `Neighborhood` names).
    *   Addressed outliers in the target variable (`SiteEnergyUse(kBtu)`) and `NumberofFloors`.
3.  **Feature Engineering**: Created new informative features such as `BuildingAge`, `ParkingRatio`, `AvgFloorArea`, `HasMultipleUses`, `DistanceToCenter`, `LocationZone`, `ComplexityScore`, and an imputed `ENERGYSTARScore`.
4.  **Feature Selection & Encoding**: Categorical features were One-Hot Encoded, and numerical features were scaled using `StandardScaler`. Features leading to data leakage (e.g., direct energy consumption metrics) were carefully excluded.
5.  **Model Development & Optimization**: 
    *   Evaluated several regression models (Linear Regression, Random Forest, XGBoost).
    *   XGBoost demonstrated the best performance, even with initial overfitting concerns.
    *   Hyperparameter tuning using `GridSearchCV` and regularization techniques were applied to mitigate overfitting and improve generalization.
6.  **API Deployment**: The optimized model was packaged with BentoML and exposed as a RESTful API.

## Model Performance

The final model is an **Optimized XGBoost Regressor**.

*   **R² Score (Cross-Validation)**: `0.7377`
*   **R² Score (Test Set)**: `0.6769`
*   **Mean Absolute Error (MAE)**: `3,237,413` kBtu
*   **Root Mean Squared Error (RMSE)**: `6,769,855` kBtu

**Interpretation**: The model explains approximately 67.7% of the variance in energy consumption. With an average error of ±3.2 million kBtu, it provides a robust estimate, particularly useful for identifying high-consumption buildings and prioritizing energy audit efforts.

### Top 5 Most Important Features:

1.  `PropertyGFATotal` (Surface totale du bâtiment)
2.  `PropertyGFABuilding(s)` (Surface des bâtiments hors parking)
3.  `LargestPropertyUseTypeGFA` (Surface de l'usage principal)
4.  `LargestPropertyUseType_Office` (Type de bâtiment: Bureau)
5.  `LocationZone_Proche` (Localisation proche du centre-ville)

## API Usage

The API allows users to send building characteristics and receive a predicted energy consumption. The API is built with BentoML and can be run via Docker.

### Prerequisites

*   [Docker](https://docs.docker.com/get-docker/) installed and running on your local machine.
*   Python 3.11+

### Project Structure (on your local machine)

After downloading the necessary files and setting up your project locally, your directory structure should look like this:

```
seattle-energy-api/
├── Dockerfile
├── bentofile.yaml
├── requirements.txt
├── service_complete.py
└── models/
    ├── energy_consumption_model.bentomodel
    ├── energy_scaler.bentomodel
    ├── energy_encoder.bentomodel
    ├── feature_info.bentomodel
    └── categorical_mappings.bentomodel
```

### Build the Docker Image

Navigate to the `seattle-energy-api` directory in your terminal and run:

```bash
docker build -t seattle-energy-api:latest .
```

This command will build the Docker image, tagging it as `seattle-energy-api` with the version `latest`.

### Run the Docker Container

Once the image is built, you can run the container:

```bash
docker run -p 3000:3000 seattle-energy-api:latest
```

This command maps port `3000` from your host machine to port `3000` inside the container. Your API will then be accessible at `http://localhost:3000`.

### Test the API

With the Docker container running, you can test the API endpoint `http://localhost:3000/predict` using `curl` or any API client. The API also provides an interactive Swagger UI at `http://localhost:3000/docs`.

**Example Request (JSON body):**

```json
{
  "PropertyGFATotal": 50000,
  "NumberofFloors": 5,
  "YearBuilt": 1990,
  "PrimaryPropertyType": "Office",
  "Neighborhood": "DOWNTOWN",
  "Latitude": 47.6062,
  "Longitude": -122.3321,
  "PropertyGFAParking": 5000,
  "NumberofBuildings": 1,
  "ENERGYSTARScore": 75
}
```

**Example `curl` command:**

```bash
curl -X POST "http://localhost:3000/predict" \
     -H "Content-Type: application/json" \
     -d '{
  "PropertyGFATotal": 50000,
  "NumberofFloors": 5,
  "YearBuilt": 1990,
  "PrimaryPropertyType": "Office",
  "Neighborhood": "DOWNTOWN",
  "Latitude": 47.6062,
  "Longitude": -122.3321,
  "PropertyGFAParking": 5000,
  "NumberofBuildings": 1,
  "ENERGYSTARScore": 75
}'
```

**Example Response:**

```json
{
  "status": "success",
  "prediction": {
    "consumption_kbtu": 5234567.89,
    "consumption_kwh": 1534567.89,
    "consumption_mwh": 1534.57
  },
  "building_info": {
    "age_years": 26,
    "age_category": "Récent",
    "distance_to_center_km": 0.0,
    "location_zone": "Centre",
    "has_parking": true,
    "has_energy_star": true
  },
  "model_performance": {
    "r2_score": 0.677,
    "mae_kbtu": 3237413,
    "note": "Le modèle explique 67.7% de la variance"
  }
}
```

## Future Improvements

*   **Advanced Feature Engineering**: Explore more complex interactions and external data sources (e.g., weather data, economic indicators).
*   **Hyperparameter Optimization**: Conduct more extensive tuning using techniques like Bayesian Optimization.
*   **Ensemble Modeling**: Combine predictions from multiple models to potentially improve robustness and accuracy.
*   **Monitoring & Retraining**: Implement MLOps practices for continuous monitoring of model performance and automatic retraining with new data.

## Contact

KoBehram@wisty.fr

