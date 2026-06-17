from app.services.predictions import PredictionService

MODEL_INPUT = {
    "age": 55,
    "sex": 1,
    "education": 3,
    "height": 170,
    "weight": 75,
    "bmi": 25.95,
    "waist_circumference": 88,
    "sbp": 142,
    "dbp": 91,
    "glucose_fasting": 126,
    "total_cholesterol": 210,
    "hdl_cholesterol": 48,
    "ldl_cholesterol": 130,
    "triglycerides": 160,
    "creatinine": 1.0,
    "bun": 16,
    "urine_protein": 0,
    "fh_diabetes_father": 0,
    "fh_diabetes_mother": 1,
    "fh_diabetes_sibling": 0,
    "fh_hypertension_father": 0,
    "fh_hypertension_mother": 1,
    "fh_hypertension_sibling": 0,
    "smoking_status": 8,
    "alcohol_frequency": 3,
    "alcohol_amount": 0,
    "walking_days": 3,
    "sedentary_hours": 7,
}


def test_prediction_models_return_stable_results_for_same_input():
    baseline = PredictionService._run_models(MODEL_INPUT)

    for _ in range(5):
        assert PredictionService._run_models(MODEL_INPUT) == baseline
