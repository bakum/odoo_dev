# import requests
# from odoo import api, models
#
# class LLMService(models.AbstractModel):
#     _name = "llm.service"
#     _description = "LLM API Service"
#
#     @api.model
#     def _get_api_key(self):
#         return self.env['ir.config_parameter'].sudo().get_param('odoo_llm.api_key')
#
#
#     @api.model
#     def generate(self, prompt, model="gpt-4"):
#         api_key = self._get_api_key()
#         res = requests.post(
#             "https://api.openai.com/v1/chat/completions",
#             json={
#                 "model": model,
#                 "messages": [{"role": "user", "content": prompt}]
#             },
#             headers={"Authorization": f"Bearer {api_key}"}
#         )
#         res.raise_for_status()
#         return res.json()["choices"][0]["message"]["content"]

import requests
from odoo import api, models
import json

class LLMService(models.AbstractModel):
    _name = "llm.service"
    _description = "Advanced Ollama LLM Service"

    @api.model
    def _get_model_name(self):
        return self.env['ir.config_parameter'].sudo().get_param('ollama.model_name', default='llama2')

    @api.model
    def _get_history(self, topic="default"):
        # Получаем историю диалога из параметра, можно реализовать хранение в модели или сессии
        history_json = self.env['ir.config_parameter'].sudo().get_param(f"ollama.chat_history.{topic}", default="[]")
        return json.loads(history_json)

    @api.model
    def _save_history(self, topic, history):
        history_json = json.dumps(history[-10:])  # сохраняем последние 10 сообщений
        self.env['ir.config_parameter'].sudo().set_param(f"ollama.chat_history.{topic}", history_json)

    @api.model
    def generate(self, user_input, topic="default"):
        model = self._get_model_name()
        history = self._get_history(topic)

        # Добавляем новое сообщение пользователя
        history.append({"role": "user", "content": user_input})

        # Готовим payload для Ollama
        messages = [{"role": h["role"], "content": h["content"]} for h in history]

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False
            }
        )
        response.raise_for_status()
        reply = response.json()["message"]["content"]

        # Добавляем ответ ассистента в историю и сохраняем
        history.append({"role": "assistant", "content": reply})
        self._save_history(topic, history)

        return reply