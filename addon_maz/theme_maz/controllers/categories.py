from odoo import http


class MazCategories(http.Controller):

    @http.route('/categories', auth="public", type="json", methods=['POST'])
    def all_published_categories(self):
        category = http.request.env['product.public.category'].search_read([('is_published', '=', True)])
        # cities = http.request.env['yh.cities'].search_read([], ['country_id', 'state_id', 'image'])
        return category
