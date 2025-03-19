from odoo import api, models, _, fields


class PartnersDistrib(models.Model):
    _inherit = "res.partner"

    guid = fields.Char(string='Guid 1C:Enterprise')
    distrib_ids = fields.One2many('distrib.distributors', 'partner_id', string='Distributor')

    # @api.onchange('city', 'street', 'street2', 'mobile',
    #              'phone', 'zip', 'website', 'country_id',
    #              'state_id')
    # def _address_set(self):
    #     for line in self:
    #         if line.distrib_ids:
    #             line.distrib_ids.write({
    #                 'city' : line.city,
    #                 'street': line.street,
    #                 'street2': line.street2,
    #                 'mobile': line.mobile,
    #                 'phone': line.phone,
    #                 'zip': line.zip,
    #                 'website': line.website,
    #                 'country_id': line.country_id.id,
    #                 'state_id': line.state_id.id,
    #             })