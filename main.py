from fastapi import FastAPI, Depends
from sqlalchemy import select
from starlette.middleware.cors import CORSMiddleware

from auth.models import User
from auth.user_service import get_current_user
from bioms.router_biome import router as biome_router
from bioms.router_player_progress import router as player_progress_router
from chat.router import router as chat_router
from chat.websocket import router as chat_websocket_router
from friends.router import router as friends_router
from database import AsyncSessionFactory
from game_logic.models import CharacterArchetype, Character

from schemas import CreateCharacterSchema

app = FastAPI()

app.include_router(chat_router)
app.include_router(chat_websocket_router)
app.include_router(biome_router)
app.include_router(player_progress_router)
app.include_router(friends_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/archetypes")
async def get_archetypes(user: User = Depends(get_current_user)):
    response = {"message": "List of available archetypes", "archetypes": []}
    async with AsyncSessionFactory() as db:
        result = await db.execute(select(CharacterArchetype))
        auth_sessions = result.scalars().all()
        for archetype in auth_sessions:
            response["archetypes"].append(archetype.serialize())

        return response


@app.get("/summary")
async def get_summary(user: User = Depends(get_current_user)):
    response = {
        "message": "General summary",
        "server_info": None,
        "user_info": None,
        "character_info": None,
    }

    async with AsyncSessionFactory() as db:
        user = await db.merge(user)

        response["user_info"] = {"username": user.username, "email": user.email}

        for character in user.characters:
            if character.character_type.name == "main":
                response["character_info"] = {
                    "name": character.name,
                    "archetype": character.archetype_id,
                }

        return response


@app.post("/create_character")
async def create_character(
    create_character: CreateCharacterSchema, user: User = Depends(get_current_user)
):
    response = {
        "message": "The main character has been successfully created!",
        "character_info": None,
    }

    async with AsyncSessionFactory() as db:
        user = await db.merge(user)

        for character in user.characters:
            if character.character_type.name == "main":
                response["message"] = "The main character has already been created!"
                response["character_info"] = CreateCharacterSchema(
                    name=character.name, archetype_id=character.archetype_id
                )

        if not response["character_info"]:
            result = await db.execute(
                select(CharacterArchetype).where(
                    CharacterArchetype.id == create_character.archetype_id
                )
            )
            existing_character = result.scalars().first()
            if not existing_character:
                response["message"] = "There is no archetype with such an id!"
                return response

            character = Character(
                name=create_character.name,
                character_type_id=1,
                archetype_id=create_character.archetype_id,
                user_id=user.id,
            )
            user.characters.append(character)
            await db.commit()
            response["character_info"] = create_character

        return response
