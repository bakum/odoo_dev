from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCommercialInvoiceReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Maxicraft BV',
            'street': 'Teststraat 1',
            'city': 'Amsterdam',
            'zip': '1011 AA',
            'country_id': cls.env.ref('base.nl').id,
        })
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'code': 'CIINC',
                'name': 'Commercial Invoice Income',
                'account_type': 'income',
                'company_id': cls.env.company.id,
            })
        cls.report = cls.env.ref(
            'ug_wholesale_shop.action_report_distrib_commercial_invoice'
        )

    def _create_product(self, default_code='70271', name='AT-ST Walker Model'):
        return self.env['product.product'].create({
            'name': name,
            'default_code': default_code or False,
            'type': 'consu',
            'list_price': 21.32,
            'qty_in_cartoon': 4,
            'invoice_policy': 'order',
        })

    def _create_invoice(self, product, **extra):
        vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2026-08-26',
            'date_facture': '2026-08-20',
            'number_facture': 'INV/2026/20413',
            'delivery_note_shipping_date': '2026-08-28',
            'delivery_note_order': 'HEO-ORDER-001',
            'invoice_line_ids': [
                Command.create({
                    'product_id': product.id,
                    'name': product.name,
                    'quantity': 8,
                    'price_unit': 21.32,
                    'account_id': self.income_account.id,
                }),
            ],
        }
        vals.update(extra)
        return self.env['account.move'].create(vals)

    def _render_html(self, invoice):
        html, _ctype = self.env['ir.actions.report']._render_qweb_html(
            'ug_wholesale_shop.action_report_distrib_commercial_invoice',
            invoice.ids,
        )
        if isinstance(html, bytes):
            return html.decode('utf-8')
        return html

    def test_commercial_invoice_html_contains_expected_content(self):
        product = self._create_product(default_code='70271')
        invoice = self._create_invoice(product)
        html = self._render_html(invoice)

        self.assertIn('Invoice', html)
        self.assertIn('INV/2026/20413', html)
        self.assertIn('The Supplier:', html)
        self.assertIn('The Buyer:', html)
        self.assertIn('VAT number:', html)
        self.assertIn("Bank's SWIFT", html)
        self.assertIn('Terms of Payment', html)
        self.assertIn('According to PO', html)
        self.assertIn('Order:', html)
        self.assertIn('HEO-ORDER-001', html)
        self.assertIn('Shipping Date:', html)
        self.assertIn('28/08/2026', html)
        self.assertNotIn('Dated:', html)
        self.assertNotIn('20/08/2026', html)
        self.assertIn('UGRS70271', html)
        self.assertIn('Price per 1 pcs', html)
        self.assertIn('excl. VAT', html)
        self.assertIn('heo GmbH', html)
        self.assertIn('DE03 5489 1300 0080 7822 09', html)
        self.assertIn('Gross weight of Shipment (kg):', html)
        self.assertIn('Net weight of Shipment (kg):', html)
        self.assertIn('Number of pallets:', html)

    def test_item_empty_without_default_code(self):
        product = self._create_product(default_code=False, name='Uncoded Model')
        invoice = self._create_invoice(product)
        html = self._render_html(invoice)
        self.assertNotIn('UGRS', html)

    def test_weights_from_linked_sale_order(self):
        product = self._create_product()
        cartoon = self.env.ref('ug_wholesale_shop.box_1')
        product.cartoon_id = cartoon.id
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': product.id,
                    'product_uom_qty': 8,
                    'price_unit': 21.32,
                }),
            ],
        })
        self.env['distrib.order.package.line'].create({
            'order_id': order.id,
            'cartoon_id': cartoon.id,
            'package_qty': 2,
            'weight_netto': 5000.0,
            'weight_brutto': 7000.0,
        })
        invoice = self._create_invoice(product)
        invoice.invoice_line_ids.sale_line_ids = order.order_line
        html = self._render_html(invoice)
        self.assertIn('7.0', html)
        self.assertIn('5.0', html)
