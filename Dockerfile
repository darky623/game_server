FROM python:3.10.4-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic revision --autogenerate && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile ${SSL_KEYFILE} --ssl-certfile ${SSL_CERTFILE}"]
