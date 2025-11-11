import json
from odoo import models


class AIMessage(models.Model):
    _inherit = 'ai.message'

    def _filter_legit_attachments(self):
        # Claude currently supports images and pdf  
        if self.thread_id.config_id.sudo().type == 'claude':
            return self.attachment_ids.filtered(
                lambda att: att.mimetype.startswith('image/') or att.mimetype == 'application/pdf'
            )
        return super()._filter_legit_attachments()

    def _prepare_message_content_claude(self):
        self.ensure_one()
        content = []
        if self.content:
            content.append({
                "type": "text",
                "text": self.content_full
            })
        if self.legit_attachment_ids:
            content.extend([{
                "type": "image" if attachment.mimetype.startswith('image/') else "document",
                "source": {
                        "type": "base64",
                        "media_type": attachment.mimetype,
                        "data": attachment.datas.decode('utf-8')
                    }
                } for attachment in self.legit_attachment_ids])

        if self.func_result:
            content.append({
                "tool_use_id": json.loads(self.func_call).get('id', None),
                "type": "tool_result",
                "content": self.func_result
            })
        elif self.func_call:
            content.append(json.loads(self.func_call))
        return content
