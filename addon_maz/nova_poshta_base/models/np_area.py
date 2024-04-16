from odoo import api, fields, models, _


class NovaPoshtaArea(models.Model):
    _name = "nova.poshta.area"
    _description = 'Nova Poshta Areas'

    ref = fields.Char(string='Ref')
    name = fields.Char(string='Area Name')
    center = fields.Char(string='Areas Center')

    _sql_constraints = [
        ('nova_poshta_area_ref_uniq',
         'UNIQUE (ref)',
         'Area Ref must be unique!')
    ]
