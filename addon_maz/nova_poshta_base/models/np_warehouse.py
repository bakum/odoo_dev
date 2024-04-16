from odoo import api, fields, models, _


class NovaPoshtaWarehouse(models.Model):
    _name = "nova.poshta.warehouse"
    _description = 'Nova Poshta Warehouses'

    ref = fields.Char(string='Ref')
    name = fields.Char(string='Name')
    name_ru = fields.Char(string='Name (RU)')
    type = fields.Char(string='Type of warehouse')
    site_key = fields.Integer(string='Warehouse Code')
    number = fields.Integer(string='Warehouse Number')
    city_ref = fields.Char(string='City Ref')
    city_description = fields.Char(string='City Description')
    city_description_ru = fields.Char(string='City Description (RU)')

    _sql_constraints = [
        ('nova_poshta_warehouse_ref_uniq',
         'UNIQUE (ref)',
         'Warehouse Ref must be unique!')
    ]
