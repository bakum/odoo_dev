from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    accounting_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Distributor accounting currency',
        config_parameter='ug_base_distrib.default_currency_accounting',
        help="Currency of multi-currency accounting of distributors.",
    )
