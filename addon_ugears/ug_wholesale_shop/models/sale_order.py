import math
from datetime import datetime

from odoo import models, _, fields, api, Command
from odoo.exceptions import UserError, AccessError
from odoo.http import request
from rectpack import newPacker, PackingBin

from odoo.tools import float_is_zero

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pallet_id = fields.Many2one('distrib.packages.sizes', 'Pallet')
    package_line = fields.One2many(
        comodel_name='distrib.order.package.line',
        inverse_name='order_id',
        string="Packages Lines",
        states=LOCKED_FIELD_STATES,
        copy=True, auto_join=True)

    boxes_total = fields.Integer(string="Total boxes", store=True, compute='_compute_boxes')
    netto_total = fields.Float(string="Total netto", store=True, compute='_compute_boxes')
    brutto_total = fields.Float(string="Total brutto", store=True, compute='_compute_boxes')
    can_full_access = fields.Boolean(compute='_compute_access', string="Can Full Access")

    incoming_count = fields.Integer(string="Incoming Count", compute='_get_incoming')
    distrib_ids = fields.Many2many(
        comodel_name='distrib.distributors.move',
        string="Incoming Distributors",
        compute='_get_incoming',
        search='_search_distrib_ids',
        copy=False)

    total_product_uom_qty = fields.Float(
        string="Total Product Quantity",
        compute="_compute_total_product_uom_qty",
        store=True
    )

    @api.depends('order_line.product_uom_qty')
    def _compute_total_product_uom_qty(self):
        for order in self:
            order.total_product_uom_qty = sum(order.order_line.mapped('product_uom_qty'))

    def _get_confirmation_template(self):
        """ Get the mail template sent on SO confirmation (or for confirmed SO's).

        :return: `mail.template` record or None if default template wasn't found
        """
        return self.env.ref('ug_wholesale_shop.mail_template_sale_confirmation', raise_if_not_found=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])
            if vals.get('name', _("New")) == _("New"):
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['date_order'])
                ) if 'date_order' in vals else None
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'new.sale.order', sequence_date=seq_date) or _("New")

        return super().create(vals_list)

    def _compute_access(self):
        for record in self:
            if self.env.user.has_group('base.group_system'):
                record.can_full_access = True
            elif self.env.user.has_group('ug_base_distrib.group_distrib_user'):
                record.can_full_access = False
            else:
                record.can_full_access = True

    @api.depends('order_line.incoming_lines')
    def _get_incoming(self):
        for order in self:
            incoming = order.order_line.incoming_lines.move_id.filtered(
                lambda r: r.operation in ('inc')
            )
            order.distrib_ids = incoming
            order.incoming_count = len(incoming)

    def _search_distrib_ids(self, operator, value):
        if operator == 'in' and value:
            self.env.cr.execute("""
                SELECT array_agg(so.id)
                    FROM sale_order so
                    JOIN sale_order_line sol ON sol.order_id = so.id
                    JOIN sale_order_line_incoming_rel soli_rel ON soli_rel.order_line_id = sol.id
                    JOIN distrib_distributors_move_line aml ON aml.id = soli_rel.incoming_line_id
                    JOIN distrib_distributors_move am ON am.id = aml.move_id
                WHERE
                    am.operation in ('inc') AND
                    am.id = ANY(%s)
            """, (list(value),))
            so_ids = self.env.cr.fetchone()[0] or []
            return [('id', 'in', so_ids)]
        elif operator == '=' and not value:
            # special case for [('invoice_ids', '=', False)], i.e. "Invoices is not set"
            #
            # We cannot just search [('order_line.invoice_lines', '=', False)]
            # because it returns orders with uninvoiced lines, which is not
            # same "Invoices is not set" (some lines may have invoices and some
            # doesn't)
            #
            # A solution is making inverted search first ("orders with invoiced
            # lines") and then invert results ("get all other orders")
            #
            # Domain below returns subset of ('order_line.invoice_lines', '!=', False)
            order_ids = self._search([
                ('order_line.incoming_lines.move_id.operation', 'in', ('inc'))
            ])
            return [('id', 'not in', order_ids)]
        return [
            ('order_line.incoming_lines.move_id.operation', 'in', ('inc')),
            ('order_line.incoming_lines.move_id', operator, value),
        ]

    def _action_confirm(self):
        self._recalc_by_package()
        send_confirmation = self.env['ir.config_parameter'].sudo().get_param('distrib.send_confirmation',
                                                                         default=False)
        if bool(send_confirmation):
            template_mail = self.env.ref('ug_wholesale_shop.mail_template_sale_confirmation_for_robot', raise_if_not_found=False)
            template_mail.send_mail(self.id, force_send=True)
        return super(SaleOrder, self)._action_confirm()

    def _action_cancel(self):
        return super()._action_cancel()

    @api.depends('package_line.package_qty')
    def _compute_boxes(self):
        for order in self:
            # order = order.with_company(order.company_id)
            order_lines = order.package_line
            amount_boxes = sum(order_lines.mapped('package_qty'))
            amount_products = sum(order_lines.mapped('weight_netto'))
            amount_brutto = sum(order_lines.mapped('weight_brutto'))
            order.boxes_total = amount_boxes
            order.netto_total = amount_products
            order.brutto_total = amount_brutto

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        menu_id = self._context.get('menu_id', False)
        action = self._context.get('action', False)
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        return res

    def _prepare_distrib_move_inc(self):
        self.ensure_one()
        domain = [('partner_id', '=', self.partner_invoice_id.id)]
        distrib = self.env['distrib.distributors'].search(domain)[:1]

        return {
            'operation': 'inc',
            'currency_id': self.currency_id.id,
            'distrib_id': False if not distrib else distrib.id,
            'move_line': [],
            'sale_order_id': self.id,
            'user_id': self.user_id.id,
        }

    def _get_distrib_delivered_lines(self, final=False):
        # pending_section = None
        invoiceable_line_ids = []
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                # pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_distrib_deliver,
                                                                  precision_digits=precision):
                continue
            if line.qty_to_distrib_deliver > 0 or (
                    line.qty_to_distrib_deliver < 0 and final) or line.display_type == 'line_note':
                invoiceable_line_ids.append(line.id)
        return self.env['sale.order.line'].browse(invoiceable_line_ids)

    def create_distrib_move_inc(self):
        self.ensure_one()
        result = self._create_distrib_move_inc()
        if isinstance(result, dict):
            return result
        if result:
            return self.action_view_incomes()
        return {'type': 'ir.actions.act_window_close'}

    def action_view_incomes(self):
        incomes = self.mapped('distrib_ids')
        action = self.env['ir.actions.actions']._for_xml_id('ug_base_distrib.action_distrib_move_in')
        if len(incomes) > 1:
            action['domain'] = [('id', 'in', incomes.ids)]
        elif len(incomes) == 1:
            form_view = [(self.env.ref('ug_base_distrib.view_distributors_distrib_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = incomes.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_operation': 'inc',
        }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.name,
        #     })
        action['context'] = context
        return action


    def _create_distrib_move_inc(self):
        if not self.env['distrib.distributors.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['distrib.distributors.move']

        invoice_vals_list = []
        invoice_item_sequence = 0
        for order in self:
            order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)
            move_val = order._prepare_distrib_move_inc()
            if not move_val['distrib_id']:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Warning'),
                        'type': 'warning',
                        'message': _('Unable to find distributor for delivery'),
                        'sticky': True,
                    }
                }
            not_delivered_lines = order._get_distrib_delivered_lines(True)

            if not any(not line.display_type for line in not_delivered_lines):
                continue
            incoming_line_vals = []
            for line in not_delivered_lines:
                incoming_line_vals.append(
                    Command.create(
                        line._prepare_incoming_line(sequence=invoice_item_sequence)
                    ),
                )
                invoice_item_sequence += 1
            move_val['move_line'] += incoming_line_vals
            invoice_vals_list.append(move_val)

            moves = self.env['distrib.distributors.move'].sudo().with_context(default_operation='inc').create(invoice_vals_list)
            return moves

            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'display_notification',
            #     'params': {
            #         'title': _('Success'),
            #         'type': 'success',
            #         'message': _('The incoming document has been successfully generated.'),
            #         'sticky': True,
            #     }
            # }

    def _recalc_by_package(self):
        self.ensure_one()
        if self.state == 'draft':
            for line in self.order_line:
                product = line.product_id
                add_qty = line.product_uom_qty
                package = add_qty // product.qty_in_cartoon
                package_float = add_qty / product.qty_in_cartoon
                if package_float > package:
                    package += 1
                line.product_uom_qty = package * product.qty_in_cartoon

    def action_calculate_sale_order(self):
        self.ensure_one()
        url = '/shop/calculator?order=%s' % (
            self.id
        )
        # action = {
        #     'type': 'ir.actions.act_url',
        #     'target': 'self',
        #     'url': url,
        # }
        action = {
            'type': 'ir.actions.client',
            'name': 'Wholesale shop',
            'tag': 'start_shop',
            'params' : {
                'url': url,
            }
        }
        # last_order_id = request.session.get('order_for_calculate', 0)
        request.session['order_for_calculate'] = self.id
        if self.pallet_id:
            request.session['website_sale_current_palette'] = self.pallet_id.id
        else:
            now = datetime.timestamp(datetime.now())
            website = request.env['website'].get_current_website()
            palette = website.get_current_palette()
            request.session['website_sale_palette_time'] = now
            request.session['website_sale_current_palette'] = palette.id
        return action

    @api.model
    def get_import_templates(self):
        """returns the xlsx import template file"""
        return [{
            'label': _('Import Template for Distribution Order'),
            'template': '/ug_wholesale_shop/static/xls/template.xlsx'
        }]

    def _cart_find_package_line(self, cartoon_id, line_id=None, **kwargs):
        self.ensure_one()
        SaleOrderLine = self.env['distrib.order.package.line']

        if not self.package_line:
            return SaleOrderLine

        # cartoon = self.env['distrib.packages.sizes'].browse(cartoon_id)

        domain = [('order_id', '=', self.id), ('cartoon_id', '=', cartoon_id)]
        if line_id:
            domain += [('id', '=', line_id)]
        return SaleOrderLine.search(domain)

    def _prepare_package_line_update_values(
            self, order_line, quantity, **kwargs
    ):
        self.ensure_one()
        values = {}

        if quantity != order_line.package_qty:
            values['package_qty'] = quantity
        # if linked_line_id and linked_line_id != order_line.linked_line_id.id:
        #     values['linked_line_id'] = linked_line_id

        return values

    def _update_package_line_values(self, order_line, update_values):
        self.ensure_one()
        order_line.write(update_values)

    def _prepare_package_line_values(
            self, cartoon_id, quantity, **kwargs
    ):
        self.ensure_one()
        cartoon = self.env['distrib.packages.sizes'].browse(cartoon_id)

        if not cartoon:
            raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))

        values = {
            'cartoon_id': cartoon.id,
            'package_qty': quantity,
            'order_id': self.id,
        }
        return values

    def _cart_update_package_line(self, product_id, quantity, order_line, **kwargs):
        self.ensure_one()

        cartoon = product_id.cartoon_id
        package = 0 if product_id.qty_in_cartoon == 0 else quantity // product_id.qty_in_cartoon

        if order_line and package <= 0:
            # Remove zero or negative lines
            order_line.unlink()
            order_line = self.env['distrib.order.package.line']
        elif order_line:
            # Update existing line
            update_values = self._prepare_package_line_update_values(order_line, package, **kwargs)
            if update_values:
                self._update_package_line_values(order_line, update_values)
        elif package > 0:
            # Create new line
            order_line_values = self._prepare_package_line_values(cartoon.id, package, **kwargs)
            order_line = self.env['distrib.order.package.line'].sudo().create(order_line_values)
        return order_line

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        self = self.with_company(self.company_id)

        if self.state != 'draft':
            request.session.pop('sale_order_id', None)
            request.session.pop('website_sale_cart_quantity', None)
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))

        product = self.env['product.product'].browse(product_id).exists()
        if add_qty and (not product or not product._is_add_to_cart_allowed()):
            raise UserError(_("The given product does not exist therefore it cannot be added to cart."))

        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]
            # pack_line = self._cart_find_package_line(product.cartoon_id.id)[:1]
        else:
            order_line = self.env['sale.order.line']
            # pack_line = self.env['distrib.order.package.line']

        try:
            if add_qty:
                add_qty = int(add_qty)
        except ValueError:
            add_qty = 1

        # pack_quantity = 0
        if add_qty and not product.qty_in_cartoon == 0:
            package = add_qty // product.qty_in_cartoon
            package_float = add_qty / product.qty_in_cartoon
            if package_float > package:
                package += 1
            add_qty = package * product.qty_in_cartoon
            # pack_quantity = package
        else:
            add_qty = 0

        try:
            if set_qty:
                set_qty = int(set_qty)
        except ValueError:
            set_qty = 0

        if set_qty:
            package = set_qty // product.qty_in_cartoon
            package_float = set_qty / product.qty_in_cartoon
            if package_float > package:
                package += 1
            set_qty = package * product.qty_in_cartoon
            # pack_quantity = package

        quantity = 0

        if set_qty:
            quantity = set_qty
        elif set_qty == 0:
            quantity = set_qty
        elif add_qty is not None:
            if order_line:
                quantity = order_line.product_uom_qty + (add_qty or 0)
            else:
                quantity = add_qty or 0

        if quantity > 0:
            quantity, warning = self._verify_updated_quantity(
                order_line,
                product_id,
                quantity,
                **kwargs,
            )
        else:
            # If the line will be removed anyway, there is no need to verify
            # the requested quantity update.
            warning = ''

        order_line = self._cart_update_order_line(product_id, quantity, order_line, **kwargs)
        # pack_line = self._cart_update_package_line(product, quantity, pack_line, **kwargs)

        if (
                order_line
                and order_line.price_unit == 0
                and self.website_id.prevent_zero_price_sale
                and product.detailed_type not in self.env['product.template']._get_product_types_allow_zero_price()
        ):
            raise UserError(_(
                "The given product does not have a price therefore it cannot be added to cart.",
            ))
        self._apply_discount_if_needed()
        return {
            'line_id': order_line.id,
            # 'pack_id': pack_line.id,
            'quantity': quantity,
            'option_ids': list(
                set(order_line.option_line_ids.filtered(lambda l: l.order_id == order_line.order_id).ids)),
            'warning': warning,
        }

    def _get_package_from_order(self):
        self.ensure_one()
        value = {}
        values = []
        for line in self.order_line:
            pack_quantity = 0 if line.product_id.qty_in_cartoon == 0 else int(
                line.product_uom_qty / line.product_id.qty_in_cartoon)
            cartoon = line.cartoon_id
            pack_found = value.get(cartoon.id) or 0
            if not pack_found:
                pack_found = {}
                pack_found['box'] = cartoon
                pack_found['id'] = cartoon.id
                pack_found['name'] = cartoon.name
                pack_found['quantity'] = pack_quantity
                pack_found['lines'] = []
                pack_found['product_id'] = line.product_id.id
                value[cartoon.id] = pack_found
            else:
                pack_found['quantity'] = pack_found['quantity'] + pack_quantity
                value[cartoon.id] = pack_found

            pack_found['lines'].append(line)

        for key, value in value.items():
            values.append(value)

        return values

    def _fill_size_variants_and_pallet_limits(self, package_data, palette):
        for line in package_data:
            line['depth'] = line['box'].depth
            line['pallet11'] = 0 if line['box'].width == 0 else palette.width // line['box'].width
            line['pallet22'] = 0 if line['box'].height == 0 else palette.height // line['box'].height
            line['boxes_on_layer'] = line['pallet11'] * line['pallet22']

            line['pallet21'] = 0 if line['box'].width == 0 else palette.height // line['box'].width
            line['pallet12'] = 0 if line['box'].height == 0 else palette.width // line['box'].height
            line['boxes_on_layer2'] = line['pallet21'] * line['pallet12']

            line['max_boxes_on_layer'] = max(line['boxes_on_layer'], line['boxes_on_layer2'])
            line['min_boxes_on_layer'] = min(line['boxes_on_layer'], line['boxes_on_layer2'])
            line['max_layers'] = 0 if line['box'].depth == 0 else palette.depth // line['box'].depth
        return package_data

    def _refill_by_depth(self, package_data):
        value = {}
        values = []
        for line in package_data:
            depth = line['depth']
            pack_found = value.get(depth) or 0
            if not pack_found:
                value[depth] = []
            value[depth].append(line)

        for key, value in value.items():
            values.append(value)
        return values

    def _pack_to_layers(self, package_data, palette, rect_count=1, bin_count=1):
        layer_count = 0
        bins = []
        palettes_size = (palette.width, palette.height)
        # palettes_size = (palette.height, palette.width)
        rectangles = []
        for line in package_data:
            layer_count = layer_count + (
                0 if line['max_boxes_on_layer'] == 0 else line['quantity'] / line['max_boxes_on_layer'])
            # for x in range(line['quantity']):
            #     package = {'rectangles': (line['box'].width, line['box'].height),
            #                'max_boxes_on_layer': line['max_boxes_on_layer'],
            #                'min_boxes_on_layer': line['min_boxes_on_layer'],
            #                'depth': line['depth'], 'box_id': line['box'].id, 'product_id': line['product_id']}
            #     rectangles.append(package)
            for y in line['lines']:
                product_uom_qty = y.product_uom_qty
                product_id = y.product_id
                qtt = 0 if product_id.qty_in_cartoon == 0 else int(product_uom_qty // product_id.qty_in_cartoon)
                for z in range(qtt):
                    package = {'rectangles': (product_id.cartoon_id.width, product_id.cartoon_id.height),
                               'max_boxes_on_layer': line['max_boxes_on_layer'],
                               'min_boxes_on_layer': line['min_boxes_on_layer'],
                               'depth': line['depth'], 'box_id': product_id.cartoon_id.id, 'product_id': product_id.id}
                    rectangles.append(package)
                # rectangles.append((line['box'].width, line['box'].height))

        layer_count = math.ceil(layer_count) + 1
        for x in range(layer_count):
            bins.append(palettes_size)

        packer = newPacker(rotation=False)
        # Add the rectangles to packing queue
        # rect_count = 1
        for r in rectangles:
            packer.add_rect(*r['rectangles'],
                            rid=f'box_{rect_count}_{r["max_boxes_on_layer"]}_{r["min_boxes_on_layer"]}_{r["depth"]}_{r["box_id"]}_{r["product_id"]}')
            rect_count += 1

        for b in bins:
            packer.add_bin(*b)

        packer.pack()
        # for current_bin in range(len(packer.bin_list())):
        #     packed_rectangles = packer[current_bin]
        #     pass

        # Obtain number of bins used for packing
        nbins = len(packer)

        # Index first bin
        # abin = packer[0]

        # Bin dimmensions (bins can be reordered during packing)
        # width, height = abin.width, abin.height

        # Number of rectangles packed into first bin
        # nrect = len(packer[0])

        # Second bin first rectangle
        # rect = packer[0][0]

        # rect is a Rectangle object
        # x = rect.x  # rectangle bottom-left x coordinate
        # y = rect.y  # rectangle bottom-left y coordinate
        # w = rect.width
        # h = rect.height
        # bin_count = 1
        layers = []
        for abin in packer:
            layer = {}
            abin.bid = f'layer_{bin_count}'
            layer['bid'] = abin.bid
            # print(abin.bid)  # Bin id if it has one
            layer['layers'] = []
            for rect in abin:
                # print(rect)
                layer['layers'].append(rect)
            bin_count += 1
            layers.append(layer)

        PackagesSizes = self.env['distrib.packages.sizes']
        Product = self.env['product.template']
        for layer in layers:
            layer['max_boxes_on_layer'] = int(layer['layers'][0].rid.split('_')[2])
            layer['min_boxes_on_layer'] = int(layer['layers'][0].rid.split('_')[3])
            layer['depth'] = int(layer['layers'][0].rid.split('_')[4])
            box_id = layer['layers'][0].rid.split('_')[5]
            domain = [('id', '=', box_id)]
            box = PackagesSizes.search(domain)[:1]
            layer['box'] = box
            # all_weidth = sum([item['depth'] for item in palette])
            all_products_cnt = 0
            all_weights_cnt = 0
            for x in layer['layers']:
                product_id = int(x.rid.split('_')[6])
                dm = [('id', '=', product_id)]
                product = Product.search(dm)[:1]
                if product:
                    all_products_cnt += product.qty_in_cartoon
                    all_weights_cnt += product.cartoon_weight_with_model
            layer['product_cnt'] = all_products_cnt
            layer['product_weight'] = all_weights_cnt
        return layers

    def _fill_palettes(self, package_data, palette):
        max_depth = palette.depth
        palettes = []
        palette = []
        unselected = []
        # selected = []
        current_depth = 0
        for sublist in package_data:
            for item in sublist:
                if not item['full']:
                    unselected.append(item)
                    continue
                current_depth = current_depth + item['depth']
                if current_depth < max_depth:
                    palette.append(item)
                    # selected.append(item)
                else:
                    palettes.append(palette)
                    palette = []
                    palette.append(item)
                    current_depth = item['depth']
            pass

        if len(palette) > 0:
            palettes.append(palette)

        all_palettes = []
        id = 1000
        all_boxes = 0
        for palette in palettes:
            all_weidth = sum([item['depth'] for item in palette])
            fill = (100 * all_weidth) // max_depth
            difference = max_depth - all_weidth
            boxes = sum([len(item['layers']) for item in palette])
            product_cnt = sum([item['product_cnt'] for item in palette])
            product_weight = sum([item['product_weight'] for item in palette])
            info = {'id': id, 'fill': fill,
                    # 'fill_str': str(fill) + '% ' +  str(all_weidth) + 'mm',
                    'fill_str': str(fill) + '%',
                    'summ_width': all_weidth,
                    'difference': difference, 'palette': palette, 'boxes': boxes,
                    'product_cnt': product_cnt, 'product_weight': product_weight}
            id += 1000
            all_boxes += boxes
            all_palettes.append(info)
        all_boxes += sum([len(item['layers']) for item in unselected])

        values = {'unselected_layers': unselected, 'palettes': all_palettes, 'all_boxes': all_boxes}
        return values

    def _add_extra_layers_to_last_palette(self, palettes, palette):
        unselected_layers = sorted(palettes['unselected_layers'], key=lambda d: d['fill'], reverse=True)
        all_palettes = palettes['palettes']
        choice = 1
        for item in unselected_layers:
            try:
                if item['choice']:
                    continue
            except KeyError:
                pass
            width = item['depth']
            for item_palette in all_palettes:
                try:
                    if item_palette['choice']:
                        continue
                except KeyError:
                    pass
                max_width = item_palette['difference']
                if width <= max_width:
                    item_palette['choice'] = choice
                    item['choice'] = choice
                    choice += 1
                else:
                    item_palette['choice'] = 0
                    try:
                        if not item['choice']:
                            item['choice'] = 0
                    except KeyError:
                        item['choice'] = 0

        for i in range(choice):
            if i == 0:
                continue
            try:
                found_unselected = next(filter(lambda x: x['choice'] == i, unselected_layers))
                found_palette = next(filter(lambda y: y['choice'] == i, all_palettes))

                found_palette['palette'].append(found_unselected)
                found_palette['summ_width'] = sum([item['depth'] for item in found_palette['palette']])
                found_palette['difference'] = palette.depth - found_palette['summ_width']
                found_palette['fill'] = (100 * found_palette['summ_width']) // palette.depth
                found_palette['fill_str'] = str(found_palette['fill']) + '%'
                boxes = len(found_unselected['layers'])
                # product_cnt = sum([item['product_cnt'] for item in found_palette['palette']])
                found_palette['boxes'] += boxes
                # found_palette['product_cnt'] += product_cnt

                unselected_layers.remove(found_unselected)
            except KeyError:
                pass
            except StopIteration:
                pass
        palettes['unselected_layers'] = unselected_layers

        for x in palettes['palettes']:
            x['product_cnt'] = sum([item['product_cnt'] for item in x['palette']])
            x['product_weight'] = sum([item['product_weight'] for item in x['palette']])
            x['self_height'] = palette.self_height
            x['cartoon_weight'] = palette.cartoon_weight

        product_cnt = sum([item['product_cnt'] for item in palettes['unselected_layers']])
        product_weight = sum([item['product_weight'] for item in palettes['unselected_layers']])
        product_cnt += sum([item['product_cnt'] for item in palettes['palettes']])
        product_weight += sum([item['product_weight'] for item in palettes['palettes']])

        # palettes['all_products'] = product_cnt
        palettes['all_products'] = self.total_product_uom_qty
        palettes['all_weight'] = product_weight

        return palettes

    def _calculate_package_list(self, package_data, palette_id):
        PackagesSizes = self.env['distrib.packages.sizes']
        domain = [('id', '=', palette_id)]
        palette = PackagesSizes.search(domain)[:1]
        package_data = self._fill_size_variants_and_pallet_limits(package_data, palette)
        package_data_by_depth = self._refill_by_depth(package_data)
        layers_by_depth = []
        for depth in package_data_by_depth:
            layers = self._pack_to_layers(depth, palette)
            for layer in layers:
                if layer['min_boxes_on_layer'] <= len(layer['layers']) <= layer['max_boxes_on_layer'] or len(
                        layer['layers']) > layer['max_boxes_on_layer']:
                    # if len(layer['layers']) >= layer['max_boxes_on_layer']:
                    layer['full'] = True
                    layer['fill'] = 100
                else:
                    layer['full'] = False
                    layer['fill'] = (100 * len(layer['layers'])) // layer['max_boxes_on_layer']
            layers_by_depth.append(layers)

        # product_cnt_before = 0
        # product_weight_before = 0
        # for x in layers_by_depth:
        #     product_cnt_before += sum([item['product_cnt'] for item in x])
        #     product_weight_before += sum([item['product_weight'] for item in x])
        palettes1 = self._fill_palettes(layers_by_depth, palette)

        palettes = self._add_extra_layers_to_last_palette(palettes1, palette)

        # product_cnt = sum([item['product_cnt'] for item in palettes['unselected_layers']])
        # product_weight = sum([item['product_weight'] for item in palettes['unselected_layers']])
        # product_cnt += sum([item['product_cnt'] for item in palettes['palettes']])
        # product_weight += sum([item['product_weight'] for item in palettes['palettes']])
        # for x in palettes['palettes']:
        #     product_cnt += x['product_cnt']

        # palettes['all_products'] = product_cnt
        # palettes['all_weight'] = product_weight
        return palettes

    def _get_package_line_data(self):
        self.package_line.unlink()
        package_data = self._get_package_from_order()
        data = []
        for package in package_data:
            line = {}
            line['order_id'] = self.id
            line['cartoon_id'] = package['box'].id
            line['package_qty'] = package['quantity']
            netto = sum([item.product_id.weight * item.product_uom_qty for item in package['lines']])
            # brutto = sum([item.product_id.weight * item.product_uom_qty + package['quantity'] * package['box'].cartoon_weight for item in package['lines']])
            brutto = package['box'].cartoon_weight * package['quantity'] + netto
            line['weight_netto'] = netto
            line['weight_brutto'] = brutto
            data.append((0, 0, line))
        return data

    def _get_packing_list(self):
        self.ensure_one()
        package_data = self._get_package_from_order()
        palette_id = self.pallet_id.id
        if palette_id:
            return self._calculate_package_list(package_data, palette_id)
        return {
            'unselected_layers': [],
            'palettes': [],
            'all_products': 0,
            'all_weight': 0,
            'all_boxes': 0
        }

    def _apply_discount_if_needed(self):
        self.ensure_one()
        discount_setting = self.env.user.has_group('product.group_discount_per_so_line')
        if not discount_setting:
            return
        distrib_ids = self.partner_id.distrib_ids
        if not distrib_ids:
            return
        distrib_id = distrib_ids[0]
        if not distrib_id.discount_available:
            return
        if self.price_total_no_discount < distrib_id.discount_after:
            self.order_line.update({'discount' : 0})
        else:
            for line in self.order_line:
                Rules = self.env['distrib.discount.rules']
                excluded = Rules._excluded_position(line)
                if excluded:
                    line.update({'discount': 0})
                    continue
                line.update({'discount': distrib_id.discount_value})
            # self.order_line.update({'discount' : distrib_id.discount_value})
