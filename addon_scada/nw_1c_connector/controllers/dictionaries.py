import json

from odoo import http
from odoo.tools import date_utils
from .utils import parse_data_from_request, apply_update_from_request


class DictionariesController(http.Controller):
    @http.route(['/api/v2/test', ],
                auth='none', website=False, cors="*", csrf=False,
                methods=['GET'])
    def test(self):
        return json.dumps({"success": True})

    @http.route(['/api/v2/<string:modelname>'],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['GET', 'PUT', 'POST', 'DELETE'])
    def index(self, **kw):
        model_name = kw['modelname']
        del kw['modelname']
        data_for_edit, sk = parse_data_from_request(kw)
        result_dict = apply_update_from_request(sk, data_for_edit, model_name)
        # result = http.request.env[model_name].sudo().search_read(sk)

        if type(result_dict) is dict:
            return json.dumps(result_dict)

        return json.dumps(result_dict, default=date_utils.json_default)
