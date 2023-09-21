from odoo import api, models, _, fields


class UsersDistrib(models.Model):
    _inherit = "res.users"

    distrib_id = fields.Many2one('distrib.distributors', "Distributor")
