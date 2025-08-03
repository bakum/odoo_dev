from odoo.tests.common import TransactionCase
from odoo import fields


class TestDistributorCurrency(TransactionCase):

    def setUp(self):
        super().setUp()
        self.EUR = self.env.ref('base.EUR')
        self.USD = self.env.ref('base.USD')
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100,
            'standard_price': 50,
        })
        self.uom = self.env.ref('uom.product_uom_unit')

        self.pricelist_eur = self.env['product.pricelist'].create({
            'name': 'EUR Pricelist',
            'currency_id': self.EUR.id,
            'item_ids': [(0, 0, {
                'applied_on': '3_global',
                'compute_price': 'fixed',
                'fixed_price': 120,
            })]
        })

        self.distributor = self.env['distrib.distributors'].create({
            'name': 'DistTest',
            'partner_id': self.env['res.partner'].create({'name': 'D'}).id,
            'pricelist_id': self.pricelist_eur.id,
            'currency_id': self.USD.id,
        })

        self.move = self.env['distrib.distributors.move'].create({
            'distrib_id': self.distributor.id,
            'operation': 'inc'
        })

    def test_currency_is_independent(self):
        self.assertNotEqual(
            self.distributor.pricelist_id.currency_id,
            self.distributor.currency_id,
            "Валюта дистрибутора должна отличаться от валюты прайслиста"
        )

    def test_line_currency_set_from_distributor(self):
        line = self.env['distrib.distributors.move.line'].create({
            'move_id': self.move.id,
            'product_id': self.product.id,
            'product_uom': self.uom.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(
            line.currency_id.id,
            self.distributor.currency_id.id,
            "currency_id строки должна быть валютой дистрибутора"
        )

    def test_price_unit_in_distributor_currency(self):
        line = self.env['distrib.distributors.move.line'].create({
            'move_id': self.move.id,
            'product_id': self.product.id,
            'product_uom': self.uom.id,
            'product_uom_qty': 1,
        })
        self.assertTrue(line.price_unit > 0, "price_unit должен быть установлен")

    def test_price_converted_correctly_by_currency(self):
        """Проверка, что цена пересчитана из EUR в USD через базовую валюту (UAH)"""

        # Примерные курсы: 1 EUR = 40 UAH, 1 USD = 33.33 UAH → 1 EUR = 1.2 USD
        self.env['res.currency.rate'].search([
            ('currency_id', '=', self.EUR.id),
            ('name', '=', fields.Date.today()),
            ('company_id', '=', self.env.company.id),
        ], limit=1).write({'rate': 1 / 40})

        self.env['res.currency.rate'].search([
            ('currency_id', '=', self.USD.id),
            ('name', '=', fields.Date.today()),
            ('company_id', '=', self.env.company.id),
        ], limit=1).write({'rate': 1 / 33.33})

        line = self.env['distrib.distributors.move.line'].create({
            'move_id': self.move.id,
            'product_id': self.product.id,
            'product_uom': self.uom.id,
            'product_uom_qty': 1,
        })

        expected_price = 120 * 40 / 33.33  # 120 EUR * EUR→UAH / USD→UAH ≈ 144
        actual_price = line.price_unit

        self.assertAlmostEqual(
            actual_price, expected_price, delta=0.01,
            msg=f"Ожидаемая цена {expected_price}, но получено {actual_price}"
        )

    def test_same_currency_no_conversion(self):
        """Если валюты совпадают, цена не должна конвертироваться."""

        # Установим валюту дистрибутора = валюте прайслиста (EUR)
        self.distributor.write({
            'currency_id': self.EUR.id,
        })

        # Создаём строку перемещения
        line = self.env['distrib.distributors.move.line'].create({
            'move_id': self.move.id,
            'product_id': self.product.id,
            'product_uom': self.uom.id,
            'product_uom_qty': 1,
        })

        # Ожидаемая цена — без пересчёта
        expected_price = 120
        actual_price = line.price_unit

        self.assertAlmostEqual(
            actual_price, expected_price, delta=0.01,
            msg=f"Ожидалось {expected_price} EUR, получено {actual_price}"
        )

    def test_line_currency_matches_distributor_when_same(self):
        """Если валюты совпадают, currency_id строки всё равно должен быть валюта дистрибутора"""

        self.distributor.write({
            'currency_id': self.EUR.id,
        })

        line = self.env['distrib.distributors.move.line'].create({
            'move_id': self.move.id,
            'product_id': self.product.id,
            'product_uom': self.uom.id,
            'product_uom_qty': 1,
        })

        self.assertEqual(
            line.currency_id.id,
            self.distributor.currency_id.id,
            "currency_id строки должна быть валютой дистрибутора (EUR)"
        )
