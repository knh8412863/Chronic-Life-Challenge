import base64
import re
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core import config
from app.dtos.foods import FoodNutritionOcrResponse, FoodNutritionResponse
from app.dtos.predictions import (
    HealthCheckupOcrActivityResponse,
    HealthCheckupOcrLipidResponse,
    HealthCheckupOcrRenalResponse,
    HealthCheckupOcrResponse,
    HealthCheckupOcrVitalsResponse,
)
from app.services import ocr_gauge

SUPPORTED_FORMATS = {
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".png": "png",
    ".pdf": "pdf",
}
MAX_OCR_FILE_SIZE_BYTES = 10 * 1024 * 1024
NO_RESULT_PATTERN = re.compile(
    r"비\s*해당|해당\s*없음|미\s*실시|미\s*측정|검사\s*안함|검사\s*없음|"
    r"not\s*applicable|\bn/?a\b",
    flags=re.IGNORECASE,
)
REFERENCE_VALUE_PATTERN = re.compile(
    r"참고\s*치|기준\s*치|정상\s*범위|판정\s*기준|정상\s*[:：]?\s*\d|"
    r"reference\s*range|normal\s*range",
    flags=re.IGNORECASE,
)
PRODUCT_INFO_PATTERN = re.compile(
    r"제품\s*명|품\s*명|식품\s*명|상품\s*명|food\s*name|product\s*name",
    flags=re.IGNORECASE,
)
OCR_RANGE_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*[~∼〜\-–—]\s*\d+(?:\.\d+)?")
OCR_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
OCR_PERCENT_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*%")
OCR_UNIT_TO_BASE = {
    "kcal": ("kcal", 1.0),
    "g": ("g", 1.0),
    "mg": ("mg", 1.0),
    "mcg": ("mg", 0.001),
    "ug": ("mg", 0.001),
    "µg": ("mg", 0.001),
}
HEALTH_GAUGE_LABEL_SPECS = [
    ("glucose_fasting", [r"공복\s*혈당", r"식전\s*혈당", r"fasting\s*glucose", r"\bfbs\b"]),
    ("total_cholesterol", [r"총\s*콜레스테롤", r"total\s*cholesterol", r"\btc\b"]),
    ("hdl_cholesterol", [r"\bhdl\b", r"hdl\s*콜레스테롤", r"고밀도\s*콜레스테롤"]),
    ("ldl_cholesterol", [r"\bldl\b", r"ldl\s*콜레스테롤", r"저밀도\s*콜레스테롤"]),
    ("triglycerides", [r"중성\s*지방", r"triglyceride", r"\btg\b"]),
    ("creatinine", [r"크레아티닌", r"creatinine"]),
    ("egfr", [r"\begfr\b", r"사구체\s*여과율"]),
    ("bun", [r"\bbun\b", r"요소\s*질소"]),
]
HEALTH_GAUGE_FIELD_SECTIONS = {
    "glucose_fasting": "vitals",
    "total_cholesterol": "lipid",
    "hdl_cholesterol": "lipid",
    "ldl_cholesterol": "lipid",
    "triglycerides": "lipid",
    "creatinine": "renal",
    "egfr": "renal",
    "bun": "renal",
}


@dataclass
class OcrField:
    text: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def y_center(self) -> float:
        return (self.y_min + self.y_max) / 2

    @property
    def height(self) -> float:
        return max(self.y_max - self.y_min, 0.0)


