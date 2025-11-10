from odoo import fields, models


class AIConfig(models.Model):
    _inherit = 'ai.config'

    type = fields.Selection(
        selection_add=[('gemini', 'Gemini')],
        ondelete={'gemini': 'cascade'}
    )

    def _get_default_model(self):
        if self.type == 'gemini':
            return 'gemini-2.5-flash'
        return super()._get_default_model()
