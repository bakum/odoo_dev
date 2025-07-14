import json

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import faiss
import numpy as np
import os
from odoo import api, models, tools

FAISS_INDEX_PATH = tools.config.filestore('llm_index')  # папка внутри Odoo-файлов

# Убедимся, что директория существует
os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

INDEX_FILE = os.path.join(FAISS_INDEX_PATH, 'faiss.index')
ID_MAP_FILE = os.path.join(FAISS_INDEX_PATH, 'id_map.json')  # сохраняем маппинг id


class VectorIndex(models.AbstractModel):
    _name = "llm.vector.index"
    _description = "FAISS Vector Index Service"

    @api.model
    def build_index(self):
        """Построение индекса и сохранение в файл."""
        docs = self.env['llm.document'].search([('embedding', '!=', False)])
        vectors, ids = [], []

        for doc in docs:
            vec = self.env['llm.embedding_service'].deserialize(doc.embedding)
            if vec:
                vectors.append(vec)
                ids.append(doc.id)

        if not vectors:
            return []

        dim = len(vectors[0])
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(vectors, dtype='float32'))

        faiss.write_index(index, INDEX_FILE)
        with open(ID_MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(ids, f)
        return ids

    @api.model
    def load_index(self):
        """Загрузка индекса из файла."""
        if not os.path.exists(INDEX_FILE):
            raise FileNotFoundError("FAISS index file not found. Build the index first.")
        return faiss.read_index(INDEX_FILE)

    @api.model
    def load_id_map(self):
        """Загрузка списка id документов."""
        if not os.path.exists(ID_MAP_FILE):
            raise FileNotFoundError("ID map file not found. Please build the index.")
        with open(ID_MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    @api.model
    def search(self, query_vec, top_k=5):
        """Поиск по загруженному индексу."""
        index = self.load_index()
        id_map = self.load_id_map()

        xq = np.array([query_vec], dtype='float32')
        distances, indices = index.search(xq, top_k)

        # Преобразуем FAISS-индексы в document.id
        real_ids = [id_map[i] for i in indices[0] if i < len(id_map)]
        return real_ids, distances[0].tolist()
