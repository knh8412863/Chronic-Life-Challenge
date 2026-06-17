#!/usr/bin/env python3
"""Export prediction feedback as model-improvement candidate data.

The script reads stored prediction feedback and result items from the service
database, then writes a CSV that can be reviewed before retraining or threshold
analysis. It does not trigger retraining by itself.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from tortoise import Tortoise

from app.core.db.databases import TORTOISE_ORM
from app.models.predictions import PredictionFeedback, PredictionResultItem

DEFAULT_OUTPUT = Path("exports/prediction-feedback.csv")


async def export_prediction_feedback(output: Path) -> int:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        feedbacks = (
            await PredictionFeedback.all().select_related("prediction_result", "user").order_by("-created_at", "-id")
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "feedback_id",
                    "user_id",
                    "prediction_result_id",
                    "feedback_type",
                    "actual_diagnosis",
                    "comment",
                    "overall_risk_level",
                    "disease_code",
                    "model_version",
                    "probability",
                    "threshold",
                    "is_at_risk",
                    "risk_level",
                    "created_at",
                ],
            )
            writer.writeheader()
            count = 0
            for feedback in feedbacks:
                result = feedback.prediction_result
                items = await PredictionResultItem.filter(result_id=result.id).order_by("disease_code")
                for item in items:
                    writer.writerow(
                        {
                            "feedback_id": feedback.id,
                            "user_id": feedback.user_id,
                            "prediction_result_id": result.id,
                            "feedback_type": feedback.feedback_type,
                            "actual_diagnosis": feedback.actual_diagnosis,
                            "comment": feedback.comment,
                            "overall_risk_level": result.overall_risk_level,
                            "disease_code": item.disease_code,
                            "model_version": item.model_version,
                            "probability": item.probability,
                            "threshold": item.threshold,
                            "is_at_risk": item.is_at_risk,
                            "risk_level": item.risk_level,
                            "created_at": feedback.created_at.isoformat(),
                        }
                    )
                    count += 1
        return count
    finally:
        await Tortoise.close_connections()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export prediction feedback for model improvement review.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    count = asyncio.run(export_prediction_feedback(args.output))
    print(f"Exported {count} prediction-feedback rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
