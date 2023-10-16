from datetime import datetime

from odoo import models, fields, api, _
import json
from urllib.request import urlopen

from odoo.exceptions import UserError


class ResCurrency(models.Model):
    _inherit = "res.currency"
    code = fields.Char(string='Code of currency', size=3)

    def create_notification(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success!'),
                'message': _('Currency code successfully loaded!'),
                'sticky': False,
            }
        }

    @api.model
    def _update_val_code(self):
        for vals in self.search([('name', '=', 'USD')]):
            vals.code = "840"
        for vals in self.search([('name', '=', 'EUR')]):
            vals.code = "978"
        for vals in self.search([('name', '=', 'UAH')]):
            vals.code = "980"

    def _cron_load_from_nbu(self):
        uah = self.env['res.currency'].sudo().search([('name', '=', 'UAH'), ('active', '=', True)])
        if len(uah) == 0:
            return
        operation_allow = self.env.company.currency_id.id == uah[0].id
        if not operation_allow:
            return
        currency = self.env['res.currency'].sudo().search([('name', '!=', 'UAH'), ('active', '=', True)])
        x = datetime.now()
        for rec in currency:
            URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={0}&date={1}{2}{3}&json'.format(
                rec.name, x.strftime("%Y"), x.strftime("%m"), x.strftime("%d"))
            try:
                res = json.load(urlopen(URL))
            except:
                raise UserError(_('Could not connect to %s' % URL))

            for line in res:
                # rec.code = line.get('r030', '')
                rates = self.env['res.currency.rate'].sudo().search([
                    ('company_id', '=', self.env.company.id),
                    ('currency_id', '=', rec.id),
                    ('name', '=', x.date())
                ])

                if len(rates) > 0:
                    rates[0].write({'rate': (1.0 / line.get('rate', 1))})
                else:
                    rec.rate_ids = [(0, 0, {
                        'rate': (1.0 / line.get('rate', 1)),
                        'company_id': self.env.company.id
                    })]

    def load_from_nbu(self):
        # self._cron_load_from_nbu()
        uah = self.env['res.currency'].sudo().search([('name', '=', 'UAH'), ('active', '=', True)])
        if len(uah) == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('Warning!'),
                    'message': _('UAH currency is not used in accounting!'),
                    'sticky': False,
                }
            }

        operation_allow = self.env.company.currency_id.id == uah[0].id
        if not operation_allow:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('Warning!'),
                    'message': _('UAH is not the currency of the current organization!'),
                    'sticky': False,
                }
            }
        for rec in self:
            if rec.name == 'UAH':
                rec.code = '980'
                continue
            x = datetime.now()
            URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={0}&date={1}{2}{3}&json'.format(
                rec.name, x.strftime("%Y"), x.strftime("%m"), x.strftime("%d"))
            try:
                res = json.load(urlopen(URL))
            except:
                raise UserError(_('Could not connect to %s' % URL))

            for line in res:
                rec.code = line.get('r030', '')
                rates = self.env['res.currency.rate'].sudo().search([
                    ('company_id', '=', self.env.company.id),
                    ('currency_id', '=', rec.id),
                    ('name', '=', x.date())
                ])

                if len(rates) > 0:
                    rates[0].write({'rate': (1.0 / line.get('rate', 1))})
                else:
                    rec.rate_ids = [(0, 0, {
                        'rate': (1.0 / line.get('rate', 1)),
                        'company_id': self.env.company.id
                    })]
                # rec.write({
                #     'rate_ids': [(0, 0, {
                #         'rate': line.get('rate', 1)
                #     })]
                # })

        if len(self) == 1:
            return self.create_notification()
