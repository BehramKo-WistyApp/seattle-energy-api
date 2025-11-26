
import bentoml
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

# ============================================
# 1. SCHÉMA D'ENTRÉE SIMPLIFIÉ
# ============================================

class BuildingInput(BaseModel):
    """
    Input simplifié pour l'utilisateur.
    On demande seulement les infos essentielles.
    """

    # Caractéristiques de base
    PropertyGFATotal: float = Field(..., gt=10000, lt=10000000,
                                    description="Surface totale en sq ft")
    NumberofFloors: int = Field(..., ge=1, le=100,
                                description="Nombre d'étages")
    YearBuilt: int = Field(..., ge=1900, le=2024,
                          description="Année de construction")

    # Type et usage
    PrimaryPropertyType: str = Field(...,
                                     description="Type de bâtiment (ex: Office, Hotel, Hospital)")

    # Localisation
    Neighborhood: str = Field(...,
                             description="Quartier (ex: DOWNTOWN, BALLARD)")
    Latitude: float = Field(..., ge=47.5, le=47.8)
    Longitude: float = Field(..., ge=-122.5, le=-122.2)

    # Optionnels
    PropertyGFAParking: Optional[float] = Field(0, ge=0)
    NumberofBuildings: Optional[float] = Field(1, ge=1)
    ENERGYSTARScore: Optional[float] = Field(None, ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
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
        }


# ============================================
# 2. SERVICE BENTOML CORRIGÉ
# ============================================

