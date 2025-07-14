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
        instruction = instructions.get(lang, "Ти помічник, який говорить тільки українською. Веди діалог українською. Відповідай українською мовою.")

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
            "Нижче надано релевантну інформацію з документів. Використовуй її при відповіді.\n\n"
            f"{context}\n\nВопрос: {text}"
        )

        # 5. Генерация ответа
        try:
            bot_text = request.env['llm.embedding_service'].sudo().generate_text(augmented_prompt)
        except ConnectionError as e:
            return {
                'success': False,
                'error': str(e),
            }

        # 6. Сохраняем сообщение бота
        bot_msg = request.env['llm.chat.message'].sudo().create({
            'session_id': session_id,
            'author': 'bot',
            'content': bot_text,
        })

        return {
            'success': True,
            'user': {'id': user_msg.id, 'content': user_msg.content, 'date': str(user_msg.date)},
            'bot':  {'id': bot_msg.id,  'content': bot_msg.content,  'date': str(bot_msg.date)},
        }

    @http.route('/llm/chat/session/<int:session_id>', type='json', auth='user')
    def load_session(self, session_id):
        session = request.env['llm.chat.session'].sudo().browse(session_id)
        if not session.exists():
            return request.not_found()

        messages = session.message_ids.sudo().search([], order='id asc')[:-20]  # Last 20 messages for performance
        llm_messages = [
            {'role': 'user' if m.author == 'user' else 'assistant', 'content': m.content}
            for m in messages
        ]

        try:
            bot_text = request.env['llm.embedding_service'].sudo().set_context(llm_messages)
        except ConnectionError as e:
            return {
                'success': False,
                'session_id': session.id,
                'bot_text': str(e),
            }

        return {
            'success': True,
            'session_id': session.id,
            'bot_text': bot_text,
        }
