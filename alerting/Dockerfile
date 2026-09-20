FROM python:3.11-slim

WORKDIR /app

COPY alerting/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared shared
COPY alerting alerting

EXPOSE 8000

CMD ["uvicorn", "alerting.main:app", "--host", "0.0.0.0", "--port", "8000"]