@bentoml.service(
    resources={"cpu": "2"},
    traffic={"timeout": 10},
)
class EnergyPredictionService:
    """Service de prédiction de consommation énergétique"""

    # Charger les références des modèles
    xgb_model_ref = bentoml.models.get("energy_consumption_model:latest")
    scaler_model_ref = bentoml.models.get("energy_scaler:latest")
    encoder_model_ref = bentoml.models.get("energy_encoder:latest")
    feature_info_model_ref = bentoml.models.get("feature_info:latest")

    def __init__(self):
        # Charger les objets Python avec les bonnes méthodes
        import bentoml

        # XGBoost
        self.model = bentoml.xgboost.load_model(self.xgb_model_ref)

        # Scaler et feature_info : sauvegardés avec picklable_model
        self.scaler = bentoml.picklable_model.load_model(self.scaler_model_ref)
        self.feature_info = bentoml.picklable_model.load_model(self.feature_info_model_ref)

        # Encoder : sauvegardé avec sklearn
        self.encoder = bentoml.sklearn.load_model(self.encoder_model_ref)

        # Extraire les noms de features
        self.numeric_features = self.feature_info['numeric_features']
        self.binary_features = self.feature_info['binary_features']
        self.categorical_features = self.feature_info['categorical_features']

    @bentoml.api
    def predict(self, input_data: BuildingInput) -> Dict[str, Any]:
        """
        Prédire la consommation énergétique d'un bâtiment.

        Args:
            input_data: Caractéristiques du bâtiment

        Returns:
            Prédiction avec informations détaillées
        """

        # 1. Calculer les features dérivées
        features = self._compute_features(input_data.model_dump())

        # 2. Créer le DataFrame
        df_input = pd.DataFrame([features])

        # 3. Séparer numériques et catégorielles
        X_numeric = df_input[self.numeric_features + self.binary_features]
        X_categorical = df_input[self.categorical_features]

        # 4. Scaler les numériques
        X_numeric_scaled = self.scaler.transform(X_numeric)
        X_numeric_scaled = pd.DataFrame(
            X_numeric_scaled,
            columns=self.numeric_features + self.binary_features
        )

        # 5. Encoder les catégorielles
        X_categorical_encoded = self.encoder.transform(X_categorical)
        encoded_feature_names = self.encoder.get_feature_names_out(self.categorical_features)
        X_categorical_encoded = pd.DataFrame(
            X_categorical_encoded,
            columns=encoded_feature_names
        )

        # 6. Combiner
        X_final = pd.concat([X_numeric_scaled, X_categorical_encoded], axis=1)

        # 7. Prédiction
        prediction_kbtu = self.model.predict(X_final)[0]

        # 8. Retourner le résultat
        return {
            "status": "success",
            "prediction": {
                "consumption_kbtu": float(prediction_kbtu),
                "consumption_kwh": float(prediction_kbtu * 0.293071),
                "consumption_mwh": float(prediction_kbtu * 0.293071 / 1000),
            },
            "building_info": {
                "age_years": features['BuildingAge'],
                "age_category": features['AgeCategory'],
                "distance_to_center_km": round(features['DistanceToCenter'], 2),
                "location_zone": features['LocationZone'],
                "has_parking": bool(features['HasParking']),
                "has_energy_star": bool(features['HasENERGYSTAR'])
            },
            "model_performance": {
                "r2_score": 0.677,
                "mae_kbtu": 3237413,
                "note": "Le modèle explique 67.7% de la variance"
            }
        }

    def _compute_features(self, data: dict) -> dict:
        """Calcule toutes les features dérivées"""

        # Temporel
        building_age = 2016 - data['YearBuilt']

        # Localisation
        seattle_center_lat = 47.6062
        seattle_center_lon = -122.3321
        distance = self._haversine_distance(
            data['Latitude'], data['Longitude'],
            seattle_center_lat, seattle_center_lon
        )

        # Structure
        property_gfa_building = data['PropertyGFATotal'] - data.get('PropertyGFAParking', 0)
        parking_ratio = data.get('PropertyGFAParking', 0) / data['PropertyGFATotal']
        avg_floor_area = property_gfa_building / data['NumberofFloors']
        has_parking = 1 if data.get('PropertyGFAParking', 0) > 0 else 0

        # Usages (simplifiés)
        largest_gfa = data['PropertyGFATotal'] * 0.85  # Hypothèse: 85% pour usage principal
        primary_use_ratio = 0.85

        # Performance
        has_energy_star = 1 if data.get('ENERGYSTARScore') is not None else 0
        energy_star_imputed = data.get('ENERGYSTARScore', 50)

        # Interactions
        complexity_score = data['PropertyGFATotal'] * 1
        is_old_large = 1 if (building_age > 50 and data['PropertyGFATotal'] > 50000) else 0

        # Catégories
        age_category = self._get_age_category(building_age)
        location_zone = self._get_location_zone(distance)

        # Déterminer BuildingType et LargestPropertyUseType
        building_type = "NonResidential"
        largest_use_type = data['PrimaryPropertyType']

        return {
            # Numériques
            'PropertyGFATotal': data['PropertyGFATotal'],
            'PropertyGFABuilding(s)': property_gfa_building,
            'PropertyGFAParking': data.get('PropertyGFAParking', 0),
            'NumberofFloors': data['NumberofFloors'],
            'NumberofBuildings': data.get('NumberofBuildings', 1),
            'BuildingAge': building_age,
            'Latitude': data['Latitude'],
            'Longitude': data['Longitude'],
            'DistanceToCenter': distance,
            'LargestPropertyUseTypeGFA': largest_gfa,
            'NumberOfUses': 1,
            'PrimaryUseRatio': primary_use_ratio,
            'SecondUseRatio': 0,
            'ParkingRatio': parking_ratio,
            'AvgFloorArea': avg_floor_area,
            'ENERGYSTARScore_Imputed': energy_star_imputed,
            'ComplexityScore': complexity_score,

            # Binaires
            'HasParking': has_parking,
            'HasMultipleUses': 0,
            'HasSecondUse': 0,
            'HasENERGYSTAR': has_energy_star,
            'IsOldLargeBuilding': is_old_large,

            # Catégorielles
            'BuildingType': building_type,
            'PrimaryPropertyType': data['PrimaryPropertyType'],
            'Neighborhood': data['Neighborhood'],
            'LargestPropertyUseType': largest_use_type,
            'AgeCategory': age_category,
            'LocationZone': location_zone,
        }

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        from math import radians, sin, cos, sqrt, asin
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c

    def _get_age_category(self, age):
        if age <= 20: return "Très récent"
        elif age <= 50: return "Récent"
        elif age <= 80: return "Ancien"
        else: return "Très ancien"

    def _get_location_zone(self, distance):
        if distance <= 2: return "Centre"
        elif distance <= 5: return "Proche"
        else: return "Périphérie"

print("✅ Service corrigé créé : service_complete.py")


