import datetime
import json
from urllib.request import urlopen

from odoo import models, fields, _, api
from odoo.exceptions import UserError


class UgImportRatesFromNbu(models.TransientModel):
    _name = "ug.rates.from.nbu"
    _description = "Import currency rates from NBU"

    def _default_name(self):
        return _('Please load the list')

    def _default_currency(self):
        curr = []
        currency = self.env['res.currency'].sudo().search([('name', '!=', 'UAH'), ('active', '=', True)])
        for cr in currency:
            curr.append(
                (0, 0, {
                    'currency': cr.id
                })
            )
        return curr

    name = fields.Char('Name', default=_default_name)
    date_from = fields.Date('From', required=True, default=lambda self: fields.Datetime.now().date())
    date_to = fields.Date('To', required=True, default=lambda self: fields.Datetime.now().date())
    company = fields.Many2one('res.company', default=lambda self: self.env.company)
    rates_ids = fields.One2many('ug.rates.from.nbu.list', 'wizard_id')
    currency_ids = fields.One2many('ug.currency.from.nbu.list', 'wizard_id', default=_default_currency)

    len_rates = fields.Integer(compute='get_len_rates')
    len_currency = fields.Integer(compute='get_len_currency')

    def write(self, vals):
        result = super(UgImportRatesFromNbu, self).write(vals)
        for line in self.rates_ids:
            rates = self.env['res.currency.rate'].sudo().search([
                ('company_id', '=', line.company_id.id),
                ('currency_id', '=', line.currency.id),
                ('name', '=', line.name)
            ])
            if len(rates) > 0:
                rates[0].write({'inverse_company_rate': line.rate})
            else:
                re = self.env['res.currency.rate'].sudo().create({
                    'company_id': line.company_id.id,
                    'currency_id': line.currency.id,
                    'name': line.name,
                    'inverse_company_rate': line.rate,
                })
        return result

    @api.depends('rates_ids')
    def get_len_rates(self):
        self.len_rates = len(self.rates_ids)

    @api.depends('currency_ids')
    def get_len_currency(self):
        self.len_currency = len(self.currency_ids)

    def create_notification(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success!'),
                'message': _('Currency rates successfully loaded!'),
                'sticky': False,
            }
        }

    def _get_full_context(self):
        return {
            'name': _('Import currency rates from NBU'),
            'res_model': 'ug.rates.from.nbu',
            'view_mode': 'form',
            'res_id': self.id,
            'context': {
                'default_name': self.name,
                'default_company': self.company,
                'default_date_from': self.date_from,
                'default_date_to': self.date_to,
                'default_rates_ids': self.rates_ids,
                'default_currency_ids': self.currency_ids,
                'active_ids': self._context.get('active_ids'),
                'update_page': True,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def load_rates_from_nbu(self):
        self.rates_ids.unlink()
        date_cur = self.date_from
        rates = []
        while date_cur <= self.date_to:
            for cur in self.currency_ids:
                URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={0}&date={1}{2}{3}&json'.format(
                    cur.currency.name, date_cur.strftime("%Y"), date_cur.strftime("%m"), date_cur.strftime("%d"))
                try:
                    res = json.load(urlopen(URL))
                except:
                    raise UserError(_('Could not connect to %s' % URL))
                for line in res:
                    rates.append((0, 0, {
                        'rate': line.get('rate', 1),
                        'company_id': self.env.company,
                        'currency': cur.currency.id,
                        'name': date_cur,
                    }))
            date_cur += datetime.timedelta(days=1)
        self.rates_ids = rates
        if not rates:
            self.name = _("Nothing to update")
        else:
            self.name = _("Successfully updated")
        return {
            'name': _('Import currency rates from NBU'),
            'res_model': 'ug.rates.from.nbu',
            'view_mode': 'form',
            'res_id': self.id,
            'context': {
                'default_name': self.name,
                'default_company': self.company,
                'default_date_from': self.date_from,
                'default_date_to': self.date_to,
                'default_rates_ids': self.rates_ids,
                'default_currency_ids': self.currency_ids,
                'active_ids': self._context.get('active_ids'),
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        # self.create_notification()


class UgImportRatesFromNbuList(models.TransientModel):
    _name = "ug.rates.from.nbu.list"
    _description = "Rates list"
    _order = 'name'

    wizard_id = fields.Many2one('ug.rates.from.nbu')
    currency = fields.Many2one('res.currency')
    name = fields.Date()
    company_id = fields.Many2one(
        related='wizard_id.company',
        string="Company")
    rate = fields.Float('Rate', digits=(12, 6))


class UgImportCurrencyFromNbuList(models.TransientModel):
    _name = "ug.currency.from.nbu.list"
    _description = "Currency list"

    wizard_id = fields.Many2one('ug.rates.from.nbu')
    currency = fields.Many2one('res.currency')
