from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def _get_active_category(self):
        category = self.env['product.public.category'].sudo().search([])
        return category
