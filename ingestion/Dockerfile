FROM python:3.11-slim

WORKDIR /app

COPY ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared shared
COPY ingestion ingestion

EXPOSE 8000

CMD ["uvicorn", "ingestion.main:app", "--host", "0.0.0.0", "--port", "8000"]
