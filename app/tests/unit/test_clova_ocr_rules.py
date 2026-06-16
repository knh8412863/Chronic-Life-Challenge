from app.services.clova_ocr import ClovaOcrService
from app.services.ocr_gauge import GaugeBox, extract_gauge_results


def _ocr_cell(text: str, col: int, row: int, *, cw: int = 140, rh: int = 36) -> dict:
    x_min = 20 + col * cw
    y_min = 20 + row * rh
    x_max = x_min + cw - 10
    y_max = y_min + rh - 8
    return {
        "inferText": text,
        "boundingPoly": {
            "vertices": [
                {"x": x_min, "y": y_min},
                {"x": x_max, "y": y_min},
                {"x": x_max, "y": y_max},
                {"x": x_min, "y": y_max},
            ]
        },
    }


def _ocr_rows(fields: list[dict]):
    return ClovaOcrService._extract_rows({"images": [{"fields": fields}]})


def test_clova_ocr_parser_extracts_health_checkup_values():
    text = """
    혈압 145/92 mmHg
    공복혈당 126 mg/dL
    총 콜레스테롤 230
    HDL 콜레스테롤 45
    LDL 콜레스테롤 150
    중성지방 180
    혈청 크레아티닌 1.4
    eGFR 58
    BUN 22
    요단백 양성
    """

    result = ClovaOcrService._parse_health_checkup_text(text)

    assert result["vitals"]["sbp"] == 145
    assert result["vitals"]["dbp"] == 92
    assert result["vitals"]["glucose_fasting"] == 126
    assert result["lipid"]["total_cholesterol"] == 230
    assert result["lipid"]["hdl_cholesterol"] == 45
    assert result["lipid"]["ldl_cholesterol"] == 150
    assert result["lipid"]["triglycerides"] == 180
    assert result["renal"]["creatinine"] == 1.4
    assert result["renal"]["egfr"] == 58
    assert result["renal"]["bun"] == 22
    assert result["renal"]["urine_protein_pos"] is True


def test_clova_ocr_parser_ignores_out_of_range_values():
    text = "공복혈당 9999 총 콜레스테롤 20 혈압 300/10"

    result = ClovaOcrService._parse_health_checkup_text(text)

    assert result["vitals"] == {}
    assert result["lipid"] == {}


def test_clova_ocr_parser_matches_korean_and_english_aliases():
    text = """
    식전혈당(FBS)
    121
    저밀도 콜레스테롤
    162
    고밀도 콜레스테롤
    39
    트리글리세라이드
    220
    단백뇨 음성
    """

    result = ClovaOcrService._parse_health_checkup_text(text)

    assert result["vitals"]["glucose_fasting"] == 121
    assert result["lipid"]["ldl_cholesterol"] == 162
    assert result["lipid"]["hdl_cholesterol"] == 39
    assert result["lipid"]["triglycerides"] == 220
    assert result["renal"]["urine_protein_pos"] is False


def test_clova_ocr_parser_does_not_use_not_applicable_or_reference_lipid_values():
    text = """
    총 콜레스테롤 비해당
    정상 기준 200 미만
    저밀도 콜레스테롤 해당 없음
    정상 범위 130 미만
    고밀도 콜레스테롤 미실시
    정상 60 이상
    중성지방 검사 안함
    참고치 150 미만
    공복혈당 121
    """

    result = ClovaOcrService._parse_health_checkup_text(text)

    assert result["lipid"] == {}
    assert result["vitals"]["glucose_fasting"] == 121


