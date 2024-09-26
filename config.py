import os

PG_URL = os.getenv('PG_URL')
PG_USERNAME = os.getenv('POSTGRES_USER')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')

db_url = f'postgresql+asyncpg://{PG_USERNAME}:{PG_PASSWORD}@{PG_URL}/{DB_NAME}'

auth_server = "http://31.129.54.119"

secret_key = "secret_key"

dt_format = '%d/%m/%Y %H:%M:%S'
token_lifetime = 3600
