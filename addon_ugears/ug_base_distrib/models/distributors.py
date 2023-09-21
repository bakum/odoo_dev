from odoo import models, fields, api, _


class Distributors(models.Model):
    _name = 'distrib.distributors'
    _description = 'Distributors records'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    ref = fields.Char(string="Number", default=lambda self: _("New"))
    name = fields.Char(string='Name', required=True, tracking=True)
    company_name = fields.Char(string='Company name', translate=True, tracking=True)
    city = fields.Char(string='City', tracking=True)
    street = fields.Char(string='Street', tracking=True)
    street2 = fields.Char(string='Street2', tracking=True)
    mobile = fields.Char(string='Mobile', tracking=True)
    email = fields.Char(string='EMail', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    zip = fields.Char(string='Zip', tracking=True)
    website = fields.Char(string='website', tracking=True)
    country_id = fields.Many2one('res.country', "Country", tracking=True)
    state_id = fields.Many2one('res.country.state', "State", tracking=True)
    partner_id = fields.Many2one('res.partner', 'Partner', tracking=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', tracking=True, required=True)
    currency_id = fields.Many2one('res.currency', compute="_compute_currency")

    @api.depends('pricelist_id')
    def _compute_currency(self):
        for rec in self:
            rec.currency_id = self.pricelist_id.currency_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['ref'] = self.env['ir.sequence'].next_by_code('distrib.distributors')
        return super(Distributors, self).create(vals_list)

    @api.model
    def get_import_templates(self):
        """returns the xlsx import template file"""
        return [{
            'label': _('Import Template for Distributors'),
            'template': '/ug_base_distrib/static/xls/distributors_template.xlsx'
        }]

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for line in self:
            line.city = line.partner_id.city
            line.street = line.partner_id.street
            line.street2 = line.partner_id.street2
            line.mobile = line.partner_id.mobile
            line.phone = line.partner_id.phone
            line.zip = line.partner_id.zip
            line.website = line.partner_id.website
            line.country_id = line.partner_id.country_id
            line.state_id = line.partner_id.state_id
