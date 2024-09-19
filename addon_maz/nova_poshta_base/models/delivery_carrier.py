# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.exceptions import UserError


class DeliveryCarrieNovaPoshta(models.Model):
    _inherit = 'delivery.carrier'

    is_novaposhta = fields.Boolean(compute='_compute_is_novaposhta', search='_search_is_novaposhta')

    @api.depends('product_id.default_code')
    def _compute_is_novaposhta(self):
        for c in self:
            c.is_novaposhta = c.product_id.default_code == "Delivery_NP"

    def _search_is_novaposhta(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise UserError(_("Operation not supported"))
        if not value:
            operator = '!=' if operator == '=' else '='
        return [('product_id.default_code', operator, 'Delivery_NP')]
