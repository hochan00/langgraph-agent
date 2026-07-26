# 파이썬 3.13 리눅스 베이스
FROM python:3.13-slim

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# 작업 폴더
WORKDIR /app

# 코드 전체 복사
COPY . .

# 의존성 설치
RUN uv sync --frozen

# 서버 실행 (0.0.0.0 = 컨테이너 밖에서 접속 허용)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
