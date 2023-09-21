from odoo import api, models, _, fields


class UsersDistrib(models.Model):
    _inherit = "res.users"

    distrib_id = fields.Many2one('distrib.distributors', "Distributor")
    # stock_id = fields.Many2one('stock.location', compute="_compute_location", store=True)
    #
    # @api.depends('distrib_id')
    # def _compute_location(self):
    #     for rec in self:
    #         rec.stock_id = self.distrib_id.stock_id
