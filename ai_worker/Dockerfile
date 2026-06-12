FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. uv 설치 (공식 이미지에서 복사해오는 가장 깔끔한 방법)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 2. 의존성 패키지 관리 파일을 컨테이너 내부에 복사합니다.
COPY pyproject.toml uv.lock ./

# 3. 워커는 DB 모델과 예측 서비스를 재사용하므로 app, ai 의존성을 함께 설치합니다.
RUN uv sync --group app --group ai --no-dev --frozen

# 4. 로컬 소스 코드와 추론 코드를 컨테이너 내부로 복사합니다.
COPY ./app ./app
COPY ./ai_worker ./ai_worker

# 5. 해당 이미지를 활용하여 도커컨테이너 실행시 실행되는 명령어입니다.
CMD ["uv", "run", "--no-sync", "python", "-m", "ai_worker.main"]
