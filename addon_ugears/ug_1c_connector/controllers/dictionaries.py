import json

from .orm.product_category import Category
from .orm.utils import get_search_criterias, apply_update_from_request
from odoo import http
import json


class PublicCategoryController(http.Controller):
    @http.route(['/api/v2/test', ],
                auth='none', website=False, cors="*", csrf=False,
                methods=['GET'])
    def test(self):
        return json.dumps({"success": True})
        #return json.loads(result)

    @http.route(['/api/v2/category',
                 '/api/v2/category/<string:guid>',
                 ],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['GET', 'PUT', 'POST', 'DELETE'])
    def index(self, guid=None, **kw):
        search_criterias = get_search_criterias(kw)
        result_dict = apply_update_from_request(kw, http.request, search_criterias, 'product.category', guid)
        if type(result_dict) is dict:
            return json.dumps(result_dict)
        result = []
        for move in result_dict:
            mod = Category.from_orm(move).dict()
            result.append(mod)
        return json.dumps(result)
