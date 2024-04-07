from odoo import models, fields


class Divisions(models.Model):
    _name = 'maz.divisions'
    _description = 'Divisions'

    name = fields.Char(string='Name',translate=True)
    email = fields.Char(string='Email')
    guid = fields.Char(string='Guid 1C:Enterprise')
    active = fields.Boolean(default=True)
