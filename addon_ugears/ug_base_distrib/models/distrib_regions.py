from odoo import fields, models, api


class ModelName(models.Model):
    _name = 'distrib.regions'
    _description = 'Regions'

    name = fields.Char(string='Name', required=True)
    desc = fields.Text(string='Description', required=True)
    active = fields.Boolean(default=True)
