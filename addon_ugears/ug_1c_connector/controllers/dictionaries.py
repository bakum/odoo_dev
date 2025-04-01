import json

from odoo import http
from odoo.tools import date_utils
from .orm.utils import parse_data_from_request, get_trans_from_request, apply_update_from_request, get_ids_from_request, \
    apply_pricelist_from_request, apply_distrib_from_request, apply_moves_from_request, apply_expenses_from_request


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
        ids = get_ids_from_request(data_for_edit)
        result_dict = apply_update_from_request(sk, data_for_edit, model_name, guid, data_for_translate, ids)
        # result = http.request.env[model_name].sudo().search_read(sk)

        if type(result_dict) is dict:
            return json.dumps(result_dict, default=date_utils.json_default)

        return json.dumps(result_dict, default=date_utils.json_default)

    @http.route(['/api/v2/pricelist/<string:guid>'],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['POST'])
    def put_pricelist(self, guid=None, **kw):
        data_for_edit, sk = parse_data_from_request(kw)
        result_dict = apply_pricelist_from_request(data_for_edit, guid)

        if type(result_dict) is dict:
            return json.dumps(result_dict, default=date_utils.json_default)

        return json.dumps(result_dict, default=date_utils.json_default)

    @http.route(['/api/v2/archive/<string:guid>/create_distrib',
                 '/api/v2/archive/<string:guid>/create_distrib/<string:pricelist_guid>'],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['POST'])
    def create_distrib(self, guid, pricelist_guid=None, **kw):
        data_for_edit, sk = parse_data_from_request(kw)
        result_dict = apply_distrib_from_request(data_for_edit, guid, pricelist_guid)

        if type(result_dict) is dict:
            return json.dumps(result_dict, default=date_utils.json_default)

        return json.dumps(result_dict, default=date_utils.json_default)

    @http.route(['/api/v2/moves/<string:partner_guid>/create_moves'],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['POST'])
    def create_moves(self, partner_guid, **kw):
        data_for_edit, sk = parse_data_from_request(kw)
        result_dict = apply_moves_from_request(data_for_edit, partner_guid)

        if type(result_dict) is dict:
            return json.dumps(result_dict, default=date_utils.json_default)

        return json.dumps(result_dict, default=date_utils.json_default)

    @http.route(['/api/v2/expenses/<string:partner_guid>/create_expense'],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['POST'])
    def create_expenses(self, partner_guid, **kw):
        data_for_edit, sk = parse_data_from_request(kw)
        result_dict = apply_expenses_from_request(data_for_edit, partner_guid)

        if type(result_dict) is dict:
            return json.dumps(result_dict, default=date_utils.json_default)

        return json.dumps(result_dict, default=date_utils.json_default)
