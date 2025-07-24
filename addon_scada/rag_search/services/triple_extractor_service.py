import re
import logging

import requests

_logger = logging.getLogger(__name__)


class TripleExtractorService:
    def __init__(self, ollama_url="http://localhost:11434", model="nous-hermes2"):
        self.ollama_url = ollama_url
        self.model = model

    def extract_triples(self, chunks):
        # chunks = self._split_text(text, max_words)
        all_triples = []
        for chunk in chunks:
            triples = self._extract_from_chunk(chunk.content)
            all_triples.extend(triples)
        return all_triples

    def _extract_from_chunk(self, text, stream=False):
        prompt = f"""
    Извлеки факты в виде триплетов из текста, представленного ниже, в формате: (сущность1, отношение, сущность2)
    Ничего не переводи, ничего не сочиняй.

    Текст:
    {text}
    """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream,
                    "temperature": 0.2
                },
                stream=stream,
                timeout=600,
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("response", "").strip()

            # content = response.choices[0].message['content']
            triples = self._parse_triples(content)
            return triples
        except Exception as e:
            _logger.exception("LLM triple extraction failed")
            return []

    def _parse_triples(self, content):
        # Простейший парсер вида: (A, B, C)
        return re.findall(r"\(([^,]+?),\s*([^,]+?),\s*([^)]+?)\)", content)
