from odoo import models, fields


class MazSaleOrder(models.Model):
    _inherit = "sale.order"

    guid = fields.Char(string='Guid 1C:Enterprise')
