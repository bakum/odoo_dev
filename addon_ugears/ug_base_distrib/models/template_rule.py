from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval


class TemplateRules(models.Model):
    _name = 'distrib.template.rules'
    _description = 'Distributors generic template rules'

    name = fields.Char('Ref', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    move_line = fields.One2many(
        comodel_name='distrib.template.rules.line',
        inverse_name='move_id',
        string="Rule Lines",
        copy=True)
    main_req = fields.Integer("Main Rule", required=True, default=1)
    filter_domain = fields.Char(default="[]")
    active = fields.Boolean(default=True)

    @api.constrains('main_req')
    def _check_main_req(self):
        for rec in self:
            domain = ['|', ('active', '=', True), ('active', '=', False)]
            count = self.sudo().search_count(domain)
            if count > 1:
                raise ValidationError(_("Distributors generic template rules should be unique"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = 'Default Templates Rule'
        return super(TemplateRules, self).create(vals_list)

    def unlink(self):
        return super(TemplateRules, self).unlink()

    def get_excluded_categories(self):
        """ Returns a list of categories that are excluded by the current template rules. """
        self.ensure_one()
        return self.move_line.mapped('categ_id.id')

    def _get_eval_context(self):
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            'datetime': safe_eval.datetime,
            'dateutil': safe_eval.dateutil,
            'time': safe_eval.time,
            'uid': self.env.uid,
            'user': self.env.user,
        }

    def _eval_domain(self, domain):
        self.ensure_one()
        return safe_eval.safe_eval(domain, self._get_eval_context())


class TemplateRulesLines(models.Model):
    _name = 'distrib.template.rules.line'
    _description = 'Distributors generic template rules lines'

    move_id = fields.Many2one(
        comodel_name='distrib.template.rules',
        string="Template Rule Reference",
        required=True, ondelete='cascade', index=True, copy=False)

    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True)
