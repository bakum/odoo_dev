import json

from odoo import http
from odoo.tools import date_utils
from .utils import parse_data_from_request, apply_update_from_request, get_trans_from_request


class DictionariesController(http.Controller):
    @http.route(['/api/v2/test', ],
                auth='none', website=False, cors="*", csrf=False,
                methods=['GET'])
    def test(self):
        return json.dumps({"success": True})

    @http.route(['/api/v2/<string:modelname>',
                 '/api/v2/<string:modelname>/<string:guid>',
                 ],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['GET', 'PUT', 'POST', 'DELETE'])
    def index(self, guid=None, **kw):
        model_name = kw['modelname']
        del kw['modelname']
        data_for_edit, sk = parse_data_from_request(kw)
        data_for_translate = get_trans_from_request(data_for_edit)
        result_dict = apply_update_from_request(sk, data_for_edit, model_name, guid, data_for_translate)
        # result = http.request.env[model_name].sudo().search_read(sk)

        if type(result_dict) is dict:
            return json.dumps(result_dict, default=date_utils.json_default)

        return json.dumps(result_dict, default=date_utils.json_default)
