from fastapi import HTTPException
from sqlalchemy import select

from game_logic.models.models import SummandParams, MultiplierParams
from game_logic.services.service import Service


class ParamsService(Service):
    async def update(self, params_id: int, params_data):
        if isinstance(params_data, SummandParams):
            param_model = SummandParams
        elif isinstance(params_data, MultiplierParams):
            param_model = MultiplierParams
        else:
            raise HTTPException(400, detail="Invalid parameters type")

        result = await self.session.execute(select(param_model).where(param_model.id == params_id))
        params = result.scalars().first()

        if not params:
            raise HTTPException(404, detail=f"Params with id {params_id} not found")

        for field, value in params_data.__dict__.items():
            if value is not None:
                setattr(params, field, value)

        self.session.add(params)
        await self.session.commit()

        return params