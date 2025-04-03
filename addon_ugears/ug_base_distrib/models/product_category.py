from re import search
import operator as py_operator
from odoo import api, models, _, fields
from odoo.exceptions import UserError
from odoo.tools import float_round

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class PublicProduct(models.Model):
    _inherit = "product.template"

    guid = fields.Char(string='Guid 1C:Enterprise')
    qty_available_dist = fields.Float(
        'Quantity On Distributor', compute='_compute_quantities_dist', search='_search_qty_available',
        compute_sudo=False, digits='Product Unit of Measure')
    theme_id = fields.Many2one('distrib.product.theme','Theme')
    region_ids = fields.Many2many('distrib.regions', string='Regions')

    def _compute_quantities_dist(self):
        res = self._compute_quantities_dict_dist()
        for template in self:
            template.qty_available_dist = res[template.id]['qty_available_dist']

    def _search_qty_available(self, operator, value):
        domain = [('qty_available_dist', operator, value)]
        product_variant_query = self.env['product.product']._search(domain)
        return [('product_variant_ids', 'in', product_variant_query)]

    def _compute_quantities_dict_dist(self):
        variants_available = {
            p['id']: p for p in self.product_variant_ids._origin.read(['qty_available_dist'])
        }
        prod_available = {}
        for template in self:
            qty_available_dist = 0
            for p in template.product_variant_ids._origin:
                qty_available_dist += variants_available[p.id]["qty_available_dist"]

            prod_available[template.id] = {
                "qty_available_dist": qty_available_dist,
            }
        return prod_available

    def action_open_distrib_quants(self):
        return self.product_variant_ids.filtered(lambda p: p.active or p.qty_available != 0).action_open_distrib_quants()

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(['name'])
        return [(template.id, '%s' % (template.name))
                for template in self]

    def _compute_item_count(self):
        is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")
        is_user = self.env.user.has_group("ug_base_distrib.group_distrib_user")
        user = is_user and not is_manager

        for template in self:
            # Pricelist item count counts the rules applicable on current template or on its variants.
            if user:
                template.pricelist_item_count = template.env['product.pricelist.item'].search_count([
                    '&', ('pricelist_id', '=', self.env.user.distrib_id.pricelist_id.id), '|', ('product_tmpl_id', '=', template.id), ('product_id', 'in', template.product_variant_ids.ids)])
            else:
                template.pricelist_item_count = template.env['product.pricelist.item'].search_count([
                    '|', ('product_tmpl_id', '=', template.id), ('product_id', 'in', template.product_variant_ids.ids)])

    def open_pricelist_rules(self):
        self.ensure_one()
        is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")
        is_user = self.env.user.has_group("ug_base_distrib.group_distrib_user")
        user = is_user and not is_manager
        if user:
            domain = [
                    '&', ('pricelist_id', '=', self.env.user.distrib_id.pricelist_id.id),
                    '|', ('product_tmpl_id', '=', self.id),
                    ('product_id', 'in', self.product_variant_ids.ids)]
        else:
            domain = ['|',
                      ('product_tmpl_id', '=', self.id),
                      ('product_id', 'in', self.product_variant_ids.ids)]

        return {
            'name': _('Price Rules'),
            'view_mode': 'tree,form',
            'views': [(self.env.ref('product.product_pricelist_item_tree_view_from_product').id, 'tree')],
            'res_model': 'product.pricelist.item',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {
                'default_product_tmpl_id': self.id,
                'default_applied_on': '1_product',
                'product_without_variants': self.product_variant_count == 1,
            },
        }


