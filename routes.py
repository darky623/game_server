from models import User, AuthSession
from game_logic.models import Character, CharacterArchetype
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from aiohttp import web, ClientSession
from database import engine
import config
import json

routes = web.RouteTableDef()

def create_archetypes():
    archetypes = []
    with Session(autoflush=False, bind=engine) as db:
        for archetype in config.archetypes:
            archetypes.append(CharacterArchetype(title=archetype['title']))
            db.add_all(archetypes)
            db.commit()


def validate_form_data(byte_str: bytes, required_fields: list):
    decoded_str = byte_str.decode('utf-8')
    try:
        data = json.loads(decoded_str)
    except json.decoder.JSONDecodeError as e:
        return None, "It is not JSON data"

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return None, f"{', '.join(missing_fields)} field(s) is missing"
    else:
        return data, None


async def check_auth_token(token: str):
    user = None
    with Session(autoflush=False, bind=engine) as db:
        auth = db.query(AuthSession).filter(AuthSession.token == token, AuthSession.status == 'active').first()
        if auth:
            if (datetime.now()-auth.create_date) <= timedelta(seconds=config.token_lifetime):
                user = auth.user
            else:
                auth.status = 'expired'
                db.commit()
        else:
            user = await check_remote_auth_token(token)

    return user


def get_token(request):
    auth_header = request.headers.get('Authorization')

    if auth_header is None or not auth_header.startswith('Bearer '):
        raise Exception('Token is invalid')

    token = auth_header[len('Bearer '):]
    return token


async def check_remote_auth_token(token: str):
    headers = {'Authorization': f'Bearer {token}'}
    async with ClientSession() as session:
        async with session.get(f'{config.auth_server}/token', headers=headers) as resp:
            byte_str = await resp.text()
            data, message = validate_form_data(byte_str.encode(), ['message', 'user', 'auth'])
            if not data:
                return None

            if not data['user']:
                return None

            else:
                with Session(autoflush=False, bind=engine) as db:
                    auth_session = AuthSession(token=data['auth']['token'],
                                               create_date=datetime.strptime(data['auth']['create_date'],
                                                                             config.dt_format))
                    user = db.query(User).filter(User.username == str(data['user']['username'])).first()
                    if not user:
                        user = User(username=data['user']['username'],
                                    email=data['user']['email'],
                                    create_date=datetime.strptime(data['user']['create_date'],
                                                                  config.dt_format))
                        db.add(user)

                    user.auth_sessions.append(auth_session)
                    db.commit()
                    return user


@routes.get('/archetypes')
async def servers_handler(request):
    response = {
        "message": "List of available archetypes",
        "archetypes": []
    }
    try:
        token = get_token(request)
    except Exception as e:
        response["message"] = str(e)
        return web.json_response(response)

    user = await check_auth_token(token)
    with Session(autoflush=False, bind=engine) as db:
        if not user:
            response["message"] = "Token is invalid!"
            return web.json_response(response)

        user = db.merge(user)
        for archetype in db.query(CharacterArchetype).all():
            response['archetypes'].append(archetype.serialize())

        return web.json_response(response)


@routes.get('/summary')
async def servers_handler(request):
    response = {"message": "General summary",
                "server_info": None,
                "user_info": None,
                "character_info": None}
    try:
        token = get_token(request)
    except Exception as e:
        response["message"] = str(e)
        return web.json_response(response)

    user = await check_auth_token(token)
    with Session(autoflush=False, bind=engine) as db:
        if not user:
            response["message"] = "Token is invalid!"
            return web.json_response(response)

        user = db.merge(user)

        response["user_info"] = {"username": user.username,
                                 "email": user.email}

        for character in user.characters:
            if character.character_type == 'main':
                response["character_info"] = {"name": character.name,
                                              "archetype": character.archetype_id}

        return web.json_response(response)


@routes.post('/create_character')
async def servers_handler(request):
    response = {
        "message": "The main character has been successfully created!",
        "character_info": None
    }
    try:
        token = get_token(request)
    except Exception as e:
        response["message"] = str(e)
        return web.json_response(response)
    byte_str = await request.read()
    data, message = validate_form_data(byte_str, ['name', 'archetype_id'])
    if not data:
        response["message"] = message
        return web.json_response(response)

    user = await check_auth_token(token)
    with Session(autoflush=False, bind=engine) as db:
        if not user:
            response["message"] = "Token is invalid!"
            return web.json_response(response)

        user = db.merge(user)

        for character in user.characters:
            if character.character_type == 'main':
                response["message"] = "The main character has already been created!"
                response["character_info"] = {"name": character.name,
                                              "archetype": character.archetype_id}

        if not response["character_info"]:
            if not db.query(CharacterArchetype).filter(CharacterArchetype.id == int(data['archetype_id'])).first():
                response["message"] = "There is no archetype with such an id!"
                return web.json_response(response)

            character = Character(name=data['name'], character_type='main', archetype_id=int(data['archetype_id']))
            user.characters.append(character)
            db.commit()
            response["character_info"] = {"name": character.name,
                                          "archetype": character.archetype_id}

        return web.json_response(response)
