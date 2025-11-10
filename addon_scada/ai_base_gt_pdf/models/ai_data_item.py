from odoo import models, fields

class AiDataItem(models.Model):
    _inherit = 'ai.data.item'

    # Это поле связывает 'Страницу' (item) с ее 'Книгой' (pdf)
    pdf_file_id = fields.Many2one(
        'ai.data.source.pdf', 
        string="PDF File Source",
        # !!! ВОТ ОНО, ВАШЕ РЕШЕНИЕ !!!
        # Если ai.data.source.pdf удаляется, Odoo
        # автоматически удалит все связанные ai.data.item.
        ondelete='cascade', 
        index=True
    )
    
    # Мы также должны убедиться, что 'data_source_id' все еще заполняется.
    # Мы будем делать это вручную в 'action_run_items' для
    # сохранения совместимости с 'ai_base_gt'.