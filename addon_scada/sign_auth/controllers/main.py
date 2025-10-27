from odoo import http
from odoo.http import request
from odoo.service import security
from odoo.osv import expression


class CustomLoginController(http.Controller):

    @http.route('/sign/login', type='json', auth='public', website=True)
    def custom_login(self, **kwargs):
        key_info = kwargs.get('keyInfo', None)
        if not key_info:
            return {
                'status': 'error',
                'message': 'No key info provided',
            }
        # Здесь логика проверки сертификата
        drfo = key_info.get('subjDRFOCode')
        edrpou = key_info.get('subjEDRPOUCode')
        email = key_info.get('subjEMail')
        name = key_info.get('subjFullName')
        phone = key_info.get('subjPhone')

        domain = []
        conditions = []

        if name:
            conditions.append(('name', 'ilike', name))
        if drfo:
            conditions.append(('partner_id.vat', '=', drfo))
        if edrpou:
            conditions.append(('partner_id.vat', '=', edrpou))
        if email:
            conditions.append(('partner_id.email', 'ilike', email))
        if phone:
            conditions.append(('partner_id.phone', 'ilike', phone))

        # Если есть несколько условий — обернём их в цепочку через '|'
        if len(conditions) == 1:
            domain = conditions
        elif len(conditions) > 1:
            # Для N условий нужно N-1 '|'
            domain = ['|'] * (len(conditions) - 1)
            for cond in conditions:
                domain.append(cond)

        user = request.env['res.users'].sudo().search(domain, limit=1)


        if user:
            partner = user.partner_id
            partner.sudo().write({
                'email': email if email else partner.email, 
                'phone': phone if phone else partner.phone, 
                'vat': drfo if drfo else edrpou if edrpou else partner.vat
                })
            # request.session.authenticate(request.db, user.login, user.password)
            request.session.uid = user.id
            request.session.login = user.login
            request.session.session_token = security.compute_session_token(request.session, request.env)
            return {
                'status': 'ok',
                'redirect': '/web',
                # 'user_id': user.id,
            }

        return {
            'status': 'error',
            'message': 'User not found',
            # 'redirect': '/web/login?error=cert',
        }

