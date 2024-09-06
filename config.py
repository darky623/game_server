db_url = "postgresql+asyncpg://postgres:123@localhost:5432/game_server"
auth_server = "http://31.129.54.119"

secret_key = "secret_key"

dt_format = '%d/%m/%Y %H:%M:%S'
token_lifetime = 360000

webhook_port = 8000
webhook_ssl_cert = None
webhook_ssl_priv = None

archetypes = [{"title": "Strength"},
              {"title": "Dexterity"},
              {"title": "Intelligence"}]

character_types = [{'name': 'main'},
                   {'name': 'collection'},
                   {'name': 'secondary'}]
