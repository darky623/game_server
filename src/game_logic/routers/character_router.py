from fastapi import APIRouter, Depends, HTTPException

from auth.models import User
from auth.user_service import get_current_user
from config.deps import get_services
from src.game_logic.battle.controllers import CharacterController
from src.game_logic.models.models import SummandParams, MultiplierParams, CharacterClass, Character, CharacterType, Race
from src.game_logic.schemas.character_schema import CharacterSchema, AddCharacterSchema, EditCharacterSchema
from src.game_logic.services.general import Services

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
                              user: User = Depends(get_current_user),
                              services: Services = Depends(get_services)):
    character = await services.character_service.get_by_id(character_id)
    if character.user.username != user.username:
        raise HTTPException(400, detail=f'User {user.username} does not match character')
    return character


@router.patch('/{character_id}', response_model=CharacterSchema)
async def change_character(character_id: int,
                         edit_character: EditCharacterSchema,
                         services: Services = Depends(get_services)):
    character = await services.character_service.get_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    try:
        if edit_character.name is not None:
            character.name = edit_character.name

        if edit_character.avatar is not None:
            character.avatar = edit_character.avatar

        if edit_character.race_id is not None:
            race = await services.race_service.get_by_id(edit_character.race_id)
            if race is None:
                raise HTTPException(status_code=400, detail="Invalid race ID")
            character.race_id = race.id

        if edit_character.class_id is not None:
            character_class = await services.class_service.get_by_id(edit_character.class_id)
            if character_class is None:
                raise HTTPException(status_code=400, detail="Invalid class ID")
            character.class_id = character_class.id

            if edit_character.subclass_id is not None:
                for subclass in character_class.subclasses:
                    if subclass.id == edit_character.subclass_id:
                        character.subclass_id = subclass.id
                        break
                else:
                    raise HTTPException(400,
                                        detail=f'Character class with id {character_class.id} has no subclass with id {edit_character.subclass_id}')

        if edit_character.character_type is not None:
            character.character_type = CharacterType(edit_character.character_type)

        if edit_character.summand_params is not None:
            summand_params_model = SummandParams(**edit_character.summand_params.model_dump())
            updated_summand_params = await services.params_service.update(character.summand_params_id,
                                                                          summand_params_model)
            character.summand_params_id = updated_summand_params.id

        if edit_character.multiplier_params is not None:
            multiplier_params_model = MultiplierParams(**edit_character.multiplier_params.model_dump())
            updated_multiplier_params = await services.params_service.update(character.multiplier_params_id,
                                                                             multiplier_params_model)
            character.multiplier_params_id = updated_multiplier_params.id

        if edit_character.item_ids is not None:
            items = await services.item_service.get_by_ids(edit_character.item_ids)
            tiers_items = {}
            for item in items:
                if not tiers_items.get(item.tier):
                    tiers_items.setdefault(item.tier, item)
                else:
                    raise HTTPException(400, detail=f'Two items of tier {item.tier} cannot be')
            character.items = items

        if edit_character.ability_ids is not None:
            abilities = await services.ability_service.get_by_ids(edit_character.ability_ids)
            tiers_abilities = {}
            for ability in abilities:
                if (not tiers_abilities.get(ability.tier)) or (ability.tier == 0):
                    tiers_abilities.setdefault(ability.tier, abilities)
                else:
                    raise HTTPException(400, f'Two abilities of tier {ability.tier} cannot be')
            character.abilities = abilities

        if edit_character.stardom is not None:
            character.stardom = edit_character.stardom

        if edit_character.level is not None:
            character.level = edit_character.level
            # Это должно быть не тут, но об этом чуть позже
            character_controller = CharacterController(character)
            character.power = character_controller.calculate_character_power()

        # if edit_character.power is not None:


        updated_character = await services.character_service.update(character_id, character)
        return updated_character

    except Exception as e:
        print(e.with_traceback())
        raise HTTPException(400, detail=str(e))


@router.delete('/{character_id}')
async def delete_character(character_id: int,
                           user: User = Depends(get_current_user),
                           services: Services = Depends(get_services)):
    await services.character_service.delete_by_id_by_user(character_id, user.id)
    return {'message': 'ok'}