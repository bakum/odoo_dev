import pydantic
from typing import Any

from pydantic import Json

from . import utils


class Category(pydantic.BaseModel):
    id: int
    name: str
    complete_name: str | None
    parent_path: str
    guid: str | None

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
