import pydantic
from typing import Optional

from pydantic import Json

from . import utils


class Category(pydantic.BaseModel):
    id: int
    name: str
    complete_name: Optional[str] = None
    parent_path: str
    guid: Optional[str] = None

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
