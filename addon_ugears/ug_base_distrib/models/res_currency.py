from odoo import models, fields, api, _
import json
from urllib.request import urlopen

from odoo.exceptions import UserError


class ResCurrency(models.Model):
    _inherit = "res.currency"
    code = fields.Char(string='Code of currency', size=3)

    @api.model
    def _update_val_code(self):
        for vals in self.search([('name', '=', 'USD')]):
            vals.code = "840"
        for vals in self.search([('name', '=', 'EUR')]):
            vals.code = "978"
        for vals in self.search([('name', '=', 'UAH')]):
            vals.code = "980"

    def load_from_nbu(self):
        for rec in self:
            URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={0}&json'.format(rec.name)
            try:
                res = json.load(urlopen(URL))
            except:
                raise UserError(_('Could not connect to %s' % URL))
            for line in res:
                rec.code = line.get('r030', '')
