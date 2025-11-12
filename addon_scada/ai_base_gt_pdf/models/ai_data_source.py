from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from odoo.tools import split_every

_logger = logging.getLogger(__name__)

class AiDataSource(models.Model):
    _inherit = 'ai.data.source'

    # 1. Добавляем 'pdf' в поле 'type' (без изменений)
    type = fields.Selection(
        selection_add=[('pdf', 'PDF File')],
        ondelete={'pdf': 'set default'}
    )

    # 2. УДАЛЯЕМ старые поля
    # file_content_pdf = ... (УДАЛЕНО)
    # file_name_pdf = ... (УДАЛЕНО)

    # 3. ДОБАВЛЯЕМ поле One2many
    pdf_file_ids = fields.One2many(
        'ai.data.source.pdf',  # Наша новая модель
        'data_source_id',      # Поле Many2one в новой модели
        string="PDF Files"
    )

    def action_index(self):
        self._create_items()
        res = super().action_index()
        return res

    # def _prepare_data_for_index(self, batch_size=100):
    #     """
    #     Расширяем метод для поддержки 'new_type'.
    #     """
    #     self.ensure_one() # Вызов из оригинального метода все еще нужен
        
    #     # 1. Сначала проверяем наш новый тип
    #     if self.type == 'pdf':
    #         # Здесь ваша логика для 'new_type'
    #         # Предположим, у вас есть свои методы _get_new_data и _prepare_new_data
    #         for data_items_batch in split_every(batch_size, self.data_item_ids):
    #             data_items = self.env['ai.data.item'].concat(*data_items_batch)
    #             yield [self._prepare_text_data_for_index(data_item) for data_item in data_items]
        
    #     # 2. Если это не наш тип, передаем управление оригинальному методу
    #     else:
    #         # Используем yield from для "делегирования" генерации
    #         yield from super()._prepare_data_for_index(batch_size=batch_size)

    def _prepare_pdf_data(self, batch_size):
        for data_items_batch in split_every(batch_size, self.data_item_ids):
            data_items = self.env['ai.data.item'].concat(*data_items_batch)
            yield [self._prepare_text_data_for_index(data_item) for data_item in data_items]        


    def _create_items(self):
        """
        Расширяем индексацию: теперь мы итерируем по НЕСКОЛЬКИМ PDF-файлам.
        """
        res = True
        pdf_sources = self.filtered(lambda s: s.type == 'pdf')
        if not pdf_sources:
            return res

        DataItem = self.env['ai.data.item']
        
        for source in pdf_sources:

            items_to_unlink = source.pdf_file_ids.mapped('data_item_ids')
            # 1. Очищаем старые данные для этого источника
            if items_to_unlink:
                _logger.info(f"AI PDF: Unlinking {len(items_to_unlink)} old items...")
                items_to_unlink.unlink()

            items_to_create = []
            files_processed = 0
            
            # 2. Итерируем по всем загруженным PDF-файлам
            for pdf_file in source.pdf_file_ids:
                try:
                    # 3. Извлекаем страницы (список строк)
                    pages_content = pdf_file._extract_text_from_pdf()
                    if not pages_content:
                        continue

                    # 4. Готовим 'ai.data.item' для КАЖДОЙ страницы
                    for i, page_text in enumerate(pages_content):
                        item_name = f"{pdf_file.file_name_pdf} - Page {i + 1}"
                        items_to_create.append({
                            'data_source_id': source.id,
                            'pdf_file_id': pdf_file.id,
                            'source': item_name,
                            'data': page_text,
                        })
                    files_processed += 1
                
                except Exception as e:
                    _logger.error(f"AI PDF: Failed to index items after creation: {e}", exc_info=True)

            if items_to_create:
                # Сначала создаем все 'item'-ы в базе данных
                new_items = DataItem.create(items_to_create)
            elif files_processed == 0 and source.pdf_file_ids:
                _logger.error("No text could be extracted from the uploaded PDF files.", exc_info=True)
                #  source.message_post(body=_("No text could be extracted from the uploaded PDF files."))
        
        return res