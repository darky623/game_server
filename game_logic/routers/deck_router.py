from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db #Функция получения сессии из вашей фабрики

from services import DeckService #Ваш сервисный класс
from schemas import UserDeck, DeckCharacter, Deck # Ваши Pydantic схемы

router = APIRouter(prefix="/userdecks", tags=["userdecks"])


@router.post("/", response_model=UserDeck, status_code=status.HTTP_201_CREATED)
async def create_user_deck(user_deck: UserDeck, db: AsyncSession = Depends(get_db)):
    # ... реализация создания UserDeck с использованием DeckService ...

@router.get("/{user_id}", response_model=List[UserDeck])
async def get_user_decks(user_id: int, db: AsyncSession = Depends(get_db)):
    # ... реализация получения списка UserDeck с использованием DeckService ...

# аналогичные роутеры для /deckcharacters

