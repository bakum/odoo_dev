import math

from odoo import models, _, fields, api
from odoo.exceptions import UserError
from odoo.http import request
from rectpack import newPacker, PackingBin

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

    def _cart_update_package_line(self, cartoon_id, quantity, order_line, **kwargs):
        self.ensure_one()

        if order_line and quantity <= 0:
            # Remove zero or negative lines
            order_line.unlink()
            order_line = self.env['distrib.order.package.line']
        elif order_line:
            # Update existing line
            update_values = self._prepare_package_line_update_values(order_line, quantity, **kwargs)
            if update_values:
                self._update_package_line_values(order_line, update_values)
        elif quantity > 0:
            # Create new line
            order_line_values = self._prepare_package_line_values(cartoon_id, quantity, **kwargs)
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
        # pack_line = self._cart_update_package_line(product.cartoon_id.id, pack_quantity, pack_line, **kwargs)

        if (
                order_line
                and order_line.price_unit == 0
                and self.website_id.prevent_zero_price_sale
                and product.detailed_type not in self.env['product.template']._get_product_types_allow_zero_price()
        ):
            raise UserError(_(
                "The given product does not have a price therefore it cannot be added to cart.",
            ))

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
            pack_quantity = int(line.product_uom_qty / line.product_id.qty_in_cartoon)
            cartoon = line.cartoon_id
            pack_found = value.get(cartoon.id) or 0
            if not pack_found:
                pack_found = {}
                pack_found['box'] = cartoon
                pack_found['id'] = cartoon.id
                pack_found['name'] = cartoon.name
                pack_found['quantity'] = pack_quantity
                pack_found['lines'] = []
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
            line['pallet11'] = palette.width // line['box'].width
            line['pallet22'] = palette.height // line['box'].height
            line['boxes_on_layer'] = line['pallet11'] * line['pallet22']

            line['pallet21'] = palette.height // line['box'].width
            line['pallet12'] = palette.width // line['box'].height
            line['boxes_on_layer2'] = line['pallet21'] * line['pallet12']

            line['max_boxes_on_layer'] = max(line['boxes_on_layer'], line['boxes_on_layer2'])
            line['min_boxes_on_layer'] = min(line['boxes_on_layer'], line['boxes_on_layer2'])
            line['max_layers'] = palette.depth // line['box'].depth
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
            for x in range(line['quantity']):
                package = {'rectangles': (line['box'].width, line['box'].height),
                           'max_boxes_on_layer': line['max_boxes_on_layer'],
                           'min_boxes_on_layer': line['min_boxes_on_layer'],
                           'depth': line['depth'], 'box_id': line['box'].id}
                rectangles.append(package)
                # rectangles.append((line['box'].width, line['box'].height))

        layer_count = math.ceil(layer_count)
        for x in range(layer_count):
            bins.append(palettes_size)

        packer = newPacker(rotation=False)
        # Add the rectangles to packing queue
        # rect_count = 1
        for r in rectangles:
            packer.add_rect(*r['rectangles'],
                            rid=f'box_{rect_count}_{r["max_boxes_on_layer"]}_{r["min_boxes_on_layer"]}_{r["depth"]}_{r["box_id"]}')
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
        nrect = len(packer[0])

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
        for layer in layers:
            layer['max_boxes_on_layer'] = int(layer['layers'][0].rid.split('_')[2])
            layer['min_boxes_on_layer'] = int(layer['layers'][0].rid.split('_')[3])
            layer['depth'] = int(layer['layers'][0].rid.split('_')[4])
            box_id = layer['layers'][0].rid.split('_')[5]
            domain = [('id', '=', box_id)]
            box = PackagesSizes.search(domain)[:1]
            layer['box'] = box
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
            info = {'id': id, 'fill': fill,
                    # 'fill_str': str(fill) + '% ' +  str(all_weidth) + 'mm',
                    'fill_str': str(fill) + '%',
                    'summ_width': all_weidth,
                    'difference': difference, 'palette': palette, 'boxes': boxes}
            id += 1000
            all_boxes += boxes
            all_palettes.append(info)
        all_boxes += sum([len(item['layers']) for item in unselected])
        values = {'unselected_layers': unselected, 'palettes': all_palettes, 'all_boxes': all_boxes}
        return values

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

        palettes = self._fill_palettes(layers_by_depth, palette)

        return palettes
