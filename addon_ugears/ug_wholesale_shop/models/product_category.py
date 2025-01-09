from odoo import models, fields, tools, api, _
from odoo.addons.http_routing.models.ir_http import slug, unslug


class Product(models.Model):
    _inherit = "product.template"

    weight = fields.Float('Weight model, gram', digits=(16, 1))
    qty_in_cartoon = fields.Integer('Quantity in cartoon', default=0)
    cartoon_id = fields.Many2one('distrib.packages.sizes', 'Cartoon')
    cartoon_weight_with_model = fields.Float('Cartoon weight with model, gram', store=True,
                                             compute='_compute_cartoon_weight_with_model')
    customscode = fields.Char('Customs tariff number', default='95030039')

    @api.depends('cartoon_id.cartoon_weight', 'weight', 'qty_in_cartoon')
    def _compute_cartoon_weight_with_model(self):
        for line in self:
            cartoon_weight_with_model = line.weight * line.qty_in_cartoon + line.cartoon_id.cartoon_weight
            cartoon_weight_with_model = tools.float_round(cartoon_weight_with_model, 1)
            line.cartoon_weight_with_model = cartoon_weight_with_model

    @api.model
    def _search_get_detail(self, website, order, options):
        # is_admin = self.env.user.has_group("base.group_system") or self.env.user.has_group("ug_base_distrib.group_distrib_manager")
        is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")
        with_image = options['displayImage']
        with_description = options['displayDescription']
        with_category = options['displayExtraLink']
        with_price = options['displayDetail']
        domains = [website.sale_product_domain()]
        category = options.get('category')
        min_price = options.get('min_price')
        max_price = options.get('max_price')
        attrib_values = options.get('attrib_values')
        if not is_manager:
            domains.append([('is_published', '=', True)])
            domains.append([('weight', '>', 0)])
            domains.append([('qty_in_cartoon', '>', 0)])
            domains.append([('cartoon_id', '<>', False)])
        if category:
            domains.append([('public_categ_ids', 'child_of', unslug(category)[1])])
        if min_price:
            domains.append([('list_price', '>=', min_price)])
        if max_price:
            domains.append([('list_price', '<=', max_price)])
        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domains.append([('attribute_line_ids.value_ids', 'in', ids)])
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domains.append([('attribute_line_ids.value_ids', 'in', ids)])
        search_fields = ['name', 'default_code', 'product_variant_ids.default_code', 'barcode']
        fetch_fields = ['id', 'name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'default_code': {'name': 'default_code', 'type': 'text', 'match': True},
            'product_variant_ids.default_code': {'name': 'product_variant_ids.default_code', 'type': 'text',
                                                 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }
        if with_image:
            mapping['image_url'] = {'name': 'image_url', 'type': 'html'}
        if with_description:
            # Internal note is not part of the rendering.
            search_fields.append('description')
            fetch_fields.append('description')
            search_fields.append('description_sale')
            fetch_fields.append('description_sale')
            mapping['description'] = {'name': 'description_sale', 'type': 'text', 'match': True}
        if with_price:
            mapping['detail'] = {'name': 'price', 'type': 'html', 'display_currency': options['display_currency']}
            mapping['detail_strike'] = {'name': 'list_price', 'type': 'html',
                                        'display_currency': options['display_currency']}
        if with_category:
            mapping['extra_link'] = {'name': 'category', 'type': 'html'}
        return {
            'model': 'product.template',
            'base_domain': domains,
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-shopping-cart',
        }

    @api.model
    def _get_package_detail(self):
        return _('Netto weight ') + str(self.weight) + _(' gram')

    @api.model
    def _get_package_detail_with_cartoon(self):
        return _('Brutto weight ') + str(self.cartoon_weight_with_model) + _(' gram')

class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'
    guid = fields.Char(string='Guid 1C:Enterprise')
