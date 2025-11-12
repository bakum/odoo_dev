from odoo import fields, models


class AIConfig(models.Model):
    _inherit = 'ai.config'

    type = fields.Selection(
        selection_add=[('chatgpt', 'ChatGPT')],
        ondelete={'chatgpt': 'cascade'}
    )

    def _get_default_model(self):
        if self.type == 'chatgpt':
            return 'gpt-4.1-mini'
        return super()._get_default_model()
