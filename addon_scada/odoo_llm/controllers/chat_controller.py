import time

from odoo import http
from odoo.http import request
import logging

from langdetect import detect
from werkzeug.urls import url_quote

_logger = logging.getLogger(__name__)

from ..services.prompt_builder import PromptBuilder


class ChatController(http.Controller):

    @classmethod
    def _deduplicate_links(self, links):
        """Удаляет дублирующиеся ссылки по name + url."""
        seen = set()
        unique = []
        for l in links:
            key = (l['name'], l['url'])
            if key not in seen:
                seen.add(key)
                unique.append(l)
        return unique

    @http.route('/llm/chat/stream/<int:identification>', type='http', auth='public')
    def stream_chat(self, identification, **kwargs):
        # session_id = int(kwargs.get('session_id', 0))
        text = kwargs.get('text', '')
        session = request.env['llm.chat.session'].sudo().browse(identification)

        messages = request.env['llm.chat.message'].sudo().search(
            [('session_id', '=', identification)], order='id desc', limit=5)
        messages = reversed(messages)

        llm_messages = [
            {'role': 'user' if m.author == 'user' else 'assistant', 'content': m.content}
            for m in messages
        ]

        is_new_session = len(llm_messages) == 0
        lang = session.lang or 'uk'
        if is_new_session:
            detected = detect(text)
            lang = detected if detected in ('ru', 'uk', 'en') else 'uk'
            session.write({'lang': lang})
            llm_messages.insert(0, {'role': 'system', 'content': PromptBuilder.get_instruction(lang)})

        vector_svc = request.env['llm.vector.service'].sudo()
        retrieved = vector_svc.semantic_search(text, k=5)
        threshold = PromptBuilder.get_threshold()
        retrieved = sorted([t for t in retrieved if t[1] <= threshold], key=lambda t: t[1])
        prompt, links = PromptBuilder.build_prompt(text, lang, retrieved, request.httprequest.host_url)

        def event_stream():
            last_ping = time.time()
            try:
                for chunk in request.env['llm.embedding_service'].sudo().stream_text(prompt=prompt,
                                                                                     history=llm_messages):
                    yield f"data: {chunk}\n\n"
                    # if time.time() - last_ping > 30:
                    #     yield "data: : keepalive\n\n"  # SSE-комментарий, для поддержания соединения
                    #     last_ping = time.time()
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"

        return request.make_response(event_stream(), [('Content-Type', 'text/event-stream')])

    @http.route('/llm/chat/send', type='json', auth='user')
    def send(self, session_id, text):
        session = request.env['llm.chat.session'].sudo().browse(session_id)

        llm_messages = []
        if session.exists():
            # is_new_session = False
            messages = request.env['llm.chat.message'].sudo().search([('session_id', '=', session_id)], order='id desc',
                                                                     limit=5)  # Last 20 messages for performance

            messages = reversed(messages)
            llm_messages = [
                {'role': 'user' if m.author == 'user' else 'assistant', 'content': m.content}
                for m in messages
            ]
        is_new_session = len(llm_messages) == 0
        detected = detect(text) if is_new_session else session.lang
        lang = detected if detected in ('ru', 'uk', 'en') else 'uk'
        if is_new_session:
            session.write({'lang': lang})

        # instructions = {
        #     'ru': "Ты помощник, который говорит только по-русски. Веди диалог на русском. Отвечай на русском языке.",
        #     'uk': "Ти помічник, який говорить тільки українською. Веди діалог українською. Відповідай українською мовою.",
        #     'en': "You are an assistant who speaks only English. Conduct a dialogue in English. Answer in English.",
        # }
        # instruction = instructions.get(lang, instructions['uk'])

        # 1. Сохраняем пользовательское сообщение
        user_msg = request.env['llm.chat.message'].sudo().create({
            'session_id': session_id,
            'author': 'user',
            'content': text,
        })

        # 2. Retrieval: semantic search топ-3
        vector_svc = request.env['llm.vector.service'].sudo()
        retrieved = vector_svc.semantic_search(text, k=5)
        THRESHOLD = PromptBuilder.get_threshold()
        retrieved = sorted(
            [t for t in retrieved if t[1] <= THRESHOLD],
            key=lambda t: t[1]
        )

        # 3. Формируем контекст
        # context_parts = []
        # seen_docs = set()
        # links = []
        # for doc, dist in retrieved:
        #     # if dist > 10.3:  # <-- фильтруем нерелевантные документы
        #     #     _logger.debug(f"Doc '{doc.name}' skipped: dist={dist:.3f} > 0.3")
        #     #     continue
        #     if not doc.id or doc.id in seen_docs:
        #         continue
        #     seen_docs.add(doc.id)
        #     if doc.text:
        #         snippet = doc.text[:500] + '...' if len(doc.text) > 500 else doc.text
        #         # snippet = doc.text_content
        #         base_url = request.httprequest.host_url
        #         safe_name = url_quote(doc.document_id.name)
        #         download_url = f"{base_url}web/content/llm.document/{doc.document_id.id}/file/{safe_name}"
        #         context_parts.append(
        #             f"`{doc.document_id.name}` (dist={dist:.3f}):\n{snippet}\n[`{doc.document_id.name}`](`{download_url}`)")
        #         # context_parts.append(f"{doc.name} (dist={dist:.3f}):\n{snippet}")
        #         links.append({'name': doc.document_id.name, 'url': download_url})
        # context = "\n\n".join(context_parts)
        #
        # question_labels = {'ru': 'Вопрос', 'uk': 'Питання', 'en': 'Question'}
        # question_label = question_labels.get(lang, question_labels['uk'])
        #
        # 4. Собираем промпт с контекстом
        # augmented_prompt = (
        #     # f"{instruction if is_new_session else ''}\n\n"
        #     # "Використовуй наведені документи лише якщо вони безпосередньо відповідають на питання. "
        #     # "Якщо ні — не згадуй їх. Не вигадуй джерела. Не вставляй посилання, якщо не впевнений.\n\n"
        #     "Не перекладай та не змінюй назви файлів. "
        #     "Завжди зберігай їх у точності як є, включаючи розширення (.pdf, .docx і т.д.), символи та регістр.\n\n"
        #     "Обгорни назви файлів у зворотні апострофи: ``назва_файлу.pdf``. "
        #     "Надай посилання на наведені документи. Не вставляй посилання, якщо не впевнений.\n\n"
        #     "Нижче надано релевантну інформацію з документів. Використовуй її при відповіді.\n\n"
        #     "Якщо вона не відповідає на запитання, скажи, що не знайшов інформації і не вигадуй."
        #     f"{context}\n\n{question_label}: {text}"
        # )

        # 3–4. Строим промпт и получаем список ссылок
        augmented_prompt, links = PromptBuilder.build_prompt(
            text=text,
            lang=lang,
            retrieved_docs=retrieved,
            base_url=request.httprequest.host_url
        )

        if is_new_session:
            llm_messages.insert(0, {'role': 'system', 'content': PromptBuilder.get_instruction(lang=lang)})

        # 5. Генерация ответа
        try:
            bot_text = request.env['llm.embedding_service'].sudo().generate_text(prompt=augmented_prompt,
                                                                                 history=llm_messages)
        except Exception as e:
            _logger.exception("LLM error: " + str(e))
            return {
                'success': False,
                'error': str(e),
            }

        unique_links = self._deduplicate_links(links)

        # Добавим ссылки, только если их нет в тексте
        if bot_text and not all(f"{l['name']}: {l['url']}" in bot_text for l in unique_links):
            links_text = "\n\nДодаткові посилання:\n" + "\n".join(f"{l['name']}: {l['url']}" for l in unique_links)
            bot_text += links_text

        # 6. Сохраняем сообщение бота
        bot_msg = request.env['llm.chat.message'].sudo().create({
            'session_id': session_id,
            'author': 'bot',
            'content': bot_text,
        })

        return {
            'success': True,
            'user': {'id': user_msg.id, 'content': user_msg.content, 'date': str(user_msg.date)},
            'bot': {'id': bot_msg.id, 'content': bot_msg.content, 'date': str(bot_msg.date)},
        }

    @http.route('/llm/chat/session/<int:session_id>', type='json', auth='user')
    def load_session(self, session_id):
        session = request.env['llm.chat.session'].sudo().browse(session_id)
        if not session.exists():
            return request.not_found()

        # messages = session.message_ids.sudo().search([], order='id asc')[:-20]  # Last 20 messages for performance
        messages = request.env['llm.chat.message'].sudo().search([('session_id', '=', session_id)], order='id desc',
                                                                 limit=20)  # Last 20 messages for performance
        llm_messages = [
            {'role': 'user' if m.author == 'user' else 'assistant', 'content': m.content}
            for m in messages
        ]

        # 👇 Попытка вставить system-инструкцию
        # instructions = {
        #     'ru': "Ты — помощник, который говорит только по-русски. Веди диалог на русском. Отвечай на русском языке.",
        #     'uk': "Ти помічник, який говорить тільки українською. Веди діалог українською. Відповідай українською мовою.",
        #     'en': "You are an assistant who speaks only English. Conduct a dialogue in English. Answer in English.",
        # }
        lang = session.lang if session.lang else 'uk'
        # lang = 'uk'  # Default language
        # user_msg = next((m['content'] for m in llm_messages if m['role'] == 'user'), None)
        # if user_msg:
        #     lang = detect(user_msg)

        # instruction = instructions.get(lang, instructions['uk'])
        llm_messages.insert(0, {'role': 'system', 'content': PromptBuilder.get_instruction(lang=lang)})

        try:
            bot_text = request.env['llm.embedding_service'].sudo().set_context(llm_messages)
        except Exception as e:
            _logger.exception("LLM error: " + str(e))
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
