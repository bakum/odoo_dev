from sentence_transformers import SentenceTransformer


class EmbedderService:
    model = SentenceTransformer("intfloat/multilingual-e5-small")