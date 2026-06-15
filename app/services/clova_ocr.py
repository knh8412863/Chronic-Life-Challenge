import base64
import re
import time
import uuid
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
        extracted_text = self._extract_text(raw_response)
        parsed = self._parse_food_nutrition_text(extracted_text)
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
        extracted_text = self._extract_text(raw_response)
        parsed = self._parse_health_checkup_text(extracted_text)
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
    def _parse_health_checkup_text(text: str) -> dict[str, Any]:
        normalized = ClovaOcrService._normalize_text(text)
        parsed: dict[str, Any] = {
            "vitals": {},
            "lipid": {},
            "renal": {},
            "activity": {},
            "matched_fields": [],
        }

        bp = ClovaOcrService._extract_blood_pressure(normalized)
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
            value = ClovaOcrService._find_labeled_number(normalized, labels, minimum, maximum, caster)
            if value is not None:
                parsed[section][field_name] = value
                parsed["matched_fields"].append(field_name)

        urine_protein = ClovaOcrService._extract_urine_protein(normalized)
        if urine_protein is not None:
            parsed["renal"]["urine_protein_pos"] = urine_protein
            parsed["matched_fields"].append("urine_protein_pos")

        return parsed

    @staticmethod
    def _parse_food_nutrition_text(text: str) -> dict[str, Any]:
        normalized = ClovaOcrService._normalize_text(text)
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

        raw_nutrition_specs = [
            ("calories", [r"열량", r"칼로리", r"calories?", r"energy"], 0, 3000, int),
            ("carbs_g", [r"탄수화물", r"carbohydrates?", r"\bcarbs?\b"], 0, 500, float),
            ("protein_g", [r"단백질(?![가-힣])", r"protein"], 0, 300, float),
            ("fat_g", [r"지방", r"총\s*지방", r"total\s*fat", r"\bfat\b"], 0, 300, float),
            ("sodium_mg", [r"나트륨", r"sodium"], 0, 100000, float),
            ("sugar_g", [r"당류", r"당\s*류", r"sugars?", r"total\s*sugars?"], 0, 300, float),
            ("fiber_g", [r"식이\s*섬유", r"식이섬유", r"dietary\s*fiber", r"fiber"], 0, 100, float),
        ]
        nutrition: dict[str, int | float] = {}
        matched_fields: list[str] = []
        for field_name, labels, minimum, maximum, caster in raw_nutrition_specs:
            value = ClovaOcrService._find_labeled_number(normalized, labels, minimum, maximum, caster)
            if field_name == "calories":
                value = ClovaOcrService._extract_basis_calories(normalized, serving_basis, basis_amount_g) or value
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
            r"(?:^|[^\d])([1-9]\d{1,2}(?:\.\d+)?)\s*g\s*(?:당|기준|per)",
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
            if 70 <= sbp <= 250 and 40 <= dbp <= 150:
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
