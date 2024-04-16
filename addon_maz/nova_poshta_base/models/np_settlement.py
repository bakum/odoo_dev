import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class NovaPoshtaSettlement(models.Model):
    _name = "nova.poshta.settlement"
    _description = 'Nova Poshta Settlements'

    ref = fields.Char(string='Ref')
    name = fields.Char(string='Name')
    name_ru = fields.Char(string='Name (RU)')
    type = fields.Char(string='Settlement Type')
    type_description = fields.Char(string='Type Description')
    type_description_ru = fields.Char(string='Type Description (RU)')
    latitude = fields.Char(string='Latitude')
    longitude = fields.Char(string='Longitude')
    area = fields.Char(string='Area')
    area_id = fields.Many2one('nova.poshta.area', string='Area')
    region = fields.Char(string='Region')
    region_description = fields.Char(string='Region Description')
    region_description_ru = fields.Char(string='Region Description (RU)')
    index_1 = fields.Char(string='Index 1')
    index_2 = fields.Char(string='Index 2')
    index_coatsu_1 = fields.Char(string='Index COATSU 1')
    delivery_1 = fields.Boolean(string='Delivery on Monday')
    delivery_2 = fields.Boolean(string='Delivery on Tuesday')
    delivery_3 = fields.Boolean(string='Delivery on Wednesday')
    delivery_4 = fields.Boolean(string='Delivery on Thursday')
    delivery_5 = fields.Boolean(string='Delivery on Friday')
    delivery_6 = fields.Boolean(string='Delivery on Saturday')
    delivery_7 = fields.Boolean(string='Delivery on Sunday')
    warehouse = fields.Integer(string='Warehouse')

    _sql_constraints = [
        ('nova_poshta_settlement_ref_uniq',
         'UNIQUE (ref)',
         'Settlement Ref must be unique!')
    ]