class ClovaOcrService:
    async def analyze_food_nutrition_label_file(
        self,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> FoodNutritionOcrResponse:
        self._validate_ocr_settings_and_file(content)
        image_format = self._detect_format(file_name, content_type)
        raw_response = await self._request_clova_ocr(file_name, image_format, content)
        fields = self._extract_fields(raw_response)
        rows = self._group_rows(fields)
        extracted_text = self._layout_text(rows) or self._extract_text(raw_response)
        parsed = self._parse_food_nutrition_rows(rows, extracted_text)
        return FoodNutritionOcrResponse(
            file_name=file_name,
            content_type=content_type,
            extracted_text=extracted_text,
            food_name=parsed["food_name"],
            amount=parsed["amount"],
            serving_basis=parsed["serving_basis"],
            total_amount_g=parsed["total_amount_g"],
            basis_amount_g=parsed["basis_amount_g"],
            serving_amount_g=parsed["serving_amount_g"],
            nutrition=FoodNutritionResponse(**parsed["nutrition"]),
            matched_fields=parsed["matched_fields"],
        )

    async def analyze_health_checkup_file(
        self,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> HealthCheckupOcrResponse:
        self._validate_ocr_settings_and_file(content)
        image_format = self._detect_format(file_name, content_type)
        raw_response = await self._request_clova_ocr(file_name, image_format, content)
        fields = self._extract_fields(raw_response)
        rows = self._group_rows(fields)
        extracted_text = self._layout_text(rows) or self._extract_text(raw_response)
        parsed = self._parse_health_checkup_rows(rows, extracted_text)
        boxes = ocr_gauge.detect_red_value_boxes(content)
        if ocr_gauge.is_gauge_form(boxes):
            gauge_results = ocr_gauge.extract_gauge_results(boxes, fields, HEALTH_GAUGE_LABEL_SPECS)
            if gauge_results:
                parsed = self._merge_gauge_health_results(parsed, gauge_results)
        return HealthCheckupOcrResponse(
            file_name=file_name,
            content_type=content_type,
            extracted_text=extracted_text,
            vitals=HealthCheckupOcrVitalsResponse(**parsed["vitals"]),
            lipid=HealthCheckupOcrLipidResponse(**parsed["lipid"]),
            renal=HealthCheckupOcrRenalResponse(**parsed["renal"]),
            activity=HealthCheckupOcrActivityResponse(**parsed["activity"]),
            matched_fields=parsed["matched_fields"],
        )

    @staticmethod
    def _validate_ocr_settings_and_file(content: bytes) -> None:
        if not config.CLOVA_OCR_INVOKE_URL or not config.CLOVA_OCR_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Clova OCR 설정이 없습니다. CLOVA_OCR_INVOKE_URL과 CLOVA_OCR_SECRET_KEY를 확인해주세요.",
            )
        if not content:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="파일 내용이 비어 있습니다.")
        if len(content) > MAX_OCR_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="OCR 파일은 10MB 이하만 업로드할 수 있습니다.",
            )

    @staticmethod
    def _detect_format(file_name: str, content_type: str) -> str:
        suffix = Path(file_name).suffix.lower()
        if suffix in SUPPORTED_FORMATS:
            return SUPPORTED_FORMATS[suffix]
        if content_type in {"image/jpeg", "image/jpg"}:
            return "jpg"
        if content_type == "image/png":
            return "png"
        if content_type == "application/pdf":
            return "pdf"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="지원하지 않는 파일 형식입니다. PDF, JPG, PNG 파일만 업로드할 수 있습니다.",
        )

    async def _request_clova_ocr(self, file_name: str, image_format: str, content: bytes) -> dict[str, Any]:
        payload = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "images": [
                {
                    "format": image_format,
                    "name": Path(file_name).stem or "health-checkup",
                    "data": base64.b64encode(content).decode("ascii"),
                }
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "X-OCR-SECRET": config.CLOVA_OCR_SECRET_KEY,
        }
        try:
            async with httpx.AsyncClient(timeout=config.CLOVA_OCR_TIMEOUT_SECONDS) as client:
                response = await client.post(config.CLOVA_OCR_INVOKE_URL, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Clova OCR 요청에 실패했습니다. status={exc.response.status_code}",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Clova OCR 서버와 통신하지 못했습니다.",
            ) from exc
        return response.json()

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        texts: list[str] = []
        for image in payload.get("images", []):
            for field in image.get("fields", []):
                text = str(field.get("inferText") or "").strip()
                if text:
                    texts.append(text)
        return "\n".join(texts)

    @staticmethod
    def _extract_rows(payload: dict[str, Any]) -> list[list[OcrField]]:
        return ClovaOcrService._group_rows(ClovaOcrService._extract_fields(payload))

    @staticmethod
    def _extract_fields(payload: dict[str, Any]) -> list[OcrField]:
        fields: list[OcrField] = []
        for image in payload.get("images", []):
            for field in image.get("fields", []):
                text = str(field.get("inferText") or "").strip()
                if not text:
                    continue
                vertices = (field.get("boundingPoly") or {}).get("vertices") or []
                xs = [float(vertex.get("x", 0) or 0) for vertex in vertices]
                ys = [float(vertex.get("y", 0) or 0) for vertex in vertices]
                if not xs or not ys:
                    fields.append(OcrField(text=text, x_min=0, y_min=1e9, x_max=0, y_max=1e9))
                    continue
                fields.append(
                    OcrField(
                        text=text,
                        x_min=min(xs),
                        y_min=min(ys),
                        x_max=max(xs),
                        y_max=max(ys),
                    )
                )
        return fields

    @staticmethod
    def _group_rows(fields: list[OcrField], line_ratio: float = 0.6) -> list[list[OcrField]]:
        if not fields:
            return []
        ordered = sorted(fields, key=lambda field: (field.y_center, field.x_min))
        heights = sorted(field.height for field in ordered if field.height > 0)
        median_height = heights[len(heights) // 2] if heights else 1.0
        threshold = max(median_height * line_ratio, 1.0)

        rows: list[list[OcrField]] = [[ordered[0]]]
        for field in ordered[1:]:
            current_y = sum(row_field.y_center for row_field in rows[-1]) / len(rows[-1])
            if abs(field.y_center - current_y) <= threshold:
                rows[-1].append(field)
            else:
                rows.append([field])
        for row in rows:
            row.sort(key=lambda field: field.x_min)
        return rows

    @staticmethod
    def _row_text(row: list[OcrField]) -> str:
        return " ".join(field.text for field in row)

    @staticmethod
    def _layout_text(rows: list[list[OcrField]]) -> str:
        return "\n".join(ClovaOcrService._row_text(row) for row in rows)

    @staticmethod
    def _parse_health_checkup_text(text: str) -> dict[str, Any]:
        return ClovaOcrService._parse_health_checkup(normalized=ClovaOcrService._normalize_text(text), rows=None)

    @staticmethod
    def _parse_health_checkup_rows(rows: list[list[OcrField]], extracted_text: str) -> dict[str, Any]:
        return ClovaOcrService._parse_health_checkup(
            normalized=ClovaOcrService._normalize_text(extracted_text),
            rows=rows,
        )

    @staticmethod
    def _parse_health_checkup(normalized: str, rows: list[list[OcrField]] | None) -> dict[str, Any]:
        parsed: dict[str, Any] = {
            "vitals": {},
            "lipid": {},
            "renal": {},
            "activity": {},
            "matched_fields": [],
        }

        bp = ClovaOcrService._extract_blood_pressure_from_rows(rows) if rows else None
        bp = bp or ClovaOcrService._extract_blood_pressure(normalized)
        if bp:
            parsed["vitals"].update(bp)
            parsed["matched_fields"].extend(bp.keys())

        field_specs = [
            (
                "vitals",
                "glucose_fasting",
                [
                    r"공복\s*혈당",
                    r"식전\s*혈당",
                    r"혈당\s*\(\s*식전\s*\)",
                    r"혈당\s*\(\s*공복\s*\)",
                    r"fasting\s*glucose",
                    r"fasting\s*blood\s*sugar",
                    r"glucose\s*\(\s*fasting\s*\)",
                    r"\bfbs\b",
                ],
                40,
                500,
                int,
            ),
            (
                "vitals",
                "glucose_postprandial",
                [
                    r"식후\s*혈당",
                    r"혈당\s*\(\s*식후\s*\)",
                    r"postprandial\s*glucose",
                    r"postprandial\s*blood\s*sugar",
                    r"\bppbs\b",
                ],
                40,
                500,
                int,
            ),
            (
                "lipid",
                "total_cholesterol",
                [r"총\s*콜레스테롤", r"총\s*콜레스테롤\s*\(total\)", r"total\s*cholesterol", r"\btc\b"],
                80,
                400,
                int,
            ),
            (
                "lipid",
                "ldl_cholesterol",
                [
                    r"\bldl\b",
                    r"ldl\s*[-]?\s*c",
                    r"ldl\s*콜레스테롤",
                    r"저밀도\s*콜레스테롤",
                    r"저밀도\s*지단백",
                    r"low\s*density\s*lipoprotein",
                ],
                30,
                300,
                int,
            ),
            (
                "lipid",
                "hdl_cholesterol",
                [
                    r"\bhdl\b",
                    r"hdl\s*[-]?\s*c",
                    r"hdl\s*콜레스테롤",
                    r"고밀도\s*콜레스테롤",
                    r"고밀도\s*지단백",
                    r"high\s*density\s*lipoprotein",
                ],
                10,
                120,
                int,
            ),
            (
                "lipid",
                "triglycerides",
                [r"중성\s*지방", r"트리글리세라이드", r"triglyceride", r"\btg\b"],
                30,
                1000,
                int,
            ),
            ("lipid", "waist_circumference", [r"허리\s*둘레", r"waist"], 50, 150, float),
            ("lipid", "height", [r"\b키\b", r"신장\s*\(cm\)", r"height"], 130, 210, float),
            ("lipid", "weight", [r"몸무게", r"체중", r"weight"], 30, 200, float),
            ("renal", "creatinine", [r"크레아티닌", r"creatinine"], 0.1, 20, float),
            ("renal", "egfr", [r"\begfr\b", r"사구체\s*여과율"], 0, 200, float),
            ("renal", "bun", [r"\bbun\b", r"요소\s*질소"], 0, 200, float),
            ("activity", "steps", [r"걸음\s*수", r"steps"], 0, 100000, int),
            ("activity", "exercise_minutes", [r"운동\s*시간", r"exercise\s*minutes"], 0, 1440, int),
            ("activity", "water_ml", [r"물\s*섭취", r"수분\s*섭취", r"water"], 0, 10000, int),
            ("activity", "sleep_hours", [r"수면\s*시간", r"sleep"], 0, 24, float),
        ]
        for section, field_name, labels, minimum, maximum, caster in field_specs:
            value = ClovaOcrService._find_labeled_row_value(rows, labels, minimum, maximum, caster) if rows else None
            value = (
                value
                if value is not None
                else ClovaOcrService._find_labeled_number(normalized, labels, minimum, maximum, caster)
            )
            if value is not None:
                parsed[section][field_name] = value
                parsed["matched_fields"].append(field_name)

        urine_protein = ClovaOcrService._extract_urine_protein_from_rows(rows) if rows else None
        urine_protein = (
            urine_protein if urine_protein is not None else ClovaOcrService._extract_urine_protein(normalized)
        )
        if urine_protein is not None:
            parsed["renal"]["urine_protein_pos"] = urine_protein
            parsed["matched_fields"].append("urine_protein_pos")

        return parsed

    @staticmethod
    def _merge_gauge_health_results(parsed: dict[str, Any], gauge_results: dict[str, int | float]) -> dict[str, Any]:
        for field_name, value in gauge_results.items():
            section = HEALTH_GAUGE_FIELD_SECTIONS.get(field_name)
            if not section:
                continue
            parsed[section][field_name] = value
            if field_name not in parsed["matched_fields"]:
                parsed["matched_fields"].append(field_name)
        return parsed

    @staticmethod
    def _parse_food_nutrition_text(text: str) -> dict[str, Any]:
        return ClovaOcrService._parse_food_nutrition(
            normalized=ClovaOcrService._normalize_text(text),
            rows=None,
        )

    @staticmethod
    def _parse_food_nutrition_rows(rows: list[list[OcrField]], extracted_text: str) -> dict[str, Any]:
        return ClovaOcrService._parse_food_nutrition(
            normalized=ClovaOcrService._normalize_text(extracted_text),
            rows=rows,
        )

    @staticmethod
    def _parse_food_nutrition(normalized: str, rows: list[list[OcrField]] | None) -> dict[str, Any]:
        total_amount_g = ClovaOcrService._extract_amount_g(
            normalized,
            [
                r"총\s*내용량",
                r"총\s*용량",
                r"내용량",
                r"제품\s*중량",
                r"net\s*weight",
                r"total\s*weight",
            ],
        )
        serving_amount_g = ClovaOcrService._extract_amount_g(
            normalized,
            [
                r"1\s*회\s*제공량",
                r"1\s*회\s*분량",
                r"제공량",
                r"serving\s*size",
            ],
        )
        serving_basis, basis_amount_g = ClovaOcrService._detect_food_serving_basis(normalized)
        scale = ClovaOcrService._nutrition_scale(serving_basis, total_amount_g, serving_amount_g, basis_amount_g)
        if ClovaOcrService._is_single_unit_basis(normalized):
            scale = 1

        raw_nutrition_specs = [
            ("calories", [r"열량", r"칼로리", r"calories?", r"energy"], "kcal", 0, 3000, int),
            ("carbs_g", [r"탄수화물", r"carbohydrates?", r"\bcarbs?\b"], "g", 0, 500, float),
            ("protein_g", [r"단백질(?![가-힣])", r"protein"], "g", 0, 300, float),
            (
                "fat_g",
                [r"총\s*지방", r"(?<!포화)(?<!트랜스)(?<!불포화)지방", r"total\s*fat", r"\bfat\b"],
                "g",
                0,
                300,
                float,
            ),
            ("sodium_mg", [r"나트륨", r"sodium"], "mg", 0, 100000, float),
            ("sugar_g", [r"당류", r"당\s*류", r"(?<!첨가)당류", r"sugars?", r"total\s*sugars?"], "g", 0, 300, float),
            ("fiber_g", [r"식이\s*섬유", r"식이섬유", r"dietary\s*fiber", r"fiber"], "g", 0, 100, float),
        ]
        nutrition: dict[str, int | float] = {}
        matched_fields: list[str] = []
        for field_name, labels, expected_unit, minimum, maximum, caster in raw_nutrition_specs:
            if field_name == "calories":
                value = ClovaOcrService._extract_calories_kcal(normalized)
            else:
                value = (
                    ClovaOcrService._find_nutrition_row_value(rows, labels, expected_unit, minimum, maximum, caster)
                    if rows
                    else None
                )
                value = (
                    value
                    if value is not None
                    else ClovaOcrService._find_nutrient_value(normalized, labels, expected_unit, minimum, maximum)
                )
            if value is None and field_name == "calories":
                value = ClovaOcrService._extract_basis_calories(normalized, serving_basis, basis_amount_g)
            if value is None:
                continue
            scaled_value = ClovaOcrService._apply_nutrition_scale(value, scale, caster)
            nutrition[field_name] = scaled_value
            matched_fields.append(field_name)

        if total_amount_g is not None:
            matched_fields.append("total_amount_g")
        if serving_amount_g is not None:
            matched_fields.append("serving_amount_g")
        if basis_amount_g is not None:
            matched_fields.append("basis_amount_g")

        return {
            "food_name": ClovaOcrService._extract_food_name(normalized),
            "amount": ClovaOcrService._build_food_amount_text(
                total_amount_g, serving_amount_g, serving_basis, basis_amount_g
            ),
            "serving_basis": serving_basis,
            "total_amount_g": total_amount_g,
            "basis_amount_g": basis_amount_g,
            "serving_amount_g": serving_amount_g,
            "nutrition": nutrition,
            "matched_fields": matched_fields,
        }

    @staticmethod
    def _detect_food_serving_basis(text: str) -> tuple[str, float | None]:
        basis_amount_g = ClovaOcrService._extract_basis_amount_g(text)
        if basis_amount_g is not None and basis_amount_g != 100:
            return "PER_AMOUNT_G", basis_amount_g
        if re.search(r"100\s*g\s*(?:당|기준|per)|per\s*100\s*g", text, flags=re.IGNORECASE):
            return "PER_100G", 100
        if re.search(r"(?:총\s*내용량|총\s*용량|제품\s*전체|총량)\s*(?:당|기준)", text, flags=re.IGNORECASE):
            return "TOTAL", None
        if re.search(r"1\s*회\s*(?:제공량|분량)\s*(?:당|기준)|per\s*serving", text, flags=re.IGNORECASE):
            return "PER_SERVING", None
        return "UNKNOWN", None

    @staticmethod
    def _nutrition_scale(
        serving_basis: str,
        total_amount_g: float | None,
        serving_amount_g: float | None,
        basis_amount_g: float | None,
    ) -> float:
        if serving_basis == "PER_100G" and total_amount_g:
            return total_amount_g / 100
        if serving_basis == "PER_AMOUNT_G" and total_amount_g and basis_amount_g:
            return total_amount_g / basis_amount_g
        if serving_basis == "PER_SERVING" and total_amount_g and serving_amount_g:
            return total_amount_g / serving_amount_g
        return 1

    @staticmethod
    def _extract_basis_amount_g(text: str) -> float | None:
        patterns = [
            r"(?:^|[^\d])([1-9]\d{1,2}(?:\.\d+)?)\s*g\s*[)\]]?\s*(?:당|기준|per)",
            r"per\s*([1-9]\d{1,2}(?:\.\d+)?)\s*g",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            value = round(float(match.group(1)), 2)
            if 10 <= value <= 999:
                return value
        return None

    @staticmethod
    def _is_single_unit_basis(text: str) -> bool:
        return bool(
            re.search(r"(?:1\s*)?(?:개|봉|봉지|팩|회|serving)\s*(?:당|기준)|per\s*serving", text, flags=re.IGNORECASE)
        )

    @staticmethod
    def _extract_calories_kcal(text: str) -> int | None:
        match = re.search(r"(?:열량|칼로리|에너지)[^\d]{0,10}(\d+(?:\.\d+)?)\s*kcal", text, re.IGNORECASE)
        if match:
            return int(round(float(match.group(1))))
        match = re.search(r"(\d+(?:\.\d+)?)\s*kcal", text, re.IGNORECASE)
        return int(round(float(match.group(1)))) if match else None

    @staticmethod
    def _find_nutrient_value(
        text: str,
        labels: list[str],
        unit: str,
        minimum: float,
        maximum: float,
    ) -> float | None:
        label_pattern = "|".join(labels)
        unit_pattern = re.escape(unit)
        unit_value_pattern = (
            rf"(?:{label_pattern})(?:(?!\n).){{0,80}}?"
            rf"(\d+(?:\.\d+)?)\s*{unit_pattern}(?![a-zA-Z가-힣%])"
        )
        value = ClovaOcrService._find_valid_nutrient_match(text, unit_value_pattern, minimum, maximum)
        if value is not None:
            return value

        loose_value_pattern = rf"(?:{label_pattern})(?:(?!\n).){{0,80}}?(\d+(?:\.\d+)?)(?!\s*%)"
        return ClovaOcrService._find_valid_nutrient_match(text, loose_value_pattern, minimum, maximum)

    @staticmethod
    def _find_valid_nutrient_match(text: str, pattern: str, minimum: float, maximum: float) -> float | None:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = float(match.group(1))
            if minimum <= value <= maximum:
                return value
        return None

    @staticmethod
    def _extract_basis_calories(text: str, serving_basis: str, basis_amount_g: float | None) -> int | None:
        if serving_basis == "PER_AMOUNT_G" and basis_amount_g is not None:
            amount = re.escape(ClovaOcrService._format_amount(basis_amount_g))
            patterns = [
                rf"{amount}\s*g\s*(?:당|기준)?[^\d]{{0,20}}(\d+(?:\.\d+)?)\s*kcal",
                rf"(\d+(?:\.\d+)?)\s*kcal[^\n]{{0,20}}{amount}\s*g\s*(?:당|기준)?",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    return int(round(float(match.group(1))))
        return None

    @staticmethod
    def _apply_nutrition_scale(value: int | float, scale: float, caster: type[int] | type[float]) -> int | float:
        scaled = float(value) * scale
        if caster is int:
            return int(round(scaled))
        return round(scaled, 2)

    @staticmethod
    def _extract_amount_g(text: str, labels: list[str]) -> float | None:
        label_pattern = "|".join(labels)
        patterns = [
            rf"(?:{label_pattern})[^\d]{{0,30}}(\d+(?:\.\d+)?)\s*(?:g|그램|㎖|ml)",
            rf"(\d+(?:\.\d+)?)\s*(?:g|그램|㎖|ml)[^\n]{{0,20}}(?:{label_pattern})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                return round(float(match.group(1)), 2)
        return None

    @staticmethod
    def _extract_food_name(text: str) -> str | None:
        patterns = [
            r"(?:제품명|품명|식품명|food\s*name|product\s*name)[^\w가-힣]{0,10}([가-힣A-Za-z0-9][^\n]{1,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = re.sub(r"\s+", " ", match.group(1)).strip(" :-")
                return value[:40] if value else None
        return None

    @staticmethod
    def _build_food_amount_text(
        total_amount_g: float | None,
        serving_amount_g: float | None,
        serving_basis: str,
        basis_amount_g: float | None,
    ) -> str | None:
        parts: list[str] = []
        if total_amount_g is not None:
            parts.append(f"총 {ClovaOcrService._format_amount(total_amount_g)}g")
        if serving_basis == "PER_100G":
            parts.append("100g당 기준 환산")
        elif serving_basis == "PER_AMOUNT_G" and basis_amount_g is not None:
            parts.append(f"{ClovaOcrService._format_amount(basis_amount_g)}g당 기준 환산")
        elif serving_basis == "PER_SERVING" and serving_amount_g is not None:
            parts.append(f"1회 제공량 {ClovaOcrService._format_amount(serving_amount_g)}g 기준 환산")
        elif serving_basis == "UNKNOWN":
            parts.append("기준 단위 확인 필요")
        return ", ".join(parts) if parts else None

    @staticmethod
    def _format_amount(value: float) -> str:
        return str(int(value)) if float(value).is_integer() else str(value)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"[ \t]+", " ", text.replace("：", ":")).strip()

    @staticmethod
    def _classify_ocr_token(text: str) -> str:
        if OCR_RANGE_PATTERN.search(text):
            return "range"
        if OCR_PERCENT_PATTERN.fullmatch(text.strip()):
            return "percent"
        if (
            OCR_PERCENT_PATTERN.search(text)
            and not OCR_NUMBER_PATTERN.sub("", OCR_PERCENT_PATTERN.sub("", text)).strip()
        ):
            return "percent"
        if OCR_NUMBER_PATTERN.search(text):
            return "number"
        return "other"

    @staticmethod
    def _label_right_edge(row: list[OcrField], label_re: re.Pattern[str]) -> float | None:
        matched = [field for field in row if label_re.search(field.text)]
        if matched:
            return max(field.x_max for field in matched)
        return row[0].x_max if row else None

    @staticmethod
    def _find_labeled_row_value(
        rows: list[list[OcrField]],
        labels: list[str],
        minimum: float,
        maximum: float,
        caster: Callable[[float], int | float],
    ) -> int | float | None:
        label_re = re.compile("|".join(labels), flags=re.IGNORECASE)
        for row in rows:
            if not label_re.search(ClovaOcrService._row_text(row)):
                continue
            label_x = ClovaOcrService._label_right_edge(row, label_re)
            if label_x is None:
                continue
            candidates = [field for field in row if field.x_min >= label_x - 1]
            value = ClovaOcrService._pick_row_number(candidates, minimum, maximum)
            if value is None:
                value = ClovaOcrService._pick_row_number(
                    [field for field in row if not label_re.search(field.text)], minimum, maximum
                )
            if value is not None:
                return caster(value)
        return None

    @staticmethod
    def _pick_row_number(tokens: list[OcrField], minimum: float, maximum: float) -> float | None:
        for field in sorted(tokens, key=lambda token: token.x_min):
            if ClovaOcrService._classify_ocr_token(field.text) in {"range", "percent"}:
                continue
            for match in OCR_NUMBER_PATTERN.finditer(field.text):
                value = float(match.group(0))
                if minimum <= value <= maximum:
                    return value
        return None

    @staticmethod
    def _find_nutrition_row_value(
        rows: list[list[OcrField]],
        labels: list[str],
        expected_unit: str,
        minimum: float,
        maximum: float,
        caster: Callable[[float], int | float],
    ) -> int | float | None:
        label_re = re.compile("|".join(labels), flags=re.IGNORECASE)
        for row in rows:
            if not label_re.search(ClovaOcrService._row_text(row)):
                continue
            label_x = ClovaOcrService._label_right_edge(row, label_re)
            candidates = [field for field in row if label_x is None or field.x_min >= label_x - 1]
            value = ClovaOcrService._pick_nutrition_value(candidates, expected_unit, minimum, maximum)
            if value is None:
                value = ClovaOcrService._pick_nutrition_value(
                    [field for field in row if not label_re.search(field.text)], expected_unit, minimum, maximum
                )
            if value is not None:
                return caster(value)
        return None

    @staticmethod
    def _pick_nutrition_value(
        tokens: list[OcrField],
        expected_unit: str,
        minimum: float,
        maximum: float,
    ) -> float | None:
        sorted_tokens = sorted(tokens, key=lambda token: token.x_min)
        for index, field in enumerate(sorted_tokens):
            if ClovaOcrService._classify_ocr_token(field.text) in {"range", "percent"}:
                continue
            match = OCR_NUMBER_PATTERN.search(field.text)
            if not match:
                continue
            raw_value = float(match.group(0))
            unit = ClovaOcrService._extract_ocr_unit(field.text[match.end() :])
            if unit is None and index + 1 < len(sorted_tokens):
                unit = ClovaOcrService._extract_ocr_unit(sorted_tokens[index + 1].text)
            converted = ClovaOcrService._convert_ocr_unit(raw_value, unit, expected_unit)
            if converted is not None and minimum <= converted <= maximum:
                return converted
        return None

    @staticmethod
    def _extract_ocr_unit(text: str) -> str | None:
        match = re.search(r"(kcal|mg|mcg|µg|ug|g)\b", text, flags=re.IGNORECASE)
        if not match:
            match = re.search(r"(kcal|mg|mcg|µg|ug|g)\s*$", text.strip(), flags=re.IGNORECASE)
        return match.group(1).lower() if match else None

    @staticmethod
    def _convert_ocr_unit(value: float, unit: str | None, expected_unit: str) -> float | None:
        if unit is None:
            return value
        if unit not in OCR_UNIT_TO_BASE:
            return value
        base_kind, base_factor = OCR_UNIT_TO_BASE[unit]
        in_base = value * base_factor
        if expected_unit == base_kind:
            return in_base
        if expected_unit == "mg" and base_kind == "g":
            return in_base * 1000
        if expected_unit == "g" and base_kind == "mg":
            return in_base / 1000
        if expected_unit == base_kind == "kcal":
            return in_base
        if expected_unit == "kcal" or base_kind == "kcal":
            return None
        return in_base

    @staticmethod
    def _extract_blood_pressure_from_rows(rows: list[list[OcrField]] | None) -> dict[str, int] | None:
        if not rows:
            return None
        bp_label = re.compile(r"혈압|blood\s*pressure|\bbp\b", flags=re.IGNORECASE)
        for row in rows:
            joined = ClovaOcrService._row_text(row)
            if not bp_label.search(joined):
                continue
            slash = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", joined)
            if slash:
                sbp, dbp = int(slash.group(1)), int(slash.group(2))
                if ClovaOcrService._is_valid_bp(sbp, dbp):
                    return {"sbp": sbp, "dbp": dbp}
            values = [int(value) for value in re.findall(r"\b(\d{2,3})\b", joined)]
            for index in range(len(values) - 1):
                sbp, dbp = values[index], values[index + 1]
                if ClovaOcrService._is_valid_bp(sbp, dbp):
                    return {"sbp": sbp, "dbp": dbp}
        sbp = ClovaOcrService._find_labeled_row_value(rows, [r"수축기", r"최고\s*혈압", r"\bsbp\b"], 70, 250, int)
        dbp = ClovaOcrService._find_labeled_row_value(rows, [r"이완기", r"최저\s*혈압", r"\bdbp\b"], 40, 150, int)
        if sbp is not None and dbp is not None:
            return {"sbp": int(sbp), "dbp": int(dbp)}
        return None

    @staticmethod
    def _is_valid_bp(sbp: int, dbp: int) -> bool:
        return 70 <= sbp <= 250 and 40 <= dbp <= 150 and sbp > dbp

    @staticmethod
    def _extract_blood_pressure(text: str) -> dict[str, int] | None:
        patterns = [
            r"(?:혈압|blood\s*pressure|bp)[^\d]{0,20}(\d{2,3})\s*/\s*(\d{2,3})",
            r"(?:수축기|최고\s*혈압|sbp)[^\d]{0,20}(\d{2,3}).{0,40}(?:이완기|최저\s*혈압|dbp)[^\d]{0,20}(\d{2,3})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            sbp = int(match.group(1))
            dbp = int(match.group(2))
            if ClovaOcrService._is_valid_bp(sbp, dbp):
                return {"sbp": sbp, "dbp": dbp}
        return None

    @staticmethod
    def _find_labeled_number(
        text: str,
        labels: list[str],
        minimum: float,
        maximum: float,
        caster: type[int] | type[float],
    ) -> int | float | None:
        label_pattern = "|".join(labels)
        pattern = rf"(?:{label_pattern})(?:(?!\n\s*(?:{label_pattern})).){{0,90}}?(\d+(?:\.\d+)?)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        context = text[match.start() : match.end()]
        if ClovaOcrService._looks_like_missing_or_reference_value(context):
            return None
        value = float(match.group(1))
        if not minimum <= value <= maximum:
            return None
        return int(round(value)) if caster is int else round(value, 2)

    @staticmethod
    def _looks_like_missing_or_reference_value(context: str) -> bool:
        number_match = re.search(r"\d+(?:\.\d+)?", context)
        if not number_match:
            return False
        before_number = context[: number_match.start()]
        if NO_RESULT_PATTERN.search(before_number):
            return True
        if PRODUCT_INFO_PATTERN.search(before_number):
            return True
        return bool(REFERENCE_VALUE_PATTERN.search(before_number))

    @staticmethod
    def _extract_urine_protein(text: str) -> bool | None:
        match = re.search(
            r"(?:요\s*단백|요단백|단백뇨|소변\s*단백|urine\s*protein|proteinuria)[^\n]{0,30}", text, flags=re.IGNORECASE
        )
        if not match:
            return None
        value = match.group(0)
        if re.search(r"양성|\+|positive|pos", value, flags=re.IGNORECASE):
            return True
        if re.search(r"음성|\-|negative|neg", value, flags=re.IGNORECASE):
            return False
        return None

    @staticmethod
    def _extract_urine_protein_from_rows(rows: list[list[OcrField]] | None) -> bool | None:
        if not rows:
            return None
        label = re.compile(r"요\s*단백|요단백|단백뇨|소변\s*단백|urine\s*protein|proteinuria", flags=re.IGNORECASE)
        for row in rows:
            joined = ClovaOcrService._row_text(row)
            if not label.search(joined):
                continue
            if re.search(r"±|\+\s*-|trace|미\s*량", joined, flags=re.IGNORECASE):
                return None
            if re.search(r"양성|(?<![\d.])\++|positive|\bpos\b", joined, flags=re.IGNORECASE):
                return True
            if re.search(r"음성|(?<![\d.])-(?!\d)|negative|\bneg\b", joined, flags=re.IGNORECASE):
                return False
        return None
