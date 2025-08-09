import requests
import time
import tiktoken
import logging

_logger = logging.getLogger(__name__)

class SummarizerService:
    def __init__(self, ollama_url="http://localhost:11434", model="nous-hermes2"):
        self.ollama_url = ollama_url
        self.model = model
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def _safe_stream(self, response, max_seconds=60):
        start_time = time.time()
        for line in response.iter_lines(decode_unicode=True):
            if time.time() - start_time > max_seconds:
                _logger.warning("Stream timeout exceeded (%ss)", max_seconds)
                break
            if line:
                try:
                    data = line.strip().removeprefix("data: ").strip()
                    yield data
                except Exception as e:
                    _logger.warning("Stream chunk parse error: %s", e)

    def summarize_chunks(self, chunks, user_query, stream=False):
        if not chunks:
            return "Nothing found for resume."

        context = "\n\n".join(f"- {c.content.strip()}" for c in chunks if c.content)
        prompt = (
            f"На основе следующих фрагментов сделай выводы кратко и по существу.\n\n"
            f"Все названия, термины и определения указывай из фрагментов. Ничего не сочиняй:\n\n"
            f"Вопрос: {user_query}\n\n"
            f"Фрагменты:\n{context}\n\n"
            f"Ответ:"
        )

        try:
            timeout_seconds = (10, 1200)  # connect 10 сек, ответ до 20 минут
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream,
                    "temperature": 0.3
                },
                stream=stream,
                timeout=timeout_seconds
            )

            response.raise_for_status()

            if stream:
                return self._safe_stream(response)

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
        except requests.exceptions.Timeout:
            _logger.error("Summarizer request timed out")
            return {"text": "[Error: summarizer timed out]", "tokens": {"prompt": 0, "completion": 0, "total": 0}}
        except Exception as e:
            _logger.exception("Error in summarize_chunks: %s", e)
            return {"text": f"[Error in chat: {e}]", "tokens": {"prompt": 0, "completion": 0, "total": 0}}

    def chat(self, messages, stream=False):
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": stream,
                    "temperature": 0.5,
                },
                stream=stream,
                timeout=(5, 60),
            )

            response.raise_for_status()

            if stream:
                return self._safe_stream(response)

            data = response.json()
            content = data.get("message", {}).get("content", "").strip()
            prompt_tokens = len(self.encoding.encode(str(messages)))
            completion_tokens = len(self.encoding.encode(content))

            return {
                "text": content,
                "tokens": {
                    "prompt": prompt_tokens,
                    "completion": completion_tokens,
                    "total": prompt_tokens + completion_tokens,
                }
            }
        except requests.exceptions.Timeout:
            _logger.error("Chat request timed out")
            return {"text": "[Error: chat timed out]", "tokens": {"prompt": 0, "completion": 0, "total": 0}}
        except Exception as e:
            _logger.exception("Error in chat: %s", e)
            return {"text": f"[Error in chat: {e}]", "tokens": {"prompt": 0, "completion": 0, "total": 0}}
