import json
from datetime import datetime, timedelta

from sqlalchemy import select

from aiohttp import ClientSession
from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from config import config
from config.database import AsyncSessionFactory
from auth.models import User, AuthSession

http_bearer = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    user = await check_auth_token(token)
    if not user:
        raise credentials_exception
    return user


async def get_current_admin_user(user: User = Depends(get_current_user)):
    if user.is_admin:
        return user
    raise HTTPException(403, 'You are not admin')


async def websocket_authentication(websocket: WebSocket) -> User:
    token = websocket.headers.get('Authorization')
    if token and token.startswith("Bearer "):
        token = token[len("Bearer "):]
        user = await get_current_user(HTTPAuthorizationCredentials(scheme='Bearer', credentials=token))
        user.last_login = datetime.now()
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def check_auth_token(token: str):
    user = None
    async with AsyncSessionFactory() as db:
        result = await db.execute(select(AuthSession).where(
            AuthSession.token == token, AuthSession.status == 'active')
        )
        auth = result.scalars().first()
        print(auth)
        if auth:
            if (datetime.now()-auth.create_date) <= timedelta(seconds=config.token_lifetime):
                user = auth.user
            else:
                auth.status = 'expired'
                await db.commit()
        else:
            user = await check_remote_auth_token(token)

    return user


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
                async with AsyncSessionFactory() as db:
                    auth_session = AuthSession(token=data['auth']['token'],
                                               create_date=datetime.strptime(data['auth']['create_date'],
                                                                             config.dt_format))
                    result = await db.execute(select(User).where(User.username == str(data['user']['username'])))
                    user = result.scalars().first()
                    if not user:
                        user = User(username=data['user']['username'],
                                    email=data['user']['email'],
                                    create_date=datetime.strptime(data['user']['create_date'],
                                                                  config.dt_format))
                        db.add(user)

                    user.auth_sessions.append(auth_session)
                    await db.commit()
                    return user
