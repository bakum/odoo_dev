import json

import warnings

from langdetect import detect

warnings.filterwarnings("ignore", category=DeprecationWarning)

import faiss
import numpy as np
import os
from odoo import api, models, tools
from sentence_splitter import SentenceSplitter, SentenceSplitterException

FAISS_INDEX_PATH = tools.config.filestore('llm_index')  # папка внутри Odoo-файлов

# Убедимся, что директория существует
os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

INDEX_FILE = os.path.join(FAISS_INDEX_PATH, 'faiss.index')
ID_MAP_FILE = os.path.join(FAISS_INDEX_PATH, 'id_map.json')  # сохраняем маппинг id
CHUNK_SIZE = 1000  # размер чанка в словах
OVERLAP = 150

# def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
#     words = text.split()
#     chunks = []
#     for i in range(0, len(words), chunk_size - overlap):
#         chunk = words[i:i + chunk_size]
#         chunks.append(" ".join(chunk))
#     return chunks


def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    try:
        lang = detect(text)
    except:
        lang = 'en'  # fallback

    lang = lang if lang in {'en', 'ru', 'uk', 'de', 'fr', 'es'} else 'en'

    try:
        splitter = SentenceSplitter(language=lang)
    except SentenceSplitterException:
        splitter = SentenceSplitter(language='ru')

    # splitter = SentenceSplitter(language='multilingual')  # Используем многоязычный сплиттер
    sentences = splitter.split(text)
    chunks = []
    chunk = ""
    for sentence in sentences:
        if len(chunk) + len(sentence) <= chunk_size:
            chunk += sentence + " "
        else:
            chunks.append(chunk.strip())
            chunk = sentence + " "
    if chunk:
        chunks.append(chunk.strip())

    # Добавим overlap
    final_chunks = []
    for i in range(0, len(chunks)):
        prev = final_chunks[-1][-overlap:] if i > 0 else ""
        final_chunks.append((prev + chunks[i])[-chunk_size:])
    return final_chunks


class VectorChunkIndex(models.AbstractModel):
    _name = "llm.vector.index"
    _description = "FAISS Vector Index Service (Chunk-based)"

    @api.model
    def build_index(self):
        chunk_model = self.env['llm.document.chunk']
        chunk_model.search([]).unlink()  # очистка

        docs = self.env['llm.document'].search([('text_content', '!=', False)])
        vectors, ids = [], []

        for doc in docs:
            chunks = split_into_chunks(doc.text_content)
            for chunk_text in chunks:
                vec = self.env['llm.embedding_service'].embed(chunk_text)
                vec_serialized = self.env['llm.embedding_service'].serialize(vec)
                chunk = chunk_model.create({
                    'document_id': doc.id,
                    'text': chunk_text,
                    'embedding': vec_serialized,
                })
                vectors.append(vec)
                ids.append(chunk.id)

        if not vectors:
            return []

        if not vectors:
            return []

        vectors = np.array(vectors, dtype='float32')  # <--- из списка в массив
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)  # <--- нормализация

        dim = vectors.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(vectors)

        faiss.write_index(index, INDEX_FILE)
        with open(ID_MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(ids, f)

        return ids

    @api.model
    def load_index(self):
        if not os.path.exists(INDEX_FILE):
            raise FileNotFoundError("FAISS index not found")
        return faiss.read_index(INDEX_FILE)

    @api.model
    def load_id_map(self):
        if not os.path.exists(ID_MAP_FILE):
            raise FileNotFoundError("ID map not found")
        with open(ID_MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    @api.model
    def search(self, query_vec, top_k=5):
        index = self.load_index()
        id_map = self.load_id_map()

        xq = np.array([query_vec], dtype='float32')
        xq = xq / np.linalg.norm(xq)
        distances, indices = index.search(xq.reshape(1, -1), top_k)

        chunk_ids = [id_map[i] for i in indices[0] if i < len(id_map)]
        chunks = self.env['llm.document.chunk'].browse(chunk_ids)
        return list(zip(chunks, distances[0].tolist()))
