FROM python:3.11-slim

WORKDIR /app

COPY scoring/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared shared
COPY scoring scoring

EXPOSE 8000

CMD ["uvicorn", "scoring.main:app", "--host", "0.0.0.0", "--port", "8000"]
