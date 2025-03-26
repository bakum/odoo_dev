from odoo import models


class PartnersDistrib(models.Model):
    _inherit = "res.partner"

    def create_distributor(self, pricelist_id=None):
        for partner in self:
            existing_distributor = self.env['distrib.distributors'].search([('partner_id', '=', partner.id)], limit=1)
            distributor_vals = {
                'name': partner.name,
                'company_name': partner.company_name,
                'city': partner.city,
                'street': partner.street,
                'street2': partner.street2,
                'mobile': partner.mobile,
                'email': partner.email,
                'phone': partner.phone,
                'zip': partner.zip,
                'website': partner.website,
                'country_id': partner.country_id.id,
                'state_id': partner.state_id.id,
                'partner_id': partner.id,
                'pricelist_id': pricelist_id or self.env['product.pricelist'].search([], limit=1).id,
                # Use provided pricelist_id or default  # Assuming a default pricelist
                # Assuming a default pallet_id
            }
            if existing_distributor:
                existing_distributor.write(distributor_vals)
            else:
                distributor_vals.update({'pallet_id': self.env['distrib.packages.sizes'].search([('type_of', '=', 'pallet')], limit=1).id})
                self.env['distrib.distributors'].create(distributor_vals)
