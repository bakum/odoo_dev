from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDeliveryNoteReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'heo GmbH',
            'street': 'West Campus 1',
            'city': 'Herxheim',
            'zip': '76863',
            'country_id': cls.env.ref('base.de').id,
        })
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'code': 'DNINC',
                'name': 'Delivery Note Income',
                'account_type': 'income',
                'company_id': cls.env.company.id,
            })
        cls.report = cls.env.ref(
            'ug_wholesale_shop.action_report_distrib_delivery_note'
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
            'delivery_note_shipping_date': '2026-08-28',
            'delivery_note_order': 'HEO-ORDER-001',
            'delivery_note_carrier': 'DHL Express',
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
            'ug_wholesale_shop.action_report_distrib_delivery_note',
            invoice.ids,
        )
        if isinstance(html, bytes):
            return html.decode('utf-8')
        return html

    def test_delivery_note_html_contains_expected_content(self):
        product = self._create_product(default_code='70271')
        invoice = self._create_invoice(product)
        html = self._render_html(invoice)

        self.assertIn('Delivery Note', html)
        self.assertIn('Dated:', html)
        self.assertIn('26/08/2026', html)
        self.assertIn('Shipping Date:', html)
        self.assertIn('28/08/2026', html)
        self.assertIn('Order:', html)
        self.assertIn('Carrier:', html)
        self.assertIn('HEO-ORDER-001', html)
        self.assertIn('DHL Express', html)
        self.assertIn('UGRS70271', html)
        self.assertIn('heo GmbH', html)
        self.assertIn('DE03 5489 1300 0080 7822 09', html)
        self.assertIn('Gross weight of Shipment (kg):', html)
        self.assertIn('Net weight of Shipment (kg):', html)
        self.assertIn('Number of pallets:', html)

        self.assertNotIn('Invoice No.', html)
        self.assertNotIn('According to PO', html)
        self.assertNotIn('Price per 1 pcs', html)
        self.assertNotIn('excl. VAT', html)
        self.assertNotIn('VAT number:', html)
        self.assertNotIn("Bank's SWIFT", html)
        self.assertNotIn('Terms of Payment', html)

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
