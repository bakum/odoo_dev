from odoo import api, fields, models, _
from odoo.osv import expression


class NovaPoshtaCity(models.Model):
    _name = "nova.poshta.city"
    _description = 'Nova Poshta Cities'
    _order = "code"

    ref = fields.Char(string='Ref')
    name = fields.Char(string='Name')
    name_ru = fields.Char(string='Name (RU)')
    code = fields.Integer(string='City ID')
    area = fields.Char(string='Area')
    area_id = fields.Many2one('nova.poshta.area', string='Area')
    settlement_type = fields.Char(string='Settlement Type')
    settlement_type_description = fields.Char(
        string='Settlement Type Description'
    )
    settlement_type_description_ru = fields.Char(
        string='Settlement Type Description (RU)'
    )
    delivery_1 = fields.Boolean(string='Delivery on Monday')
    delivery_2 = fields.Boolean(string='Delivery on Tuesday')
    delivery_3 = fields.Boolean(string='Delivery on Wednesday')
    delivery_4 = fields.Boolean(string='Delivery on Thursday')
    delivery_5 = fields.Boolean(string='Delivery on Friday')
    delivery_6 = fields.Boolean(string='Delivery on Saturday')
    delivery_7 = fields.Boolean(string='Delivery on Sunday')

    _sql_constraints = [
        ('nova_poshta_city_ref_uniq',
         'UNIQUE (ref)',
         'City Reference must be unique!')
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator in ('ilike', 'like', '=', '=like', '=ilike'):
            domain = expression.AND([
                args or [],
                ['|', ('name_ru', operator, name), ('name', operator, name)]
            ])
            recs = self.search(domain, limit=limit)
            return recs.name_get()
        return super(NovaPoshtaCity, self).name_search(name, args, operator, limit)
