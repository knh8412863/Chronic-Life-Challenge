import base64
import re
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core import config
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


class ClovaOcrService:
    async def analyze_health_checkup_file(
        self,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> HealthCheckupOcrResponse:
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
