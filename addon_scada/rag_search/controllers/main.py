import logging
import time

from odoo import http, _
from odoo.http import request, Response
from ..services.gibberish_filter import GibberishFilter
from ..services.index_service import RagIndexService
from ..services.summarizer_service import SummarizerService

_logger = logging.getLogger(__name__)


class RAGSearchController(http.Controller):

    def _get_llm_model(self):
        return request.env['ir.config_parameter'].sudo().get_param('rag_search.rag_llm_model_name', default='llama3')

    def _get_entrypoint(self):
        return request.env['ir.config_parameter'].sudo().get_param('rag_search.rag_ollama_entrypoint',
                                                                   default='http://localhost:11434')

    @http.route('/rag/search', type='json', auth='user', methods=['POST'])
    def search(self, query, top_k=5, threshold=0.7, summarized=True, **kwargs):
        if not query:
            return {'error': _('Empty query'), 'details': _('Please provide a search query.')}

        if GibberishFilter.is_gibberish(query):
            return {'error': 'Query seems to be gibberish', 'details': _('Please provide a valid search query.')}

        try:
            indexer = RagIndexService(request.env)
            results = indexer.search(query, top_k=top_k, threshold=threshold)

            # Формируем список чанков (моделей rag.chunk)
            chunk_ids = [r['id'] for r in results]
            chunks = request.env['rag.chunk'].sudo().browse(chunk_ids)

            # ✅ Генерация резюме через LLM
            summary = _("No relevant information.") if summarized or len(chunk_ids) == 0 else ""
            if chunks and summarized:
                summarizer = SummarizerService(ollama_url=self._get_entrypoint(), model=self._get_llm_model())
                summary = summarizer.summarize_chunks(chunks, query)

            return {
                'results': results,
                'summary': summary['text'] if isinstance(summary, dict) else summary,
                'tokens': summary['tokens'] if isinstance(summary, dict) else {'prompt': 0, 'completion': 0, 'total': 0}
            }
        except Exception as e:
            _logger.exception(_("Search error: %s"), e)
            return {'error': _('Search failed'), 'details': str(e)}

    @http.route('/rag/search/stream', type='http', auth='user')
    def stream_search(self, **kwargs):
        query = kwargs.get('text', '')
        try:
            indexer = RagIndexService(request.env)
            results = indexer.search(query, top_k=10, threshold=0.85)

            chunk_ids = [r['id'] for r in results]
            chunks = request.env['rag.chunk'].sudo().browse(chunk_ids)
            summarizer = SummarizerService(ollama_url=self._get_entrypoint(), model=self._get_llm_model())

            def generate():
                for chunk in summarizer.summarize_chunks(chunks, query, stream=True):
                    yield f"data: {chunk}\n\n"

            headers = [
                ('Content-Type', 'text/event-stream'),
                ('Cache-Control', 'no-cache'),
                ('X-Accel-Buffering', 'no'),  # Для Nginx
            ]
            return Response(generate(), headers=headers, status=200, direct_passthrough=True)
        except Exception as e:
            _logger.exception("Error in stream_chat(): %s", e)
            return Response(f"data: [Stream error: {e}]\n\n", status=500)

    @http.route('/rag/chat/stream', type='http', auth='user')
    def stream_chat(self, **kwargs):
        text = kwargs.get('text', '')

        def generate():
            try:
                fake_text = f"You said: {text}. Streaming response...\n"
                for char in fake_text:
                    yield char.encode("utf-8")
                    time.sleep(0.05)
                # yield b'\n'  # закрывающий chunk
            except Exception as e:
                _logger.exception("Error in stream generate(): %s", e)
                yield f"\n[error]: {str(e)}".encode("utf-8")

        return Response(
            generate(),
            status=200,
            headers=[
                ('Content-Type', 'text/event-stream'),
                ('Cache-Control', 'no-cache'),
                ('X-Accel-Buffering', 'no'),
            ],
            direct_passthrough=True
        )
