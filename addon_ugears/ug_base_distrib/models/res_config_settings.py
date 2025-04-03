from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    accounting_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Distributor accounting currency',
        config_parameter='ug_base_distrib.default_currency_accounting',
        help="Currency of multi-currency accounting of distributors.",
    )
    report_period = fields.Integer(
        string='Distributor accounting report period',
        config_parameter='distrib.report_distrib_quantity_period',
        help="Period in Months for reports.",
    )
    restrict_date = fields.Datetime(
        string='Date of prohibition of data editing',
        config_parameter='distrib.restrict_date',
        help="Changes to data before this date inclusive are prohibited.",
    )
    danger_limit = fields.Integer(
        string='Limit for execution of dangerous operations',
        config_parameter='distrib.danger_limit',
        help="Set null to disable the limit.",
    )
