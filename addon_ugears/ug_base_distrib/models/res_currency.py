from odoo import models, fields, api


class ResCurrency(models.Model):
    _inherit = "res.currency"
    code = fields.Char(string='Code of currency', size=3)

    @api.model
    def _update_val_code(self):
        for vals in self.search([('name','=','USD')]):
            vals.code = "840"
        for vals in self.search([('name','=','EUR')]):
            vals.code = "978"
        for vals in self.search([('name','=','UAH')]):
            vals.code = "980"
