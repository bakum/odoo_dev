import json
import openai
from openai._types import NOT_GIVEN
from odoo import models, _
from odoo.exceptions import UserError
from odoo.addons.ai_base_gt.models.ai_thread import MESSAGE_TYPE_ROLE_MAP


class AIThread(models.Model):
    _inherit = 'ai.thread'

    def _get_tools_spec_chatgpt(self):
        tools = [{
            'type': 'function',
            'function': tool
        } for tool in self._get_tools_spec()]
        return tools

    def _do_request_chatgpt(self, message):
        """Handle ChatGPT API request"""
        self.ensure_one()
        config = self.config_id.sudo()

        if not config.api_key:
            raise UserError(_("ChatGPT API key is not configured"))

        client = openai.OpenAI(api_key=config.api_key)

        # Prepare message history
        messages = []
        if thread_context := self._get_thread_context():
            messages.append({
                "role": "system",
                "content": thread_context,
            })

        # Add conversation history
        messages.extend(self._prepare_message_history_chatgpt(self.message_ids))

        try:
            return client.chat.completions.create(
                model=config.model,
                messages=messages,
                tools=self._get_tools_spec_chatgpt() or NOT_GIVEN,
                parallel_tool_calls=False,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        except Exception as e:
            raise UserError(_("ChatGPT API Error: %s") % str(e))

    def _prepare_message_history_chatgpt(self, messages):
        self.ensure_one()
        message_history = []
        for msg in messages:
            message = {
                'role': MESSAGE_TYPE_ROLE_MAP[msg.message_type],
                'content': [],
            }

            if msg.content:
                message["content"].append({
                    "type": "text",
                    "text": msg.content_full
                })
            if msg.legit_attachment_ids:
                message["content"].extend([{
                    "type": "image_url",
                    "image_url": {"url": f"data:{attachment.mimetype};base64,{attachment.datas.decode('utf-8')}"}
                    } for attachment in msg.legit_attachment_ids])

            if msg.func_result:
                message['role'] = 'tool'
                message['tool_call_id'] = json.loads(msg.func_call).get('id', None)
                message["content"].append({
                    "type": "text",
                    "text": msg.func_result
                })
            elif msg.func_call:
                message["tool_calls"] = [json.loads(msg.func_call)]

            message_history.append(message)
        return message_history

    def _parse_response_tool_chatgpt(self, response):
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            return tool_call.model_dump()
        return False

    def _execute_tool_chatgpt(self, func_call):
        func_name = func_call['function']['name']
        arguments = json.loads(func_call['function']['arguments'])
        return self._run_tool(func_name, **arguments)

    def _parse_response_text_chatgpt(self, response):
        """Parse ChatGPT response content"""
        return response.choices[0].message.content
