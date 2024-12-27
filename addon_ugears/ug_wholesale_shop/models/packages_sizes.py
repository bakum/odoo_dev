from odoo import models, fields, _, api


class PackagesSizes(models.Model):
    _name = 'distrib.packages.sizes'
    _description = 'Packages Sizes'

    active = fields.Boolean(default=True)
    ref = fields.Char(string="Ref", copy=False, readonly=True, default=lambda self: _("New"))
    name = fields.Char(string='Name', copy=False, required=False)
    width = fields.Integer('Width, mm', required=True)
    height = fields.Integer('Height, mm', required=True)
    depth = fields.Integer('Depth, mm', required=True)
    cartoon_weight = fields.Float('Cartoon Weight, gram', digits=(16, 1), default=0.0)
    type_of = fields.Selection(
        selection=[
            ('package', "Package"),
            ('box', "Cartoon"),
            ('pallet', "Pallet"),
        ],
        string="Type of package",
        copy=True, default='box')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = str(vals['width']) + 'x' + str(vals['height']) + 'x' + str(vals['depth'])
            vals['ref'] = str(vals['width']) + 'x' + str(vals['height']) + 'x' + str(vals['depth'])
        return super(PackagesSizes, self).create(vals_list)

    def name_get(self):
        result = []
        for sizes in self:
            # name = sizes.name
            name = '%s - %s' % (sizes.type_of, sizes.name)
            result.append((sizes.id, name))
        return result

    @api.onchange('width','height','depth')
    def _onchange_type(self):
        for vals in self:
            vals.name = str(vals['width']) + 'x' + str(vals['height']) + 'x' + str(vals['depth'])
            vals.ref = str(vals['width']) + 'x' + str(vals['height']) + 'x' + str(vals['depth'])

