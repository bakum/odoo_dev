from odoo import http
from odoo.http import request
from odoo.service import security


class CustomLoginController(http.Controller):

    @http.route('/sign/login', type='json', auth='public', website=True)
    def custom_login(self, **kwargs):
        key_info = kwargs.get('keyInfo')
        # Здесь логика проверки сертификата
        # user = request.env['res.users'].sudo().search([('cert_id', '=', cert_id)], limit=1)
        drfo = key_info.get('subjDRFOCode')
        name = key_info.get('subjFullName')

        user = request.env['res.users'].sudo().search([
            '|', ('name', 'ilike', name), ('partner_id.vat', '=', drfo)
        ], limit=1)

        # partner = request.env['res.partner'].sudo().search([
        #     ('vat', '=', drfo)
        # ], limit=1)
        # if not user:
        #     if partner:
        #         user = request.env['res.users'].sudo().search([
        #             ('partner_id', '=', partner.id)
        #         ], limit=1)


        if user:
            # request.session.authenticate(request.db, user.login, user.password)
            request.session.uid = user.id
            request.session.login = user.login
            request.session.session_token = security.compute_session_token(request.session, request.env)
            return {
                'status': 'ok',
                'redirect': '/web',
                'user_id': user.id,
            }

        return {
            'status': 'error',
            'message': 'User not found',
            'redirect': '/web/login?error=cert',
        }

