# Seattle Energy Prediction API

API de prédiction de consommation énergétique des bâtiments de Seattle.

## 🚀 Déploiement

Cette API est déployée sur Render.com à partir de ce repository.

## 🧪 Test local

Pour tester localement avec Docker :

    docker build -t energy-api .
    docker run -p 3000:3000 energy-api

## 📖 Documentation

Une fois déployé, accédez à la documentation Swagger :

    https://votre-app.onrender.com/docs

## 🏗️ Architecture

- **Framework**: BentoML
- **Modèle**: XGBoost
- **Validation**: Pydantic
- **Déploiement**: Docker sur Render.com

## 📊 Exemple de requête

    curl -X POST https://votre-app.onrender.com/predict \
      -H "Content-Type: application/json" \
      -d '{
        "input_data": {
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
      }'

## 👨‍💻 Auteur

Projet réalisé dans le cadre de la formation Data Engineer - OpenClassrooms
