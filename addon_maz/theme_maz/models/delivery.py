from odoo import models, fields


class MazDelivery(models.Model):
    _inherit = "delivery.carrier"

    guid = fields.Char(string='Guid 1C:Enterprise')
