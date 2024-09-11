import os

from dotenv import load_dotenv
load_dotenv()

if os.getenv("DOCKER_DB_URL"):
    db_url = os.getenv('DOCKER_DB_URL')
else:
    db_url = os.getenv('DB_URL')

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
