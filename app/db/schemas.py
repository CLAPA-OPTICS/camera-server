from pydantic import BaseModel


class ParamsBase(BaseModel):
    #name: str | None
    #cross_line_x: int | None
    #cross_line_y: int | None
    gain: int | None
    gamma: int | None
    contrast: int | None
    exposure_time: int | None

class ParamsCreate(ParamsBase):
    pass


class Params(ParamsBase):
    id: int
    class Config:
        orm_mode: True
