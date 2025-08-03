
from odoo.tests.common import TransactionCase
from odoo import fields


class TestDistributorsModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.EUR = self.env.ref('base.EUR')
        self.USD = self.env.ref('base.USD')
        self.partner = self.env['res.partner'].create({'name': 'Partner X'})
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test Pricelist',
            'currency_id': self.EUR.id
        })

    def test_create_distributor(self):
        distributor = self.env['distrib.distributors'].create({
            'name': 'Test Distributor',
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'currency_id': self.EUR.id,
        })
        self.assertTrue(distributor.ref)
        self.assertEqual(distributor.currency_id, self.EUR)

    def test_onchange_partner_fills_address_fields(self):
        new_partner = self.env['res.partner'].create({
            'name': 'Partner Y',
            'city': 'Lviv',
            'street': 'Main St',
            'street2': 'Apt 1',
            'mobile': '123456',
            'phone': '654321',
            'zip': '79000',
            'website': 'http://example.com',
            'country_id': self.env.ref('base.ua').id,
            'state_id': self.env['res.country.state'].create({
                'name': 'Lvivska',
                'code': 'LV',
                'country_id': self.env.ref('base.ua').id,
            }).id
        })

        distributor = self.env['distrib.distributors'].new({
            'partner_id': new_partner.id,
        })
        distributor._onchange_partner_id()

        self.assertEqual(distributor.city, 'Lviv')
        self.assertEqual(distributor.street, 'Main St')
        self.assertEqual(distributor.website, 'http://example.com')

    def test_compute_has_move(self):
        distributor = self.env['distrib.distributors'].create({
            'name': 'With Move',
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'currency_id': self.USD.id,
        })
        self.env['distrib.distributors.move'].create({
            'distrib_id': distributor.id,
            'operation': 'inc'
        })
        distributor._compute_has_move()
        self.assertTrue(distributor.has_move)

    def test_write_distributor(self):
        distributor = self.env['distrib.distributors'].create({
            'name': 'Writable Distributor',
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'currency_id': self.EUR.id,
        })
        distributor.write({'name': 'Updated Name'})
        self.assertEqual(distributor.name, 'Updated Name')

    def test_unlink_distributor(self):
        distributor = self.env['distrib.distributors'].create({
            'name': 'To Delete',
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'currency_id': self.EUR.id,
        })
        distributor_id = distributor.id
        distributor.unlink()
        self.assertFalse(self.env['distrib.distributors'].browse(distributor_id).exists())

    def test_copy_distributor(self):
        distributor = self.env['distrib.distributors'].create({
            'name': 'Original Distributor',
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'currency_id': self.EUR.id,
        })
        copy = distributor.copy()
        self.assertNotEqual(copy.id, distributor.id)
        self.assertEqual(copy.pricelist_id, distributor.pricelist_id)
