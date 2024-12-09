from odoo import models, fields, tools, api


class Product(models.Model):
    _inherit = "product.template"

    weight = fields.Float('Weight model, gram', digits=(16, 1))
    qty_in_cartoon = fields.Integer('Quantity in cartoon', default=0)
    cartoon_id = fields.Many2one('distrib.packages.sizes', 'Cartoon')
    cartoon_weight_with_model = fields.Float('Cartoon weight with model, gram', store=True,
                                             compute='_compute_cartoon_weight_with_model')

    @api.depends('cartoon_id.cartoon_weight','weight','qty_in_cartoon')
    def _compute_cartoon_weight_with_model(self):
        for line in self:
            cartoon_weight_with_model = line.weight * line.qty_in_cartoon + line.cartoon_id.cartoon_weight
            cartoon_weight_with_model = tools.float_round(cartoon_weight_with_model,1)
            line.cartoon_weight_with_model = cartoon_weight_with_model


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'
    guid = fields.Char(string='Guid 1C:Enterprise')
