import json

from odoo import http
from .orm.product_category import Category, Product, Pricelist, PricelistItem, Rates, Theme, SalesChannels
from .orm.utils import get_search_criterias, apply_update_from_request, parse_data_from_request, batch_update_from

ORM_DICT = {
    'product.category': Category,
    'product.product': Product,
    'product.template': Product,
    'product.pricelist': Pricelist,
    'product.pricelist.item': PricelistItem,
    'res.currency.rate': Rates,
    'distrib.product.theme': Theme,
    'distrib.sales.channels': SalesChannels,
}


class PublicCategoryController(http.Controller):
    @http.route(['/api/v2/test', ],
                auth='none', website=False, cors="*", csrf=False,
                methods=['GET'])
    def test(self):
        return json.dumps({"success": True})

    # @http.route(['/api/v2/category',
    #              '/api/v2/category/<string:guid>',
    #              ],
    #             auth='bearer_api_key', website=False, cors="*", csrf=False,
    #             methods=['GET', 'PUT', 'POST', 'DELETE'])
    # def index(self, guid=None, **kw):
    #     data, sk = parse_data_from_request(kw)
    #     # search_criterias = get_search_criterias(data['params'])
    #     result_dict = apply_update_from_request(sk, data, 'product.category', guid)
    #     if type(result_dict) is dict:
    #         return json.dumps(result_dict)
    #     result = []
    #     for move in result_dict:
    #         mod = Category.from_orm(move).dict()
    #         result.append(mod)
    #     return json.dumps(result)

    @http.route(['/api/v2/<string:modelname>',
                 '/api/v2/<string:modelname>/<string:guid>',
                 ],
                auth='bearer_api_key', website=False, cors="*", csrf=False,
                methods=['GET', 'PUT', 'POST', 'DELETE'])
    def index(self, guid=None, **kw):
        model_name = kw['modelname']
        del kw['modelname']
        data, sk = parse_data_from_request(kw)
        result_dict = apply_update_from_request(sk, data, model_name, guid)
        if type(result_dict) is dict:
            return json.dumps(result_dict)
        result = []
        for move in result_dict:
            try:
                function = ORM_DICT[model_name]
                mod = function.from_orm(move).dict()
            except KeyError:
                continue
            # if model_name == 'product.category':
            #     mod = Category.from_orm(move).dict()
            # elif model_name == 'product.product':
            #     mod = Product.from_orm(move).dict()
            # elif model_name == 'product.template':
            #     mod = Product.from_orm(move).dict()
            # elif model_name == 'product.pricelist':
            #     mod = Pricelist.from_orm(move).dict()
            # elif model_name == 'product.pricelist.item':
            #     mod = PricelistItem.from_orm(move).dict()
            # else:
            #     continue
            result.append(mod)
        return json.dumps(result)

    @http.route([
        '/api/v2/<string:modelname>/synchronization',
    ],
        auth='bearer_api_key', website=False, cors="*", csrf=False,
        methods=['POST'])
    def full_update(self, **kw):
        model_name = kw['modelname']
        del kw['modelname']
        data, sk = parse_data_from_request(kw)
        return json.dumps(batch_update_from(data, model_name))
