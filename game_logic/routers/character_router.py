from fastapi import APIRouter, Depends, HTTPException

from auth.models import User
from auth.user_service import get_current_user
from deps import get_services
from game_logic.models.models import SummandParams, MultiplierParams, CharacterClass, Character, CharacterType, Race
from game_logic.schemas.character_schema import CharacterSchema, AddCharacterSchema
from game_logic.services.general import Services

router = APIRouter(prefix='/characters', tags=['Characters'])


@router.post('', response_model=CharacterSchema)
async def create_character(add_character: AddCharacterSchema,
                           user: User = Depends(get_current_user),
                           services: Services = Depends(get_services)):
    summand_params_model = SummandParams(**add_character.summand_params.model_dump())
    multiplier_params_model = MultiplierParams(**add_character.multiplier_params.model_dump())
    inserted_summand_params = await services.params_service.add(summand_params_model)
    inserted_multiplier_params = await services.params_service.add(multiplier_params_model)
    try:
        character_class: CharacterClass = await services.class_service.get_by_id(add_character.class_id)
        for subclass in character_class.subclasses:
            if subclass.id == add_character.subclass_id:
                break
        else:
            raise HTTPException(400, detail=f'Character class with id {character_class.id} has no subclass with id {add_character.character_subclass_id}')
        race: Race = await services.race_service.get_by_id(add_character.race_id)
        tiers_items = {}
        items = await services.item_service.get_by_ids(add_character.item_ids)
        for item in items:
            if not tiers_items.get(item.tier):
                tiers_items.setdefault(item.tier, item)
            else:
                raise HTTPException(400, detail=f'Two items of tier {item.tier} cannot be')
        tiers_abilities = {}
        abilities = await services.ability_service.get_by_ids(add_character.ability_ids)
        for ability in abilities:
            if (not tiers_abilities.get(ability.tier)) or (ability.tier == 0):
                tiers_items.setdefault(ability.tier, abilities)
            else:
                raise HTTPException(400, f'Two abilities of tier {ability.tier} cannot be')
        character_type = CharacterType(add_character.character_type)
        if character_type != CharacterType.MAIN:
            user_id = None
        else: user_id = user.id
        character_model = Character(name=add_character.name,
                                    avatar=add_character.avatar,
                                    class_id=character_class.id,
                                    subclass_id=add_character.subclass_id,
                                    race_id=race.id,
                                    character_type=character_type,
                                    summand_params_id=inserted_summand_params.id,
                                    multiplier_params_id=inserted_multiplier_params.id,
                                    user_id=user_id,
                                    stardom=add_character.stardom,
                                    level=add_character.level)
        character_model.items.extend(items)
        character_model.abilities.extend(abilities)
        inserted_character = await services.character_service.add(character_model)
        return inserted_character
    except Exception as e:
        print(e.with_traceback())
        raise HTTPException(400, detail=str(e))


@router.get('', response_model=list[CharacterSchema])
async def get_user_characters(user: User = Depends(get_current_user),
                              services: Services = Depends(get_services)):
    characters = await services.character_service.get_by_user_id(user.id)
    return characters


@router.get('/{character_id}', response_model=CharacterSchema)
async def get_character_by_id(character_id: int,
                              user: User = Depends(get_current_user)):
    ...


@router.delete('/{character_id}')
async def delete_character(character_id: int,
                           user: User = Depends(get_current_user),
                           services: Services = Depends(get_services)):
    await services.character_service.delete_by_id_by_user(character_id, user.id)
    return {'message': 'ok'}