import logging

from odoo import models, SUPERUSER_ID, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    palette_id = fields.Many2one(
        'distrib.packages.sizes',
        compute='_compute_palette_id',
        string='Default Palette')

    def sale_get_order(self, force_create=False, update_pricelist=False):
        """ Return the current sales order after mofications specified by params.

        :param bool force_create: Create sales order if not already existing
        :param bool update_pricelist: Force to recompute all the lines from sales order to adapt the price with the current pricelist.
        :returns: record for the current sales order (might be empty)
        :rtype: `sale.order` recordset
        """
        self.ensure_one()

        self = self.with_company(self.company_id)
        SaleOrder = self.env['sale.order'].sudo()

        sale_order_id = request.session.get('sale_order_id')

        if sale_order_id:
            sale_order_sudo = SaleOrder.browse(sale_order_id).exists()
        elif self.env.user and not self.env.user._is_public():
            sale_order_sudo = self.env.user.distrib_id.partner_id.last_website_so_id
            if sale_order_sudo:
                available_pricelists = self.get_pricelist_available()
                if sale_order_sudo.pricelist_id not in available_pricelists:
                    # Do not reload the cart of this user last visit
                    # if the cart uses a pricelist no longer available.
                    sale_order_sudo = SaleOrder
                else:
                    # Do not reload the cart of this user last visit
                    # if the Fiscal Position has changed.
                    fpos = sale_order_sudo.env['account.fiscal.position'].with_company(
                        sale_order_sudo.company_id
                    )._get_fiscal_position(
                        sale_order_sudo.partner_id,
                        delivery=sale_order_sudo.partner_shipping_id
                    )
                    if fpos.id != sale_order_sudo.fiscal_position_id.id:
                        sale_order_sudo = SaleOrder
        else:
            sale_order_sudo = SaleOrder

        # Ignore the current order if a payment has been initiated. We don't want to retrieve the
        # cart and allow the user to update it when the payment is about to confirm it.
        if sale_order_sudo and sale_order_sudo.get_portal_last_transaction().state in (
                'pending', 'authorized', 'done'
        ):
            sale_order_sudo = None

        if not (sale_order_sudo or force_create):
            # Do not create a SO record unless needed
            if request.session.get('sale_order_id'):
                request.session.pop('sale_order_id')
                request.session.pop('website_sale_cart_quantity', None)
            return self.env['sale.order']

        # Only set when neeeded
        pricelist_id = False

        partner_sudo = self.env.user.distrib_id.partner_id
        if len(partner_sudo) == 0:
            partner_sudo = self.env.user.partner_id

        # cart creation was requested
        if not sale_order_sudo:
            so_data = self._prepare_sale_order_values(partner_sudo)
            sale_order_sudo = SaleOrder.with_user(SUPERUSER_ID).create(so_data)

            request.session['sale_order_id'] = sale_order_sudo.id
            request.session['website_sale_cart_quantity'] = sale_order_sudo.cart_quantity
            # The order was created with SUPERUSER_ID, revert back to request user.
            sale_order_sudo = sale_order_sudo.with_user(self.env.user).sudo()
            return sale_order_sudo

        # Existing Cart:
        #   * For logged user
        #   * In session, for specified partner

        # case when user emptied the cart
        if not request.session.get('sale_order_id'):
            request.session['sale_order_id'] = sale_order_sudo.id
            request.session['website_sale_cart_quantity'] = sale_order_sudo.cart_quantity

        # check for change of partner_id ie after signup
        if sale_order_sudo.partner_id.id != partner_sudo.id and request.website.partner_id.id != partner_sudo.id:
            previous_fiscal_position = sale_order_sudo.fiscal_position_id
            previous_pricelist = sale_order_sudo.pricelist_id

            # Reset the session pricelist according to logged partner pl
            request.session.pop('website_sale_current_pl', None)
            pricelist_id = self._get_current_pricelist_id(partner_sudo)
            request.session['website_sale_current_pl'] = pricelist_id

            # change the partner, and trigger the computes (fpos)
            sale_order_sudo.write({
                'partner_id': partner_sudo.id,
                'partner_invoice_id': partner_sudo.id,
                'payment_term_id': self.sale_get_payment_term(partner_sudo),
                # Must be specified to ensure it is not recomputed when it shouldn't
                'pricelist_id': pricelist_id,
            })

            if sale_order_sudo.fiscal_position_id != previous_fiscal_position:
                sale_order_sudo.order_line._compute_tax_id()

            if sale_order_sudo.pricelist_id != previous_pricelist:
                update_pricelist = True
        elif update_pricelist:
            # Only compute pricelist if needed
            pricelist_id = self._get_current_pricelist_id(partner_sudo)

        # update the pricelist
        if update_pricelist:
            request.session['website_sale_current_pl'] = pricelist_id
            sale_order_sudo.write({'pricelist_id': pricelist_id})
            sale_order_sudo._recompute_prices()

        return sale_order_sudo

    def _prepare_sale_order_values(self, partner_sudo):
        self.ensure_one()
        addr = partner_sudo.address_get(['delivery'])
        if not request.website.is_public_user():
            last_sale_order = self.env['sale.order'].sudo().search(
                [('partner_id', '=', partner_sudo.id), ('website_id', '=', self.id)],
                limit=1,
                order="date_order desc, id desc",
            )
            if last_sale_order and last_sale_order.partner_shipping_id.active:  # first = me
                addr['delivery'] = last_sale_order.partner_shipping_id.id

        affiliate_id = request.session.get('affiliate_id')
        salesperson_user_sudo = self.env['res.users'].sudo().browse(affiliate_id).exists()
        if not salesperson_user_sudo:
            salesperson_user_sudo = self.salesperson_id or partner_sudo.parent_id.user_id or partner_sudo.user_id

        pricelist_id = self._get_current_pricelist_id(partner_sudo)
        fiscal_position_id = self._get_current_fiscal_position_id(partner_sudo)

        values = {
            'company_id': self.company_id.id,

            'fiscal_position_id': fiscal_position_id,
            'partner_id': partner_sudo.id,
            'partner_invoice_id': partner_sudo.id,
            'partner_shipping_id': addr['delivery'],

            'pricelist_id': pricelist_id,
            'payment_term_id': self.sale_get_payment_term(partner_sudo),

            'team_id': self.salesteam_id.id or partner_sudo.parent_id.team_id.id or partner_sudo.team_id.id,
            'user_id': salesperson_user_sudo.id,
            'website_id': self.id,
        }

        return values

    def get_palettes_available(self):
        self.ensure_one()
        domain = [('type_of', '=', 'pallet')]

        return self.env['distrib.packages.sizes'].search(domain)

    def get_current_palette(self):
        ProductPalette = self.env['distrib.packages.sizes']
        palette = ProductPalette

        if request and request.session.get('website_sale_current_palette'):
            palette = ProductPalette.browse(request.session['website_sale_current_palette']).exists().sudo()
            if not palette:
                request.session.pop('website_sale_current_palette')
                palette = ProductPalette

        if not palette:
            distrib_sudo = self.env.user.distrib_id
            palette = distrib_sudo.pallet_id

            available_palettes = self.get_palettes_available()
            if not palette:
                palette = available_palettes[0]

                if not palette:
                    _logger.error(
                        'Failed to find palette for distributor "%s" (id %s)',
                        distrib_sudo.name, distrib_sudo.id,
                    )

        return palette

    def get_current_pricelist(self):
        """
        :returns: The current pricelist record
        """
        self = self.with_company(self.company_id)
        ProductPricelist = self.env['product.pricelist']

        pricelist = ProductPricelist
        if request and request.session.get('website_sale_current_pl'):
            # `website_sale_current_pl` is set only if the user specifically chose it:
            #  - Either, he chose it from the pricelist selection
            #  - Either, he entered a coupon code
            pricelist = ProductPricelist.browse(request.session['website_sale_current_pl']).exists().sudo()
            country_code = self._get_geoip_country_code()
            if not pricelist or not pricelist._is_available_on_website(self) or not pricelist._is_available_in_country(
                    country_code):
                request.session.pop('website_sale_current_pl')
                pricelist = ProductPricelist

        if not pricelist:
            partner_sudo = self.env.user.partner_id
            distrib_sudo = self.env.user.distrib_id

            # If the user has a saved cart, it take the pricelist of this last unconfirmed cart
            # pricelist = partner_sudo.last_website_so_id.pricelist_id
            pricelist = distrib_sudo.pricelist_id
            if not pricelist:
                # The pricelist of the user set on its partner form.
                # If the user is not signed in, it's the public user pricelist
                pricelist = partner_sudo.property_product_pricelist

            # The list of available pricelists for this user.
            # If the user is signed in, and has a pricelist set different than the public user pricelist
            # then this pricelist will always be considered as available
            available_pricelists = self.get_pricelist_available()
            if available_pricelists and pricelist not in available_pricelists:
                # If there is at least one pricelist in the available pricelists
                # and the chosen pricelist is not within them
                # it then choose the first available pricelist.
                # This can only happen when the pricelist is the public user pricelist and this pricelist is not in the available pricelist for this localization
                # If the user is signed in, and has a special pricelist (different than the public user pricelist),
                # then this special pricelist is amongs these available pricelists, and therefore it won't fall in this case.
                pricelist = available_pricelists[0]

            if not pricelist:
                _logger.error(
                    'Failed to find pricelist for partner "%s" (id %s)',
                    partner_sudo.name, partner_sudo.id,
                )
        return pricelist

    def _compute_palette_id(self):
        for website in self:
            website.palette_id = website.get_current_palette()
