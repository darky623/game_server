from models import User, AuthSession
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from aiohttp import web, ClientSession
import config
import json

routes = web.RouteTableDef()
engine = create_engine(config.sqlite_database, echo=True)


def validate_form_data(byte_str: str, required_fields: list):
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
            pass

    return user


async def check_remote_auth_token(token: str):
    request = str({"token": token})
    async with ClientSession() as session:
        async with session.get(f'{config.auth_server}/check_token', data=request.encode('utf-8')) as resp:
            byte_str = await resp.text()
            data, message = validate_form_data(byte_str, ['message', 'user', 'auth'])
            if not data:
                return data, message

            if not data['user']:
                return None, data['message']

            else:
                with Session(autoflush=False, bind=engine) as db:
                    auth_session = AuthSession(token=data['auth']['token'],
                                               create_date=datetime.strptime(data['auth']['date_create'],
                                                                             config.dt_format))
                    user = db.query(User).filter(User.username == str(data['user']['username'])).first()
                    if not user:
                        user = User(username=data['user']['username'],
                                    email=data['user']['email'],
                                    create_date=datetime.strptime(data['user']['date_create'],
                                                                  config.dt_format))
                        db.add(user)

                    user.auth_sessions.append(auth_session)
                    db.commit()

    return data, message
