from odoo import models, fields, api, Command


class SaleOrder(models.Model):
    _inherit = "sale.order.line"

    cartoon_id = fields.Many2one(
        related='product_template_id.cartoon_id',
        string="Cartoon ID",
        store=True, precompute=True)
    qty_delivered_method = fields.Selection(selection_add=[('distrib_move', 'Distributor Moves')])
    distrib_move_ids = fields.One2many('distrib.distributors.move', 'sale_line_id', string='Distributor Moves')
    qty_to_distrib_deliver = fields.Float(compute='_compute_qty_to_distrib_deliver', digits='Product Unit of Measure')
    display_qty_distrib_widget = fields.Boolean(compute='_compute_qty_to_distrib_deliver')

    incoming_lines = fields.Many2many(
        comodel_name='distrib.distributors.move.line',
        relation='sale_order_line_incoming_rel', column1='order_line_id', column2='incoming_line_id',
        string="Incoming Lines",
        copy=False)

    def _prepare_incoming_line(self, **optional_values):
        self.ensure_one()
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'product_uom_qty': self.qty_to_distrib_deliver,
            'price_unit': self.price_unit,
            'discount': self.discount,
            'sale_line_ids': [Command.link(self.id)],
        }
        if optional_values:
            res.update(optional_values)
        return res

    def _get_outgoing_incoming_moves(self):
        outgoing_moves_ids = set()
        incoming_moves_ids = set()

        moves = self.incoming_lines.filtered(lambda r: r.state != 'cancel' and self.product_id == r.product_id)
        if self._context.get('accrual_entry_date'):
            moves = moves.filtered(lambda r: fields.Date.context_today(r, r.date) <= self._context['accrual_entry_date'])

        for move in moves:
            if move.credit > 0.0:
                outgoing_moves_ids.add(move.id)
            elif move.debit > 0.0:
                incoming_moves_ids.add(move.id)

        return self.env['distrib.distributors.move.line'].browse(outgoing_moves_ids), self.env['distrib.distributors.move.line'].browse(incoming_moves_ids)

    @api.depends('product_id')
    def _compute_qty_delivered_method(self):
        """ Stock module compute delivered qty for product [('type', 'in', ['consu', 'product'])]
            For SO line coming from expense, no picking should be generate: we don't manage stock for
            those lines, even if the product is a storable.
        """
        super(SaleOrder, self)._compute_qty_delivered_method()

        for line in self:
            if not line.is_expense and line.product_id.type in ['consu', 'product']:
                line.qty_delivered_method = 'distrib_move'

    @api.depends('incoming_lines.state','incoming_lines.debit','incoming_lines.credit')
    def _compute_qty_delivered(self):
        super(SaleOrder, self)._compute_qty_delivered()

        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.qty_delivered_method == 'distrib_move':
                qty = 0.0
                outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
                for move in outgoing_moves:
                    if move.state != 'done':
                        continue
                    qty -= move.product_uom._compute_quantity(move.credit, line.product_uom, rounding_method='HALF-UP')
                for move in incoming_moves:
                    if move.state != 'done':
                        continue
                    qty += move.product_uom._compute_quantity(move.debit, line.product_uom, rounding_method='HALF-UP')
                line.qty_delivered = qty


    @api.depends('product_uom_qty', 'qty_delivered', 'state', 'incoming_lines', 'product_uom')
    def _compute_qty_to_distrib_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_distrib_deliver = line.product_uom_qty - line.qty_delivered
            if line.state in ('draft', 'sent',
                              'sale') and line.product_uom and line.qty_to_distrib_deliver > 0:
                if line.state == 'sale' and not line.incoming_lines:
                    line.display_qty_distrib_widget = False
                else:
                    line.display_qty_distrib_widget = True
            else:
                line.display_qty_distrib_widget = False