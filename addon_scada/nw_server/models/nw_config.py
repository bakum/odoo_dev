from odoo import fields, models


class NwConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dey_count_to_clear = fields.Integer(string='Last days count',
                                        default=90,
                                        config_parameter='nw_server.default_last_dey_count', )