class PublicProductDistrib(models.Model):
    _inherit = "product.product"

    quant_ids = fields.One2many('distrib.quant', 'product_id')  # used to compute quantities
    move_ids = fields.One2many('distrib.distributors.move.line', 'product_id')  # used to compute quantities
    qty_available_dist = fields.Float('Quantity On Distributor',
                                      compute='_compute_quantities_dist',
                                      search='_search_quantities_dist',
                                      digits='Product Unit of Measure', compute_sudo=False,
                                      help="Current quantity of products.\n"
                                           "In a context with a single Stock Location, this includes "
                                           "goods stored at this Location, or any of its children.\n"
                                           "In a context with a single Warehouse, this includes "
                                           "goods stored in the Stock Location of this Warehouse, or any "
                                           "of its children.\n"
                                           "stored in the Stock Location of the Warehouse of this Shop, "
                                           "or any of its children.\n"
                                           "Otherwise, this includes goods stored in any Stock Location "
                                           "with 'internal' type.")
    virtual_available_dist = fields.Float(
        'Forecasted Quantity Distributor', compute='_compute_quantities_dist',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Forecast quantity (computed as Quantity On Hand "
             "- Outgoing + Incoming)\n"
             "In a context with a single Stock Location, this includes "
             "goods stored in this location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")

    incoming_qty_dist = fields.Float(
        'Incoming Qtt', compute='_compute_quantities_dist',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Quantity of planned incoming products.\n"
             "In a context with a single Stock Location, this includes "
             "goods arriving to this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods arriving to the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods arriving to any Stock "
             "Location with 'internal' type.")
    outgoing_qty_dist = fields.Float(
        'Outgoing Qtt', compute='_compute_quantities_dist',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Quantity of planned outgoing products.\n"
             "In a context with a single Stock Location, this includes "
             "goods leaving this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods leaving the Stock Location of this Warehouse, or "
             "any of its children.\n"
             "Otherwise, this includes goods leaving any Stock "
             "Location with 'internal' type.")

    def _search_quantities_dist(self, operator, value):
        return self._search_product_quantity(operator, value, 'qty_available_dist')

    def _search_product_quantity(self, operator, value, field):
        # TDE FIXME: should probably clean the search methods
        # to prevent sql injections
        if field not in ('qty_available_dist', 'virtual_available_dist', 'incoming_qty_dist', 'outgoing_qty_dist'):
            raise UserError(_('Invalid domain left operand %s', field))
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise UserError(_('Invalid domain operator %s', operator))
        if not isinstance(value, (float, int)):
            raise UserError(_("Invalid domain right operand '%s'. It must be of type Integer/Float", value))

        # TODO: Still optimization possible when searching virtual quantities
        ids = []
        # Order the search on `id` to prevent the default order on the product name which slows
        # down the search because of the join on the translation table to get the translated names.
        for product in self.with_context(prefetch_fields=False).search([], order='id'):
            if OPERATORS[operator](product[field], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    @api.depends('move_ids.product_uom_qty', 'move_ids.state')
    @api.depends_context('uid', 'from_date', 'to_date', )
    def _compute_quantities_dist(self):
        distrib_id = self.env.user.distrib_id.id
        if not distrib_id:
            distrib_id = self._context.get('distrib')
        products = self.filtered(lambda p: p.type != 'service')
        res = products._compute_quantities_dict_dist(distrib_id, self._context.get('from_date'),
                                                     self._context.get('to_date'))
        for product in products:
            product.update(res[product.id])
        # Services need to be set with 0.0 for all quantities
        services = self - products
        services.qty_available_dist = 0.0
        services.incoming_qty_dist = 0.0
        services.outgoing_qty_dist = 0.0
        services.virtual_available_dist = 0.0

    def _compute_quantities_dict_dist(self, distrib_id, from_date=False, to_date=False, no_inventory=False):
        dates_in_the_past = False
        # only to_date as to_date will correspond to qty_available
        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True

        domain_quant = [('product_id', 'in', self.ids)]
        domain_move_in = [('product_id', 'in', self.ids)]
        domain_move_in += [('operation', '=', 'inc')]
        domain_move_in += [('state', '=', 'done')]
        if no_inventory:
            domain_move_in += [('is_inventory', '=', False)]
        domain_move_out = [('product_id', 'in', self.ids)]
        domain_move_out += [('operation', '=', 'out')]
        domain_move_out += [('state', '=', 'done')]

        if distrib_id:
            domain_move_in += [('distrib_id', '=', distrib_id)]
            domain_move_out += [('distrib_id', '=', distrib_id)]
            domain_quant += [('distrib_id', '=', distrib_id)]

        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)

        if from_date:
            date_date_expected_domain_from = [('date', '>=', from_date)]
            domain_move_in += date_date_expected_domain_from
            domain_move_out += date_date_expected_domain_from
        if to_date:
            date_date_expected_domain_to = [('date', '<=', to_date)]
            domain_move_in += date_date_expected_domain_to
            domain_move_out += date_date_expected_domain_to

        Move = self.env['distrib.distributors.move.line'].with_context(active_test=False)
        Quant = self.env['distrib.quant'].with_context(active_test=False)

        moves_in_res = dict((item['product_id'][0], item['product_uom_qty']) for item in
                            Move._read_group(domain_move_in, ['product_id', 'product_uom_qty'], ['product_id'],
                                             orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_uom_qty']) for item in
                             Move._read_group(domain_move_out, ['product_id', 'product_uom_qty'], ['product_id'],
                                              orderby='id'))
        quants_res = dict((item['product_id'][0], (item['quantity'])) for item in
                          Quant._read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
        if dates_in_the_past:
            # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_uom_qty']) for item in
                                     Move._read_group(domain_move_in_done, ['product_id', 'product_uom_qty'],
                                                      ['product_id'], orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_uom_qty']) for item in
                                      Move._read_group(domain_move_out_done, ['product_id', 'product_uom_qty'],
                                                       ['product_id'], orderby='id'))
        res = dict()
        for product in self.with_context(prefetch_fields=False):
            origin_product_id = product._origin.id
            product_id = product.id
            if not origin_product_id:
                res[product_id] = dict.fromkeys(
                    ['qty_available_dist', 'incoming_qty_dist', 'outgoing_qty_dist', 'virtual_available_dist'],
                    0.0,
                )
                continue

            begin_ost = quants_res.get(origin_product_id, 0.0)
            # try:
            #     begin_ost = qnt[0]
            # except:
            #     begin_ost = qnt

            rounding = product.uom_id.rounding
            res[product_id] = {}
            if dates_in_the_past:
                qty_available_dist = begin_ost - moves_in_res_past.get(origin_product_id,
                                                                       0.0) + moves_out_res_past.get(
                    origin_product_id, 0.0)
            else:
                qty_available_dist = begin_ost
            res[product_id]['qty_available_dist'] = float_round(qty_available_dist, precision_rounding=rounding)
            res[product_id]['incoming_qty_dist'] = float_round(moves_in_res.get(origin_product_id, 0.0),
                                                               precision_rounding=rounding)
            res[product_id]['outgoing_qty_dist'] = float_round(moves_out_res.get(origin_product_id, 0.0),
                                                               precision_rounding=rounding)
            res[product_id]['virtual_available_dist'] = float_round(
                qty_available_dist + res[product_id]['incoming_qty_dist'] - res[product_id]['outgoing_qty_dist'],
                precision_rounding=rounding)
        return res

    def action_open_distrib_quants(self):
        if len(self) == 1:
            self = self.with_context(
                default_product_id=self.id,
                single_product=True
            )
        else:
            self = self.with_context(product_tmpl_ids=self.product_tmpl_id.ids)
        action = self.env['distrib.quant'].action_view_inventory()
        action['domain'] = [('product_id', 'in', self.ids)]
        action["name"] = _('Update Quantity')
        return action

    def name_get(self):
        result = []
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            result.append((product.id, name))
        return result


class ProductCategoryImport(models.Model):
    _inherit = 'product.category'
    guid = fields.Char(string='Guid 1C:Enterprise')

    @api.model
    def get_import_templates(self):
        """returns the xlsx import template file"""
        return [{
            'label': _('Import Template for Product Categories'),
            'template': '/ug_base_distrib/static/xls/category_template.xlsx'
        }]
