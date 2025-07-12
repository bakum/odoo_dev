from odoo import http
from odoo.http import request

from langdetect import detect

class ChatController(http.Controller):
    @http.route('/llm/chat/send', type='json', auth='user')
    def send(self, session_id, text):
        lang = detect(text)
        instructions = {
            'ru': "Ты — помощник, который говорит только по-русски. Веди диалог на русском. Отвечай на русском языке.",
            'uk': "Ти помічник, який говорить тільки українською. Веди діалог українською. Відповідай українською мовою.",
            'en': "You are an assistant who speaks only English. Conduct a dialogue in English. Answer in English.",
        }
        instruction = instructions.get(lang, "You are an assistant who speaks only English. Answer in the language of the question.")

        # 1. Сохраняем пользовательское сообщение
        user_msg = request.env['llm.chat.message'].sudo().create({
            'session_id': session_id,
            'author': 'user',
            'content': text,
        })

        # 2. Retrieval: semantic search топ-3
        vector_svc = request.env['llm.vector.service'].sudo()
        retrieved = vector_svc.semantic_search(text, k=3)

        # 3. Формируем контекст
        context_parts = []
        for doc, dist in retrieved:
            if doc.text_content:
                snippet = doc.text_content[:1000] + '...' if len(doc.text_content) > 1000 else doc.text_content
                context_parts.append(f"{doc.name} (dist={dist:.3f}):\n{snippet}")
        context = "\n\n".join(context_parts)

        # 4. Собираем промпт с контекстом
        augmented_prompt = (
            f"{instruction}\n\n"
            "Ниже представлена релевантная информация из документов. Используйте её при ответе.:\n\n"
            f"{context}\n\nВопрос: {text}"
        )

        # 5. Генерация ответа
        bot_text = request.env['llm.embedding_service'].sudo().generate_text(augmented_prompt)

        # 6. Сохраняем сообщение бота
        bot_msg = request.env['llm.chat.message'].sudo().create({
            'session_id': session_id,
            'author': 'bot',
            'content': bot_text,
        })

        return {
            'user': {'id': user_msg.id, 'content': user_msg.content, 'date': str(user_msg.date)},
            'bot':  {'id': bot_msg.id,  'content': bot_msg.content,  'date': str(bot_msg.date)},
        }