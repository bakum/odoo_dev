from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class _FakeFormat:
    def set_bg_color(self, _color):
        return self


class _FakeSheet:
    def __init__(self):
        self.cells = {}

    def set_column(self, *_args, **_kwargs):
        return None

    def write(self, row, col, value, _fmt=None):
        self.cells[(row, col)] = value


class _FakeWorkbook:
    def __init__(self):
        self.sheet = None

    def add_worksheet(self, _name):
        self.sheet = _FakeSheet()
        return self.sheet

    def add_format(self, _props=None):
        return _FakeFormat()


@tagged('post_install', '-at_install')
class TestDistribPricelistXls(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Без правил шаблону потрапляють усі товари
        cls.env['distrib.template.rules'].search([]).unlink()
        # Дистриб'ютор бачить лише товари свого регіону
        cls.region = cls.env['distrib.regions'].create({'name': 'Test Region', 'desc': 'Test Region'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Pricelist Model',
            'type': 'consu',
            'list_price': 10.0,
            'barcode': '4820184199991',
            'qty_in_cartoon': 6,
            'region_ids': [Command.set([cls.region.id])],
        })
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Distributor Pricelist',
            'currency_id': cls.env.ref('base.EUR').id,
            'item_ids': [Command.create({
                'applied_on': '1_product',
                'product_tmpl_id': cls.product.product_tmpl_id.id,
                'compute_price': 'fixed',
                'fixed_price': 7.25,
            })],
        })
        cls.distrib = cls.env['distrib.distributors'].create({
            'name': 'Test Distributor',
            'partner_id': cls.env['res.partner'].create({'name': 'Test Distributor Partner'}).id,
            'pricelist_id': cls.pricelist.id,
            'region_id': cls.region.id,
            'pallet_id': cls.env['distrib.packages.sizes'].create({
                'width': 1200, 'height': 800, 'depth': 1800, 'type_of': 'pallet',
            }).id,
            'currency_id': cls.env.ref('base.EUR').id,
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Distributor User',
            'login': 'distrib_user_pricelist',
            'distrib_id': cls.distrib.id,
            'groups_id': [Command.set([cls.env.ref('ug_base_distrib.group_distrib_user').id])],
        })

    def _generate(self, user):
        workbook = _FakeWorkbook()
        self.env['report.ug_wholesale_shop.export_distrib_pricelist_xls'].with_user(user).generate_xlsx_report(
            workbook, {}, self.env['product.template'].with_user(user),
        )
        return workbook.sheet.cells

    def test_pricelist_contains_distributor_prices(self):
        cells = self._generate(self.user)
        row = next(r for (r, c), value in cells.items() if c == 0 and value == self.product.barcode)
        self.assertEqual(cells[(row, 3)], 6)
        self.assertAlmostEqual(cells[(row, 4)], 7.25)
        self.assertEqual(cells[(row, 5)], 'EUR')
        self.assertEqual(cells[(0, 8)], self.pricelist.name)

    def test_user_without_distributor_gets_error(self):
        user = self.env['res.users'].create({
            'name': 'User Without Distributor',
            'login': 'user_without_distrib',
            'groups_id': [Command.set([self.env.ref('ug_base_distrib.group_distrib_user').id])],
        })
        with self.assertRaises(UserError):
            self._generate(user)
