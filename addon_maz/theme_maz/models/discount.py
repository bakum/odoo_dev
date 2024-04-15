from datetime import datetime
from odoo import models, fields


class CurrentDiscounts(models.Model):
    _name = 'maz.discount'
    _description = 'Discounts'
    _order = 'use_from desc'

    discount = fields.Integer(string="Discount", default=0)
    use_from = fields.Date(string="Use from", default=datetime.today(), copy=False)
