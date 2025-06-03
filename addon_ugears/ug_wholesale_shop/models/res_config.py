from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_confirmation = fields.Boolean(
        string='Send confirmation email',
        config_parameter='distrib.send_confirmation',
        help="Send email after order confirmation.",
    )