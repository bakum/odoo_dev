from odoo import api, models, _, fields


class UsersDistrib(models.Model):
    _inherit = "res.users"

    division_id = fields.Many2one('maz.divisions', "Division")
