from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestShopDefaultCategory(TransactionCase):

    def test_settings_store_default_category(self):
        category = self.env['product.public.category'].create({'name': 'Test Models'})
        settings = self.env['res.config.settings'].create({'shop_default_category_id': category.id})
        settings.execute()
        param = self.env['ir.config_parameter'].sudo().get_param('distrib.default_shop_category_id')
        self.assertEqual(param, str(category.id))
        self.assertEqual(self.env['res.config.settings'].create({}).shop_default_category_id, category)
