from werkzeug.urls import url_quote

class PromptBuilder:
    """
    Сервис для сборки системных инструкций, контекста из документов
    и финального промпта для LLM.
    """

    # Шаблоны инструкций по языкам
    INSTRUCTIONS = {
        'ru': "Ты помощник, который говорит только по-русски. Веди диалог на русском. Отвечай на русском языке.",
        'uk': "Ти помічник, який говорить тільки українською. Відповідай українською мовою.",
        'en': "You are an assistant who speaks only English. Answer in English.",
    }

    # Мэтчинг метки вопроса по языку
    QUESTION_LABELS = {
        'ru': 'Вопрос',
        'uk': 'Питання',
        'en': 'Question',
    }

    DIST_THRESHOLD = 1.5  # можно конфигурировать

    @classmethod
    def get_threshold(cls):
        """
        Возвращает пороговое значение дистанции для фильтрации документов.
        """
        return cls.DIST_THRESHOLD

    @classmethod
    def get_instruction(cls, lang):
        """
        Возвращает инструкцию для LLM в зависимости от языка.
        Если язык не поддерживается, возвращает украинскую инструкцию.
        """
        return cls.INSTRUCTIONS.get(lang, cls.INSTRUCTIONS['uk'])

    @classmethod
    def build_prompt(cls, text, lang, retrieved_docs, base_url):
        """
        Собирает единый текст промпта для LLM с учётом:
          - базовой инструкции (system)
          - контекста из документов (отфильтрованных по dist)
          - пользовательского вопроса
        retrieved_docs — список кортежей (doc_obj, dist)
        """
        # 1. Выбираем инструкцию и метку вопроса
        # instruction = cls.INSTRUCTIONS.get(lang, cls.INSTRUCTIONS['uk'])
        question_label = cls.QUESTION_LABELS.get(lang, cls.QUESTION_LABELS['uk'])

        # 2. Формируем контекст из документов
        context_parts = []
        links = []
        seen = set()
        # base_url = ""  # можно заменить на request.httprequest.host_url в контроллере

        for doc, dist in retrieved_docs:
            if dist > cls.DIST_THRESHOLD or not doc.id or doc.id in seen:
                continue
            seen.add(doc.id)

            snippet = doc.text[:500] + '...' if len(doc.text) > 500 else doc.text
            safe_name = url_quote(doc.document_id.name)
            download_url = f"{base_url}web/content/llm.document/{doc.document_id.id}/file/{safe_name}"

            context_parts.append(
                f"`{doc.document_id.name}` (dist={dist:.3f}):\n{snippet}\n"
                f"[`{doc.document_id.name}`](`{download_url}`)"
            )
            links.append({'name': doc.document_id.name, 'url': download_url})

        context = "\n\n".join(context_parts)

        # 3. Собираем финальный промпт
        prompt = (
            # f"{instruction}\n\n"
            "Не перекладай та не змінюй назви файлів.\n\n"
            "Завжди зберігай їх у точності як є, включаючи розширення (.pdf, .docx і т.д.), символи та регістр.\n\n"
            "Обгорни назви файлів у зворотні апострофи: ``назва_файлу.pdf``.\n\n"
            "Надай посилання на наведені документи, але не вигадуй їх. Не вставляй посилання, якщо не впевнений.\n\n"
            "Нижче надано релевантну інформацію з документів. Використовуй її при відповіді.\n\n"
            "Якщо вона не відповідає на запитання, скажи, що не знайшов інформації і не вигадуй.\n\n"
            f"{context}\n\n"
            f"{question_label}: {text}"
        )

        return prompt, links