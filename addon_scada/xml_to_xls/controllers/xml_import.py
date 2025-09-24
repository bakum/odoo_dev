# xml_to_xls/controllers/xml_import.py
import base64
import json
from odoo import http
from odoo.http import request


class XmlImportController(http.Controller):

    @http.route('/xml_to_xls/upload_xml', type='json', auth='user', methods=['POST'])
    def upload_xml(self, **kwargs):
        """
        Принимает base64-строку XML-файла и имя файла.
        Создает запись xml.import и возвращает её id.
        """
        try:
            data = kwargs.get("data")
            filename = kwargs.get("filename", "import.xml")

            if not data:
                return {"error": "Missing base64 data"}

            # Проверка паддинга и декодирование
            data_str = data.decode() if isinstance(data, bytes) else data
            missing_padding = len(data_str) % 4
            if missing_padding:
                data_str += "=" * (4 - missing_padding)
            try:
                decoded = base64.b64decode(data_str)
            except Exception as e:
                return {"error": f"Base64 decode failed: {e}"}

            # Создаем запись
            record = request.env["xml.import"].sudo().create({
                "xml_file": base64.b64encode(decoded),  # сохранить корректно
                "xml_filename": filename,
            })
            if not record:
                return {"error": "Failed to create xml.import record"}

            record.action_fill_template()    

            return {
                "id": record.id,
                "name": record.display_name,
            }

        except Exception as e:
            return {"error": str(e)}
