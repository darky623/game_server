import os

from dotenv import load_dotenv
load_dotenv()

PG_URL = os.getenv('PG_URL')
PG_USERNAME = os.getenv('POSTGRES_USER')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')

if os.getenv("DOCKER"):
    db_url = f'postgresql+asyncpg://{PG_USERNAME}:{PG_PASSWORD}@{PG_URL}/{DB_NAME}'
else:
    db_url = os.getenv('DB_URL_LOCAL')

auth_server = os.getenv('AUTH_SERVER')

secret_key = os.environ.get('SECRET_KEY')

dt_format = '%d/%m/%Y %H:%M:%S'
token_lifetime = 3600

webhook_port = os.environ.get('WEBHOOK_PORT')
webhook_ssl_cert = None
webhook_ssl_priv = None

archetypes = [{"title": "Strength"},
              {"title": "Dexterity"},
              {"title": "Intelligence"}]

character_types = [{'name': 'main'},
                   {'name': 'collection'},
                   {'name': 'secondary'}]
