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
class TestExportOrderToXls(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref('base.lv')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Buyer',
            'country_id': cls.env.ref('base.de').id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Model',
            'type': 'consu',
            'list_price': 10.0,
            'barcode': '4820184121931',
            'qty_in_cartoon': 4,
            'invoice_policy': 'order',
        })

    def test_country_of_origin_is_ukraine(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 4,
                    'price_unit': 10.0,
                }),
            ],
        })
        workbook = _FakeWorkbook()
        self.env['report.ug_base_distrib.export_order_to_xls'].generate_xlsx_report(
            workbook, {}, order,
        )
        origin_values = [
            value for (row, col), value in workbook.sheet.cells.items()
            if col == 2 and row > 9
        ]
        self.assertTrue(origin_values)
        self.assertIn('Ukraine', origin_values)
        self.assertNotIn('Latvia', origin_values)
        self.assertEqual(self.env.company.country_id.code, 'LV')