def test_clova_ocr_parser_scales_food_nutrition_per_100g_to_total_amount():
    text = """
    제품명 단백질바
    총 내용량 140g
    100g당
    열량 250 kcal
    탄수화물 30 g
    단백질 12 g
    지방 8 g
    나트륨 200 mg
    당류 10 g
    식이섬유 4 g
    """

    result = ClovaOcrService._parse_food_nutrition_text(text)

    assert result["food_name"] == "단백질바"
    assert result["serving_basis"] == "PER_100G"
    assert result["total_amount_g"] == 140
    assert result["nutrition"]["calories"] == 350
    assert result["nutrition"]["carbs_g"] == 42
    assert result["nutrition"]["protein_g"] == 16.8
    assert result["nutrition"]["fat_g"] == 11.2
    assert result["nutrition"]["sodium_mg"] == 280
    assert result["nutrition"]["sugar_g"] == 14
    assert result["nutrition"]["fiber_g"] == 5.6


def test_clova_ocr_parser_scales_food_nutrition_per_custom_gram_to_total_amount():
    text = """
    제품명 그래놀라바
    총 내용량 90g
    30g당 기준
    열량 120 kcal
    탄수화물 20 g
    단백질 3 g
    지방 4 g
    나트륨 80 mg
    당류 7 g
    """

    result = ClovaOcrService._parse_food_nutrition_text(text)

    assert result["food_name"] == "그래놀라바"
    assert result["serving_basis"] == "PER_AMOUNT_G"
    assert result["total_amount_g"] == 90
    assert result["basis_amount_g"] == 30
    assert result["nutrition"]["calories"] == 360
    assert result["nutrition"]["carbs_g"] == 60
    assert result["nutrition"]["protein_g"] == 9
    assert result["nutrition"]["fat_g"] == 12
    assert result["nutrition"]["sodium_mg"] == 240
    assert result["nutrition"]["sugar_g"] == 21


def test_clova_ocr_parser_prefers_custom_gram_column_when_100g_column_also_exists():
    text = """
    총 내용량 155g
    30g당 140 kcal
    100g당
    나트륨 210mg 11% 690mg 35%
    탄수화물 22g 7% 73g 23%
    당류 2g 2% 7g 7%
    식이섬유 2g 8% 6g 24%
    지방 6g 11% 20g 37%
    트랜스지방 0g 0g
    포화지방 1.9g 13% 6g 40%
    콜레스테롤 0mg 0% 0mg 0%
    단백질 1g 2% 3g 5%
    """

    result = ClovaOcrService._parse_food_nutrition_text(text)

    assert result["serving_basis"] == "PER_AMOUNT_G"
    assert result["total_amount_g"] == 155
    assert result["basis_amount_g"] == 30
    assert result["nutrition"]["calories"] == 723
    assert result["nutrition"]["sodium_mg"] == 1085
    assert result["nutrition"]["carbs_g"] == 113.67
    assert result["nutrition"]["sugar_g"] == 10.33
    assert result["nutrition"]["fiber_g"] == 10.33
    assert result["nutrition"]["fat_g"] == 31
    assert result["nutrition"]["protein_g"] == 5.17


def test_clova_ocr_parser_does_not_treat_small_nutrient_grams_as_serving_basis():
    text = """
    제품명 과자
    100g당
    열량 595 kcal
    탄수화물 86 g
    단백질 12 g
    지방 20 g
    나트륨 0 mg
    당류 12 g
    식이섬유 11 g
    """

    result = ClovaOcrService._parse_food_nutrition_text(text)

    assert result["serving_basis"] == "PER_100G"
    assert result["basis_amount_g"] == 100
    assert result["nutrition"]["calories"] == 595
    assert result["nutrition"]["carbs_g"] == 86
    assert result["nutrition"]["protein_g"] == 12
    assert result["nutrition"]["fat_g"] == 20
    assert result["nutrition"]["sodium_mg"] == 0
    assert result["nutrition"]["sugar_g"] == 12
    assert result["nutrition"]["fiber_g"] == 11


