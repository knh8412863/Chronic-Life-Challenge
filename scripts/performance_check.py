#!/usr/bin/env python3
"""Measure API latency and write a Markdown P95 report.

This script intentionally avoids project dependencies so it can run from a
fresh Python environment. Authentication values are read from environment
variables or command-line options and are never written to the report.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import ssl
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://all4health.kro.kr/api/v1"
DEFAULT_OUTPUT = Path("docs/performance-result.md")


@dataclass(frozen=True)
class Endpoint:
    name: str
    method: str
    path: str
    auth_required: bool = True
    expected_statuses: tuple[int, ...] = (200,)


@dataclass
class Sample:
    latency_ms: float
    status_code: int | None
    ok: bool
    error: str | None = None


ENDPOINTS: tuple[Endpoint, ...] = (
    Endpoint("Home summary", "GET", "/home/summary"),
    Endpoint("Notifications", "GET", "/notifications"),
    Endpoint("Notification unread count", "GET", "/notifications/unread-count"),
    Endpoint("Challenges", "GET", "/challenges"),
    Endpoint("Challenge summary", "GET", "/challenges/summary"),
    Endpoint("My challenge participations", "GET", "/challenge-participations/me"),
    Endpoint("Prediction result list", "GET", "/prediction-results?limit=20"),
    Endpoint("Weekly report list", "GET", "/weekly-reports?limit=20"),
    Endpoint("Vital records", "GET", "/health/vitals?limit=20"),
    Endpoint("Lipid records", "GET", "/health/lipid-obesity-records?limit=20"),
    Endpoint("Renal records", "GET", "/health/renal-records?limit=20"),
    Endpoint("Exercise logs", "GET", "/health/exercise-logs?limit=20"),
    Endpoint("Activity logs", "GET", "/health/activity-logs?limit=20"),
)

EXTERNAL_DEPENDENCY_ENDPOINTS: tuple[Endpoint, ...] = (
    Endpoint("Swagger docs", "GET", "/../docs", auth_required=False, expected_statuses=(200,)),
)


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = math.ceil((percentile_value / 100) * len(ordered)) - 1
    return ordered[max(0, min(rank, len(ordered) - 1))]


def request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float,
    insecure_skip_tls_verify: bool = False,
) -> tuple[int, dict[str, Any] | None, float, str | None]:
    headers = {"Accept": "application/json"}
    data: bytes | None = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    started = time.perf_counter()
    try:
        context = ssl._create_unverified_context() if insecure_skip_tls_verify else None
        with urlopen(
            Request(url, data=data, headers=headers, method=method),
            timeout=timeout,
            context=context,
        ) as response:
            body = response.read()
            elapsed_ms = (time.perf_counter() - started) * 1000
            if not body:
                return response.status, None, elapsed_ms, None
            try:
                return response.status, json.loads(body.decode("utf-8")), elapsed_ms, None
            except json.JSONDecodeError:
                return response.status, None, elapsed_ms, None
    except HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return exc.code, None, elapsed_ms, str(exc)
    except (TimeoutError, URLError, OSError) as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return 0, None, elapsed_ms, str(exc)


def extract_access_token(response_body: dict[str, Any] | None) -> str | None:
    if not response_body:
        return None
    candidates = [
        response_body.get("access_token"),
        response_body.get("token"),
        (response_body.get("data") or {}).get("access_token") if isinstance(response_body.get("data"), dict) else None,
        (response_body.get("data") or {}).get("token") if isinstance(response_body.get("data"), dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def login(
    base_url: str,
    email: str,
    password: str,
    timeout: float,
    insecure_skip_tls_verify: bool = False,
) -> tuple[str, Sample]:
    status_code, body, elapsed_ms, error = request_json(
        "POST",
        urljoin(base_url.rstrip("/") + "/", "auth/login"),
        payload={"email": email, "password": password},
        timeout=timeout,
        insecure_skip_tls_verify=insecure_skip_tls_verify,
    )
    token = extract_access_token(body)
    ok = status_code == 200 and token is not None
    if not ok and error is None:
        error = "login succeeded without an access token" if status_code == 200 else f"HTTP {status_code}"
    return token or "", Sample(elapsed_ms, status_code, ok, error)


def measure_endpoint(
    base_url: str,
    endpoint: Endpoint,
    token: str | None,
    iterations: int,
    timeout: float,
    insecure_skip_tls_verify: bool = False,
) -> list[Sample]:
    samples: list[Sample] = []
    url = urljoin(base_url.rstrip("/") + "/", endpoint.path.lstrip("/"))
    for _ in range(iterations):
        status_code, _, elapsed_ms, error = request_json(
            endpoint.method,
            url,
            token=token,
            timeout=timeout,
            insecure_skip_tls_verify=insecure_skip_tls_verify,
        )
        samples.append(
            Sample(
                latency_ms=elapsed_ms,
                status_code=status_code or None,
                ok=status_code in endpoint.expected_statuses,
                error=error,
            )
        )
    return samples


def summarize(samples: list[Sample]) -> dict[str, Any]:
    latencies = [sample.latency_ms for sample in samples]
    failures = [sample for sample in samples if not sample.ok]
    return {
        "count": len(samples),
        "success_count": len(samples) - len(failures),
        "failure_count": len(failures),
        "failure_rate": (len(failures) / len(samples) * 100) if samples else 0.0,
        "avg": statistics.fmean(latencies) if latencies else 0.0,
        "p50": percentile(latencies, 50),
        "p95": percentile(latencies, 95),
        "max": max(latencies) if latencies else 0.0,
        "status_codes": sorted({sample.status_code for sample in samples if sample.status_code is not None}),
        "last_error": next((sample.error for sample in reversed(samples) if sample.error), None),
    }


def format_ms(value: float) -> str:
    return f"{value:,.1f}"


def grade_from_p95(p95_values: list[float]) -> str:
    if not p95_values:
        return "성능 테스트를 수행하지 않았다."
    over = [value for value in p95_values if value > 3000]
    if not over:
        return "P95 3초 이내 성능 테스트 결과를 제시하였다."
    if len(over) <= max(1, len(p95_values) // 4):
        return "대부분 3초 이내이다."
    if len(over) <= len(p95_values) // 2:
        return "간헐적으로 3초를 초과한다."
    return "자주 3초를 초과한다."


def write_report(
    output: Path,
    base_url: str,
    iterations: int,
    results: list[tuple[Endpoint, dict[str, Any]]],
    login_summary: dict[str, Any] | None,
    include_external: bool,
) -> None:
    measured_at = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    p95_values = [summary["p95"] for _, summary in results if summary["failure_rate"] < 100]
    grade = grade_from_p95(p95_values)

    lines = [
        "# API 성능 테스트 결과",
        "",
        f"- 측정 일시: {measured_at}",
        f"- 대상 Base URL: `{base_url}`",
        f"- 반복 횟수: endpoint당 {iterations}회",
        "- 측정 방식: Python 표준 라이브러리 기반 순차 요청, 클라이언트 측 왕복 시간 측정",
        "- 인증 방식: 로그인 API로 access token 발급 후 보호 API 호출",
        "- 평가 기준: 각 API P95 Latency 3,000ms 이내 여부",
        f"- 종합 판단: **{grade}**",
        "",
        "## 측정 범위",
        "",
        "- 로그인, 홈 요약, 알림, 챌린지, 예측 이력, 주간 리포트, 건강 기록 조회 API를 대상으로 측정합니다.",
        "- OCR, LLM 조언 생성, PDF 생성, SMTP 메일 발송처럼 외부 서비스 또는 파일 처리에 의존하는 API는 일반 조회 API와 분리해서 해석합니다.",
        "- 네트워크 상태, EC2 리소스 상태, DB 데이터량에 따라 결과가 달라질 수 있습니다.",
        "",
    ]

    if login_summary is not None:
        lines.extend(
            [
                "## 로그인 측정",
                "",
                "| API | Count | Success | Failure | Avg(ms) | P50(ms) | P95(ms) | Max(ms) | Status |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
                (
                    f"| `POST /auth/login` | {login_summary['count']} | {login_summary['success_count']} | "
                    f"{login_summary['failure_count']} | {format_ms(login_summary['avg'])} | "
                    f"{format_ms(login_summary['p50'])} | {format_ms(login_summary['p95'])} | "
                    f"{format_ms(login_summary['max'])} | {login_summary['status_codes']} |"
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## API별 측정 결과",
            "",
            "| API | Count | Success | Failure | Failure Rate | Avg(ms) | P50(ms) | P95(ms) | Max(ms) | Status | 판단 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for endpoint, summary in results:
        judgment = "3초 이내" if summary["p95"] <= 3000 and summary["failure_rate"] < 100 else "확인 필요"
        lines.append(
            f"| `{endpoint.method} {endpoint.path}` | {summary['count']} | {summary['success_count']} | "
            f"{summary['failure_count']} | {summary['failure_rate']:.1f}% | {format_ms(summary['avg'])} | "
            f"{format_ms(summary['p50'])} | {format_ms(summary['p95'])} | {format_ms(summary['max'])} | "
            f"{summary['status_codes']} | {judgment} |"
        )

    lines.extend(
        [
            "",
            "## 실행 방법",
            "",
            "```bash",
            "PERF_EMAIL='테스트계정@example.com' PERF_PASSWORD='테스트비밀번호' \\",
            "python scripts/performance_check.py --iterations 20 --output docs/performance-result.md",
            "```",
            "",
            "외부 의존/파일 처리 API까지 포함해서 별도로 측정하려면:",
            "",
            "```bash",
            "PERF_EMAIL='테스트계정@example.com' PERF_PASSWORD='테스트비밀번호' \\",
            "python scripts/performance_check.py --iterations 20 --include-external",
            "```",
            "",
            "## 비고",
            "",
            "- 결과 문서에는 비밀번호, access token 등 인증 정보가 기록되지 않습니다.",
            "- 실패율이 높은 API는 계정 데이터 부재, 권한 문제, 서버 상태를 별도로 확인해야 합니다.",
        ]
    )
    if include_external:
        lines.append("- 이번 실행에는 외부 의존 API 측정 옵션이 포함되었습니다.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure All4Health API latency and calculate P95.")
    parser.add_argument("--base-url", default=os.getenv("PERF_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--email", default=os.getenv("PERF_EMAIL"))
    parser.add_argument("--password", default=os.getenv("PERF_PASSWORD"))
    parser.add_argument("--token", default=os.getenv("PERF_ACCESS_TOKEN"))
    parser.add_argument("--iterations", type=int, default=int(os.getenv("PERF_ITERATIONS", "20")))
    parser.add_argument("--warmup", type=int, default=int(os.getenv("PERF_WARMUP", "2")))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("PERF_TIMEOUT", "10")))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--include-external", action="store_true")
    parser.add_argument(
        "--insecure-skip-tls-verify",
        action="store_true",
        default=os.getenv("PERF_INSECURE_SKIP_TLS_VERIFY", "").lower() in {"1", "true", "yes"},
        help="Skip TLS certificate verification for local measurement environments with missing CA bundles.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.iterations < 1:
        print("--iterations must be >= 1", file=sys.stderr)
        return 2

    token = args.token
    login_samples: list[Sample] = []
    if not token:
        if not args.email or not args.password:
            print("Set PERF_EMAIL/PERF_PASSWORD or PERF_ACCESS_TOKEN before running.", file=sys.stderr)
            return 2
        for _ in range(max(args.warmup, 0)):
            login(
                args.base_url,
                args.email,
                args.password,
                args.timeout,
                args.insecure_skip_tls_verify,
            )
        for _ in range(args.iterations):
            token, sample = login(
                args.base_url,
                args.email,
                args.password,
                args.timeout,
                args.insecure_skip_tls_verify,
            )
            login_samples.append(sample)
            if not token:
                print(f"Login failed: {sample.error}", file=sys.stderr)
                return 1

    endpoints = list(ENDPOINTS)
    if args.include_external:
        endpoints.extend(EXTERNAL_DEPENDENCY_ENDPOINTS)

    results: list[tuple[Endpoint, dict[str, Any]]] = []
    for endpoint in endpoints:
        for _ in range(max(args.warmup, 0)):
            measure_endpoint(
                args.base_url,
                endpoint,
                token if endpoint.auth_required else None,
                1,
                args.timeout,
                args.insecure_skip_tls_verify,
            )
        samples = measure_endpoint(
            args.base_url,
            endpoint,
            token if endpoint.auth_required else None,
            args.iterations,
            args.timeout,
            args.insecure_skip_tls_verify,
        )
        results.append((endpoint, summarize(samples)))

    login_summary = summarize(login_samples) if login_samples else None
    write_report(args.output, args.base_url, args.iterations, results, login_summary, args.include_external)
    print(f"Wrote performance report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
