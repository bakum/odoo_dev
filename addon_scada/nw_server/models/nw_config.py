from odoo import fields, models


class NwConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dey_count_to_clear = fields.Integer(string='Last days count',
                                        default=90,
                                        config_parameter='nw_server.default_last_dey_count', )

    for_stable_data = fields.Boolean(string='Stable data only',
                                        config_parameter='nw_server.default_for_stable_data', )
