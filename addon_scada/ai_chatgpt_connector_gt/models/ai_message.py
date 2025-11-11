from odoo import models


class AIMessage(models.Model):
    _inherit = 'ai.message'

    def _filter_legit_attachments(self):
        # ChatGPT currently only supports images
        if self.thread_id.config_id.sudo().type == 'chatgpt':
            return self.attachment_ids.filtered(
                lambda att: att.mimetype.startswith('image/')
            )
        return super()._filter_legit_attachments()
