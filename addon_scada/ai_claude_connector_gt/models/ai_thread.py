import json
from anthropic import Anthropic
from anthropic._types import NOT_GIVEN
from odoo import models, _
from odoo.exceptions import UserError


class AIThread(models.Model):
    _inherit = 'ai.thread'

    def _get_tools_spec_claude(self):
        tools = self._get_tools_spec()
        for tool in tools:
            tool['input_schema'] = tool.pop('parameters')
        return tools

    def _do_request_claude(self, message):
        """Handle Claude API request"""
        self.ensure_one()
        config = self.config_id.sudo()

        if not config.api_key:
            raise UserError(_("Claude API key is not configured"))

        # Initialize Claude client
        client = Anthropic(api_key=config.api_key)

        # Add system context if exists
        system_message = None
        if thread_context := self._get_thread_context():
            system_message = thread_context

        # Add conversation history
        messages = self._prepare_message_history_claude(self.message_ids)

        try:
            return client.messages.create(
                model=config.model,
                system=system_message or NOT_GIVEN,
                messages=messages,
                tools=self._get_tools_spec_claude() or NOT_GIVEN,
                tool_choice={
                    "type": "auto",
                    "disable_parallel_tool_use": True
                },
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )

        except Exception as e:
            raise UserError(_("Claude API Error: %s") % str(e))

    def _prepare_message_history_claude(self, messages):
        self.ensure_one()
        message_history = []
        for msg in messages:
            message = {
                "role": "assistant" if msg.message_type == 'response' else "user",
                "content": msg._prepare_message_content_claude(),
            }
            message_history.append(message)
        return message_history

    def _parse_response_tool_claude(self, response):
        content = next((c for c in response.content if c.type == 'tool_use'), None)
        if content:
            return content.model_dump()
        return False

    def _execute_tool_claude(self, func_call):
        return self._run_tool(func_call['name'], **func_call['input'])

    def _parse_response_text_claude(self, response):
        """Parse Claude response content"""
        content = next((c for c in response.content if c.type == 'text'), None)
        return content and content.text
