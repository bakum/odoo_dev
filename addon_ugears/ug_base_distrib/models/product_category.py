from odoo import api, models, _, fields


class PublicProduct(models.Model):
    _inherit = "product.template"

    guid = fields.Char(string='Guid 1C:Enterprise')


class ProductCategoryImport(models.Model):
    _inherit = 'product.category'
    guid = fields.Char(string='Guid 1C:Enterprise')

    @api.model
    def get_import_templates(self):
        """returns the xlsx import template file"""
        return [{
            'label': _('Import Template for Product Categories'),
            'template': '/ug_base_distrib/static/xls/category_template.xlsx'
        }]
