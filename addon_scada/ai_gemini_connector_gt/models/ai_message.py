import json
from odoo import models


class AIMessage(models.Model):
    _inherit = "ai.message"

    def _filter_legit_attachments(self):
        # Gemini currently only supports images. For other types, users must upload them to Google Cloud Storage.
        # We'll implement this in the future. For now, we'll just use the images.
        if self.thread_id.config_id.sudo().type == "gemini":
            return self.attachment_ids.filtered(
                lambda a: a.mimetype.startswith("image/")
            )
        return super()._filter_legit_attachments()

    def _prepare_message_parts_gemini(self):
        self.ensure_one()
        message = []
        if self.content:
            message.append({"text": self.content_full})
        if self.func_result:
            func_call = json.loads(self.func_call)
            message.append(
                {
                    "function_response": {
                        "id": func_call.get("id", None),
                        "name": func_call.get("name", None),
                        "response": {"result": json.loads(self.func_result)},
                    }
                }
            )
        elif self.func_call:
            message.append({"function_call": json.loads(self.func_call)})
        if self.legit_attachment_ids:
            message.extend(
                [
                    {
                        "inline_data": {
                            "mime_type": attachment.mimetype,
                            "data": attachment.datas.decode("utf-8"),
                        }
                    }
                    for attachment in self.legit_attachment_ids
                ]
            )
        return message
