# Dockerfile
FROM python:3.11

WORKDIR /app

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]