def test_clova_ocr_row_parser_prefers_result_over_reference_range():
    rows = _ocr_rows(
        [
            _ocr_cell("검사항목", 0, 0),
            _ocr_cell("참고치", 1, 0),
            _ocr_cell("결과", 2, 0),
            _ocr_cell("공복혈당", 0, 1),
            _ocr_cell("70~100", 1, 1),
            _ocr_cell("126", 2, 1),
            _ocr_cell("총콜레스테롤", 0, 2),
            _ocr_cell("0~200", 1, 2),
            _ocr_cell("230", 2, 2),
        ]
    )

    result = ClovaOcrService._parse_health_checkup_rows(rows, ClovaOcrService._layout_text(rows))

    assert result["vitals"]["glucose_fasting"] == 126
    assert result["lipid"]["total_cholesterol"] == 230


def test_clova_ocr_row_parser_converts_nutrition_units_and_excludes_percent():
    rows = _ocr_rows(
        [
            _ocr_cell("총 내용량 90g", 0, 0),
            _ocr_cell("30g당 기준", 1, 0),
            _ocr_cell("나트륨", 0, 1),
            _ocr_cell("0.12g", 1, 1),
            _ocr_cell("6%", 2, 1),
            _ocr_cell("탄수화물", 0, 2),
            _ocr_cell("20g", 1, 2),
            _ocr_cell("7%", 2, 2),
        ]
    )

    result = ClovaOcrService._parse_food_nutrition_rows(rows, ClovaOcrService._layout_text(rows))

    assert result["serving_basis"] == "PER_AMOUNT_G"
    assert result["total_amount_g"] == 90
    assert result["basis_amount_g"] == 30
    assert result["nutrition"]["sodium_mg"] == 360
    assert result["nutrition"]["carbs_g"] == 60


def test_clova_ocr_parser_extracts_unlabeled_kcal_and_parenthesized_basis_without_total_scaling():
    text = """
    총 내용량 372g
    1개당 (31 g) 당
    139 kcal
    나트륨 80 mg
    탄수화물 18 g
    단백질 2 g
    지방 5 g
    """

    result = ClovaOcrService._parse_food_nutrition_text(text)

    assert result["serving_basis"] == "PER_AMOUNT_G"
    assert result["basis_amount_g"] == 31
    assert result["nutrition"]["calories"] == 139
    assert result["nutrition"]["sodium_mg"] == 80
    assert result["nutrition"]["carbs_g"] == 18


def test_clova_ocr_parser_uses_unit_anchor_when_percent_appears_before_value():
    text = """
    총 내용량 1개
    400 kcal
    탄수화물 17 % 56 g
    단백질 8 g 15 %
    지방 11 % 7 g
    나트륨 18 % 640 mg
    당류 8 % 8 g
    """

    result = ClovaOcrService._parse_food_nutrition_text(text)

    assert result["nutrition"]["calories"] == 400
    assert result["nutrition"]["carbs_g"] == 56
    assert result["nutrition"]["protein_g"] == 8
    assert result["nutrition"]["fat_g"] == 7
    assert result["nutrition"]["sodium_mg"] == 640
    assert result["nutrition"]["sugar_g"] == 8


def test_gauge_results_match_value_box_to_label_by_y_axis():
    fields = [
        ClovaOcrService._extract_fields(
            {
                "images": [
                    {
                        "fields": [
                            _ocr_cell("총콜레스테롤", 0, 0),
                            _ocr_cell("199", 2, 0),
                            _ocr_cell("공복혈당", 0, 1),
                            _ocr_cell("95", 2, 1),
                        ]
                    }
                ]
            }
        )
    ][0]
    boxes = [
        GaugeBox(x_min=295, y_min=18, x_max=355, y_max=52),
        GaugeBox(x_min=295, y_min=54, x_max=355, y_max=88),
    ]

    result = extract_gauge_results(
        boxes,
        fields,
        [
            ("total_cholesterol", [r"총\s*콜레스테롤"]),
            ("glucose_fasting", [r"공복\s*혈당"]),
        ],
    )

    assert result == {"total_cholesterol": 199, "glucose_fasting": 95}
