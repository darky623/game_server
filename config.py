import os

PG_URL = os.getenv('PG_URL')
PG_USERNAME = os.getenv('PG_USERNAME')
PG_PASSWORD = os.getenv('PG_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

db_url = f'postgresql+asyncpg://{PG_USERNAME}:{PG_PASSWORD}@{PG_URL}/{DB_NAME}'
auth_server = "http://31.129.54.119"

secret_key = "secret_key"

dt_format = '%d/%m/%Y %H:%M:%S'
token_lifetime = 3600

webhook_port = 8000
webhook_ssl_cert = None
webhook_ssl_priv = None

archetypes = [{"title": "Strength"},
              {"title": "Dexterity"},
              {"title": "Intelligence"}]

character_types = [{'name': 'main'},
                   {'name': 'collection'},
                   {'name': 'secondary'}]
