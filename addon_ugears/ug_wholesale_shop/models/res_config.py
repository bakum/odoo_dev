from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_confirmation = fields.Boolean(
        string='Send confirmation email',
        config_parameter='distrib.send_confirmation',
        help="Send email after order confirmation.",
    )
    beneficiary = fields.Many2one('res.partner', string='Default beneficiary', default_model='res.partner',
                                          config_parameter='distrib.default_beneficiary',
                                          help="Default beneficiary for wholesale orders. If not set, the company will be used.")
