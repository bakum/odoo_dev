import base64
import io
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:
    _logger.warning("PyMuPDF (fitz) library not found. Please install 'pip install PyMuPDF'.")
    fitz = None

class AiDataSourcePdf(models.Model):
    _name = 'ai.data.source.pdf'
    _description = 'AI Data Source PDF File'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    
    data_source_id = fields.Many2one(
        'ai.data.source', 
        string="Data Source",
        ondelete='cascade', 
        required=True
    )
    
    # Поля, которые мы ПЕРЕНЕСЛИ из ai.data.source
    file_content_pdf = fields.Binary(
        string="PDF File", 
        required=True
    )
    file_name_pdf = fields.Char(
        string="PDF Filename", 
        required=True
    )

    # ДОБАВЛЕНО: 'Книга' теперь "видит" свои 'Страницы'
    data_item_ids = fields.One2many(
        'ai.data.item',
        'pdf_file_id',
        string="Data Items"
    )

    def _extract_text_from_pdf(self):
        """
        Извлекает текст из ЭТОГО PDF-файла.
        Возвращает список строк (каждая строка - одна страница)
        """
        self.ensure_one()
        if not fitz:
            raise UserError(_("The 'PyMuPDF' (fitz) library is not installed. PDF processing is unavailable. Please run 'pip install PyMuPDF'."))
        
        if not self.file_content_pdf:
            return [] # Возвращаем пустой список

        doc = None
        try:
            decoded_file = base64.b64decode(self.file_content_pdf)
            doc = fitz.open(stream=decoded_file, filetype="pdf")
            
            text_parts = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text") or ""
                if text.strip(): # Добавляем только непустые страницы
                    text_parts.append(text)
            
            return text_parts # Возвращаем список страниц
        
        except Exception as e:
            _logger.error(f"Failed to extract text from PDF {self.file_name_pdf}: {e}", exc_info=True)
            raise UserError(_("Failed to process PDF file (%s). It might be corrupted. Error: %s", self.file_name_pdf, e))
        
        finally:
            if doc:
                doc.close()