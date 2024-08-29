sqlite_database = "postgresql://postgres:123@localhost:5432/game_server"
auth_server = "http://31.129.54.119"

secret_key = "secret_key"

dt_format = '%d/%m/%Y %H:%M:%S'
token_lifetime = 3600

webhook_port = 80
webhook_ssl_cert = None
webhook_ssl_priv = None

archetypes = [{"title": "Strength", "chars": []},
              {"title": "Dexterity", "chars": []},
              {"title": "Intelligence", "chars": []}]
