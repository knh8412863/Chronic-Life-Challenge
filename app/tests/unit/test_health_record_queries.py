from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.models.users import Gender
from app.services.predictions import HealthInputService


def test_health_survey_record_response_combines_health_and_lifestyle_input():
    snapshot = SimpleNamespace(
        id=3,
        input_mode="DEEP",
        created_at=datetime(2026, 6, 2, 9, 0),
        chronic_health_input=SimpleNamespace(
            age=30,
            gender=Gender.FEMALE,
            height=Decimal("160.00"),
            weight=Decimal("55.00"),
            bmi=Decimal("21.48"),
            waist_circumference=Decimal("72.50"),
            sbp=120,
            dbp=80,
            glucose_fasting=95,
            diagnosed_diseases=["DIABETES"],
            medications=[],
            last_checkup_period="UNDER_1_YEAR",
            fh_diabetes_father=False,
            fh_diabetes_mother=True,
            fh_diabetes_sibling=False,
            fh_hypertension_father=False,
            fh_hypertension_mother=False,
            fh_hypertension_sibling=False,
            family_history_ckd=False,
        ),
        lifestyle_input=SimpleNamespace(
            smoking_status=0,
            alcohol_frequency=1,
            alcohol_amount=2,
            walking_days=5,
            sedentary_hours=Decimal("6.5"),
            exercise_frequency=3,
            physical_activity_min=150,
            sleep_hours=Decimal("7.0"),
            stress_level=2,
            diet_score=Decimal("8.5"),
        ),
    )

    result = HealthInputService._to_health_survey_record(snapshot)

    assert result.health_input_id == 3
    assert result.gender == "FEMALE"
    assert result.height == 160.0
    assert result.waist_circumference == 72.5
    assert result.diagnosed_diseases == ["DIABETES"]
    assert result.walking_days == 5
    assert result.diet_score == 8.5


def test_lipid_obesity_record_response_converts_decimal_values():
    record = SimpleNamespace(
        id=7,
        record_date=date(2026, 6, 1),
        total_cholesterol=210,
        hdl_cholesterol=55,
        ldl_cholesterol=130,
        triglycerides=160,
        height_cm=Decimal("160.00"),
        weight_kg=Decimal("60.00"),
        bmi=Decimal("23.44"),
        waist_circumference=Decimal("80.00"),
        memo="점심 후 측정",
        created_at=datetime(2026, 6, 1, 12, 0),
        updated_at=datetime(2026, 6, 1, 12, 0),
    )

    result = HealthInputService._to_lipid_obesity_record(record)

    assert result.record_id == 7
    assert result.height == 160.0
    assert result.weight == 60.0
    assert result.bmi == 23.44
    assert result.waist_circumference == 80.0


def test_renal_record_response_converts_decimal_values():
    record = SimpleNamespace(
        id=9,
        record_date=date(2026, 6, 1),
        creatinine=Decimal("1.20"),
        egfr=Decimal("80.50"),
        bun=Decimal("18.00"),
        urine_protein_pos=False,
        memo=None,
        created_at=datetime(2026, 6, 1, 12, 0),
        updated_at=datetime(2026, 6, 1, 12, 0),
    )

    result = HealthInputService._to_renal_record(record)

    assert result.record_id == 9
    assert result.creatinine == 1.2
    assert result.egfr == 80.5
    assert result.bun == 18.0
    assert result.urine_protein_pos is False
