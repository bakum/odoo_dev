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
    shop_default_category_id = fields.Many2one('product.public.category', string='Default shop category',
                                               config_parameter='distrib.default_shop_category_id',
                                               help="Category selected when the wholesale shop is opened from the menu. If not set, all products are shown.")
