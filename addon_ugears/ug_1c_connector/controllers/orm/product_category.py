from typing import Optional, List

import pydantic

from . import utils


class Company(pydantic.BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class Category(pydantic.BaseModel):
    id: int
    name: str
    complete_name: Optional[str] = None
    parent_path: str
    guid: Optional[str] = None

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class Product(pydantic.BaseModel):
    id: int
    categ_id: Category
    name: str
    type: str
    guid: Optional[str] = None

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class Currency(pydantic.BaseModel):
    id: int
    name: str
    code: Optional[str] = None

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class PricelistItem(pydantic.BaseModel):
    id: int
    pricelist_id: int
    product_id: Optional[Product] = None
    product_tmpl_id: Optional[Product] = None
    currency_id: Optional[Currency] = None
    compute_price: str
    fixed_price: Optional[int] = None
    min_quantity: Optional[int] = None
    date_start: Optional[str]
    date_end: Optional[str]

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class Pricelist(pydantic.BaseModel):
    id: int
    currency_id: Currency
    name: str
    guid: Optional[str] = None
    item_ids: List[PricelistItem]

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class Rates(pydantic.BaseModel):
    id: int
    name: str
    currency_id: Currency
    company_id: int
    rate: float

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class Theme(pydantic.BaseModel):
    id: int
    name: str
    guid: Optional[str] = None
    product_ids: List[Product]

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class SalesChannels(pydantic.BaseModel):
    id: int
    name: str
    guid: Optional[str] = None

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
