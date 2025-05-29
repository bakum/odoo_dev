from odoo.addons.account.controllers.portal import PortalAccount
from odoo.http import request


class PortalAccountWholesale(PortalAccount):

    def _get_invoices_domain(self):
        if request.env.user.has_group('ug_base_distrib.group_distrib_manager'):
            return [('state', 'not in', ('cancel', 'draft')), ('move_type', 'in',
                                                               ('out_invoice', 'out_refund', 'in_invoice', 'in_refund',
                                                                'out_receipt', 'in_receipt'))]
        distrib_id = request.env.user.distrib_id
        if not distrib_id:
            return []
        partner_id = distrib_id.partner_id
        if not partner_id:
            return []
        return ['&', ('state', 'not in', ('cancel', 'draft')),
                ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')),
                ('partner_id', '=', partner_id.id)]
