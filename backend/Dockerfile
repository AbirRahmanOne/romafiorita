FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Shell form so Render's $PORT is honoured (defaults to 8000 locally).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
