from odoo import fields, models


class AIConfig(models.Model):
    _inherit = 'ai.config'

    type = fields.Selection(
        selection_add=[('claude', 'Claude')],
        ondelete={'claude': 'cascade'}
    )

    def _get_default_model(self):
        if self.type == 'claude':
            return 'claude-3-5-haiku-latest'
        return super()._get_default_model()
