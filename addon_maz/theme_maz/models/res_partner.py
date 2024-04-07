from odoo import api, models, _, fields


class PartnerDivision(models.Model):
    _inherit = "res.partner"

    division_id = fields.Many2one('maz.divisions', "Division")