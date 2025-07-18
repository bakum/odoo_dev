import requests
import logging
import tiktoken

_logger = logging.getLogger(__name__)

class SummarizerService:
    def __init__(self, ollama_url="http://localhost:11434", model="nous-hermes2"):
        self.ollama_url = ollama_url
        self.model = model
        self.encoding = tiktoken.get_encoding("cl100k_base")  # или подбери подходящий

    def summarize_chunks(self, chunks, user_query):
        if not chunks:
            return "Ничего не найдено для резюме."

        # Объединяем контент чанков
        context = "\n\n".join(f"- {c.content.strip()}" for c in chunks if c.content)
        prompt = (
            f"На основе следующих фрагментов сделай выводы кратко и по существу\n\n"
            f"Все названия, термины и определения указывай из фрагментов. Ничего не сочиняй:\n\n"
            f"Вопрос: {user_query}\n\n"
            f"Фрагменты:\n{context}\n\n"
            f"Ответ:"
        )

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=600,
            )
            response.raise_for_status()
            data = response.json()

            output = data.get("response", "").strip()
            prompt_tokens = len(self.encoding.encode(prompt))
            output_tokens = len(self.encoding.encode(output))
            total_tokens = prompt_tokens + output_tokens

            return {
                "text": output,
                "tokens": {
                    "prompt": prompt_tokens,
                    "completion": output_tokens,
                    "total": total_tokens,
                }
            }
        except Exception as e:
            _logger.exception("Ошибка при генерации резюме: %s", e)
            return {
                "text": f"[Ошибка генерации ответа: {e}]",
                "tokens": {"prompt": 0, "completion": 0, "total": 0}
            }
