from nltk.tokenize import sent_tokenize
import tiktoken


class ChunkingService:
    def __init__(self, model_name="cl100k_base", max_tokens=300, overlap=50, language="english"):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.language = language
        self.encoding = tiktoken.get_encoding(model_name)
        self._ensure_nltk_resources()

    def _ensure_nltk_resources(self):
        import nltk
        from nltk.data import find
        import os

        # Добавляем стандартные пути для Linux и Windows
        for path in [
            os.path.expanduser("~/nltk_data"),
            "/usr/share/nltk_data",
            "/usr/local/share/nltk_data",
            "/usr/lib/nltk_data",
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming", "nltk_data"),  # Windows fallback
        ]:
            if os.path.exists(path) and path not in nltk.data.path:
                nltk.data.path.append(path)

        try:
            find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

    def split_text(self, text):
        try:
            sentences = sent_tokenize(text, language=self.language)
        except Exception as e:
            import re
            print(f"Warning: fallback sentence split due to: {e}")
            sentences = re.split(r'(?<=[\.\!\?])\s+', text.strip())

        # Собираем позиции предложений в тексте
        spans = []
        cursor = 0
        for s in sentences:
            start = text.find(s, cursor)
            if start == -1:
                continue  # safety check
            end = start + len(s)
            spans.append((s, start, end))
            cursor = end

        return self._split_by_token_limit(spans)

    def _split_by_token_limit(self, spans):
        chunks = []
        i = 0
        n = len(spans)

        while i < n:
            current_chunk = []
            token_count = 0
            j = i

            while j < n:
                sentence, start, end = spans[j]
                sentence_tokens = len(self.encoding.encode(sentence))
                if token_count + sentence_tokens > self.max_tokens:
                    break
                current_chunk.append((sentence, start, end))
                token_count += sentence_tokens
                j += 1

            if not current_chunk:
                sentence, start, end = spans[i]
                current_chunk.append((sentence, start, end))
                j = i + 1

            chunk_text = " ".join(s[0] for s in current_chunk)
            chunk_start = current_chunk[0][1]
            chunk_end = current_chunk[-1][2]
            chunks.append({
                'text': chunk_text,
                'start': chunk_start,
                'end': chunk_end,
            })

            # Overlap обработка
            if self.overlap > 0:
                overlap_tokens = 0
                back_idx = j - 1
                while back_idx > i and overlap_tokens < self.overlap:
                    overlap_tokens += len(self.encoding.encode(spans[back_idx][0]))
                    back_idx -= 1
                i = back_idx + 1
            else:
                i = j

        return chunks



