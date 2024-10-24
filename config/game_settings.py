import os

PG_URL = os.getenv("PG_URL")
PG_USERNAME = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")

db_url = f"postgresql+asyncpg://{PG_USERNAME}:{PG_PASSWORD}@{PG_URL}/{DB_NAME}"

auth_server = os.getenv("AUTH_SERVER")

secret_key = os.environ.get("SECRET_KEY")

dt_format = "%d/%m/%Y %H:%M:%S"
token_lifetime = 360000

permissions_for_clan = {
    "Head": [
        "invite_users",
        "kick_users",
        "edit_clan_settings",
        "assigning_roles",
        "delete_clan",
        "access_to_god_chat",
        "bank_access",
        "start_clan_wars",
        "moderate_chat",
    ],
    "Deputy": [
        "invite_users",
        "kick_users",
        "assigning_roles_to_elder",
        "delete_clan",
        "access_to_god_chat",
        "bank_access",
        "start_clan_wars",
        "moderate_chat",
    ],
    "Elder": [
        "invite_users",
        "kick_users",
        "moderate_chat",
    ],
    "Officer": ["invite_users"],
    "Participant": [],
}

max_of_clan_members_from_rang = {1: 25, 2: 30, 3: 35, 4: 40}
