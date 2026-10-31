from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestImportOrderRounding(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Distributor Partner'})
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Distributor Pricelist',
            'currency_id': cls.env.ref('base.EUR').id,
        })
        cls.pallet = cls.env['distrib.packages.sizes'].create({
            'width': 1200, 'height': 800, 'depth': 1800, 'type_of': 'pallet',
        })
        cls.distrib = cls.env['distrib.distributors'].create({
            'name': 'Test Distributor',
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'pallet_id': cls.pallet.id,
            'currency_id': cls.env.ref('base.EUR').id,
        })
        cls.box = cls.env['distrib.packages.sizes'].create({
            'width': 300, 'height': 200, 'depth': 100, 'type_of': 'box',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Model',
            'type': 'consu',
            'list_price': 10.0,
            'qty_in_cartoon': 4,
            'cartoon_id': cls.box.id,
        })
        group_user = cls.env.ref('ug_base_distrib.group_distrib_user')
        group_no_rounding = cls.env.ref('ug_wholesale_shop.group_distrib_import_no_rounding')
        cls.user_rounding = cls.env['res.users'].create({
            'name': 'Distributor User',
            'login': 'distrib_user_rounding',
            'distrib_id': cls.distrib.id,
            'groups_id': [Command.set([group_user.id])],
        })
        cls.user_no_rounding = cls.env['res.users'].create({
            'name': 'Distributor User Without Rounding',
            'login': 'distrib_user_no_rounding',
            'distrib_id': cls.distrib.id,
            'groups_id': [Command.set([group_no_rounding.id])],
        })

    def _import(self, user, qtt):
        wizard = self.env['ug.wholesale.import.order'].with_user(user).create({
            'xls_file': b'dGVzdA==',
            'products_ids': [Command.create({'product_id': self.product.id, 'qtt': qtt})],
        })
        return wizard

    def _save(self, wizard):
        wizard.save_order()
        return self.env['sale.order'].search([('partner_id', '=', self.partner.id)], order='id desc', limit=1)

    def test_import_rounds_to_boxes_without_group(self):
        wizard = self._import(self.user_rounding, 5)
        self.assertFalse(wizard.no_box_rounding)
        self.assertEqual(wizard.products_ids.qtt_by_box, 8)

        order = self._save(wizard)
        self.assertFalse(order.skip_box_rounding)
        self.assertEqual(order.order_line.product_uom_qty, 8)

    def test_import_keeps_quantity_with_group(self):
        wizard = self._import(self.user_no_rounding, 5)
        self.assertTrue(wizard.no_box_rounding)
        self.assertEqual(wizard.products_ids.qtt_by_box, 5)

        order = self._save(wizard)
        self.assertTrue(order.skip_box_rounding)
        self.assertEqual(order.order_line.product_uom_qty, 5)

        order.action_confirm()
        self.assertEqual(order.order_line.product_uom_qty, 5)
        # Неповна коробка рахується як ціла
        self.assertEqual(order.package_line.package_qty, 2)
        self.assertEqual(order.boxes_total, 2)

    def test_calculator_always_rounds(self):
        order = self._save(self._import(self.user_no_rounding, 5))
        order._recalc_by_package()
        self.assertEqual(order.order_line.product_uom_qty, 8)
