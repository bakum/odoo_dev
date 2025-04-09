import json
# import pytz

from odoo import http, fields, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools import float_compare

CHANNEL_MAP = {
    'qtt_Channel_0001': 'Channel_0001',
    'qtt_Channel_0002': 'Channel_0002',
    'qtt_Channel_0003': 'Channel_0003',
    'qtt_Channel_0004': 'Channel_0004',
    'qtt_Channel_0005': 'Channel_0005',
}


def get_id_from_ext_id(ext_id):
    ext = http.request.env['ir.model.data'].sudo().search([('name', '=', ext_id)], limit=1)
    id = False
    if len(ext) > 0:
        for line in ext:
            id = line.res_id
    return ext_id if not id else id


def get_recordset_from_ext_id(ext_id):
    ext = http.request.env['ir.model.data'].sudo().search([('name', '=', ext_id)], limit=1)
    id = None
    mn = None
    if len(ext) > 0:
        for line in ext:
            id = line.res_id
            mn = line.model
    if id:
        return http.request.env[mn].sudo().search([('id', '=', id)])
    return ext_id


def apply_id_from_ext_id(ext_id_dict):
    key_for_del = []
    for key, value in ext_id_dict.items():
        if 'id' in key:
            if key == 'guid' or key == 'id' or 'ids' in key:
                continue
            new_value = get_id_from_ext_id(value)
            if isinstance(new_value, int):
                ext_id_dict[key] = new_value
            if isinstance(new_value, str):
                key_for_del.append(key)
    for x in key_for_del:
        del ext_id_dict[x]


def apply_distrib_from_request(search_criterias, guid, pricelist_guid):
    partner_sudo = http.request.env['res.partner'].sudo()
    try:
        if guid:
            partner_sudo = partner_sudo.search([('guid', '=', guid)])[:1]
            if partner_sudo:
                if pricelist_guid:
                    pricelist = http.request.env['product.pricelist'].sudo().search([('guid', '=', pricelist_guid)])[:1]
                    if pricelist:
                        partner_sudo.create_distributor(pricelist.id)
                    else:
                        partner_sudo.create_distributor()
                else:
                    partner_sudo.create_distributor()
        else:
            return {"success": False, 'error': 'No guid provided'}

        if partner_sudo:
            new_dict = partner_sudo.read(list(set(http.request.env['res.partner']._fields)))
            return {"success": True, 'result': new_dict}
        else:
            return {"success": False, 'error': 'Partner not found'}

    except Exception as e:
        return {"success": False, 'error': str(e)}


def apply_pricelist_from_request(search_criterias, guid):
    pricelist_sudo = http.request.env['product.pricelist'].sudo()
    pricelist = pricelist_sudo
    try:
        if guid:
            pricelist = pricelist_sudo.search([('guid', '=', guid)])[:1]

        id_ext = search_criterias.get('id')
        del search_criterias['id']
        price_items = search_criterias.get('item_ids')
        del search_criterias['item_ids']
        apply_id_from_ext_id(search_criterias)

        if pricelist:
            written = pricelist.write(search_criterias)
            mod = {"success": written}
        else:
            pricelist = pricelist.create(search_criterias)
            mod = {"success": False}

        for model in pricelist:
            new_dict = model.read(list(set(http.request.env['product.pricelist']._fields)))
            mod['result'] = new_dict
            mod['success'] = True
            # print(new_dict)
        if id_ext:
            found = http.request.env['ir.model.data'].sudo().search_read([('name', '=', id_ext)], limit=1)
            if len(found) == 0:
                http.request.env['ir.model.data'].sudo().create({
                    'name': id_ext,
                    'model': 'product.pricelist',
                    'noupdate': True,
                    'module': '__import__',
                    'res_id': pricelist.id
                })

        pricelist.item_ids.unlink()
        items = []
        for x in price_items:
            apply_id_from_ext_id(x)
            if not 'product_tmpl_id' in x:
                continue
            if "date_end" in x and not x['date_end']:
                del x['date_end']
            items.append((0, 0, x))

        pricelist.item_ids = items
        return mod

    except Exception as e:
        return {"success": False, 'error': str(e)}


def get_active_field_present(modelname):
    return 'active' in http.request.env[modelname]._fields


def apply_update_from_request(kw, search_criterias, modelname, guid=None, trans=None, ids=None):
    apply_id_from_ext_id(search_criterias)
    active_present = get_active_field_present(modelname)
    active_domain = ['|', ('active', '=', True), ('active', '=', False)]
    try:
        if guid:
            ext_id = http.request.env['ir.model.data'].sudo().search([('name', '=', guid)], limit=1)
            if len(ext_id) > 0:
                for line in ext_id:
                    id = line.res_id
                    if http.request.httprequest.method == 'GET':
                        moves = http.request.env[modelname].sudo().search_read([('id', '=', id)], limit=1)
                    else:
                        moves = http.request.env[modelname].sudo().search([('id', '=', id)], limit=1)
            else:
                if http.request.httprequest.method == 'GET':
                    if active_present:
                        active_domain = expression.AND([[('guid', '=', guid)], active_domain])
                        moves = http.request.env[modelname].sudo().search_read(active_domain, limit=1)
                    else:
                        moves = http.request.env[modelname].sudo().search_read([('guid', '=', guid)], limit=1)
                else:
                    if active_present:
                        active_domain = expression.AND([[('guid', '=', guid)], active_domain])
                        moves = http.request.env[modelname].sudo().search(active_domain, limit=1)
                    else:
                        moves = http.request.env[modelname].sudo().search([('guid', '=', guid)], limit=1)
        else:
            moves = http.request.env[modelname].sudo().search_read(kw)
    except Exception as e:
        return {"success": False, 'error': str(e)}

    id_ext = None
    if 'id' in search_criterias:
        id_ext = search_criterias.get('id')
        del search_criterias['id']

    try:
        if http.request.httprequest.method == 'GET':
            return moves
        elif http.request.httprequest.method == 'POST':
            if (len(kw) != 0 or guid) and len(moves) > 0:
                written = moves[0].write(search_criterias)
                mod = {"success": written}
                for model in moves:
                    translate_field(model, trans)
                    try:
                        update_ids(model, ids)
                    except Exception as e:
                        pass
                    new_dict = model.read(list(set(http.request.env[modelname]._fields)))
                    mod['result'] = new_dict
                    # print(new_dict)
                if id_ext:
                    found = http.request.env['ir.model.data'].sudo().search_read([('name', '=', id_ext)], limit=1)
                    if len(found) == 0:
                        http.request.env['ir.model.data'].sudo().create({
                            'name': id_ext,
                            'model': modelname,
                            'noupdate': True,
                            'module': '__import__',
                            'res_id': moves[0].id
                        })
                return mod
            else:
                written = http.request.env[modelname].sudo().create(search_criterias)
                mod = {"success": False}
                for model in written:
                    translate_field(model, trans)
                    try:
                        update_ids(model, ids)
                    except Exception as e:
                        pass
                    new_dict = model.read(list(set(http.request.env[modelname]._fields)))
                    mod['result'] = new_dict
                    mod['success'] = True
                    # print(new_dict)
                if id_ext:
                    found = http.request.env['ir.model.data'].sudo().search_read([('name', '=', id_ext)], limit=1)
                    if len(found) == 0:
                        http.request.env['ir.model.data'].sudo().create({
                            'name': id_ext,
                            'model': modelname,
                            'noupdate': True,
                            'module': '__import__',
                            'res_id': written.id
                        })

                return mod
        elif http.request.httprequest.method == 'PUT':
            mod = {"success": False}
            if (len(moves) > 0) and guid:
                written = moves[0].write(search_criterias)
                for model in moves:
                    translate_field(model, trans)
                    try:
                        update_ids(model, ids)
                    except Exception as e:
                        pass
                    new_dict = model.read(list(set(http.request.env[modelname]._fields)))
                    mod['result'] = new_dict
                    mod['success'] = written
                    # print(new_dict)
                if id_ext:
                    found = http.request.env['ir.model.data'].sudo().search_read([('name', '=', id_ext)], limit=1)
                    if len(found) == 0:
                        http.request.env['ir.model.data'].sudo().create({
                            'name': id_ext,
                            'model': modelname,
                            'noupdate': True,
                            'module': '__import__',
                            'res_id': moves[0].id
                        })
            # else:
            #     written = False
            return mod
        elif http.request.httprequest.method == 'DELETE':
            if (len(moves) > 0) and guid:
                deleted = moves[0].unlink()
            else:
                deleted = False
            return {"success": deleted}
    except Exception as e:
        return {"success": False, 'error': str(e)}


def translate_field(rec, trans):
    for fld in rec._fields:
        field = rec._fields[fld]
        if field.column_type is None:
            continue
        if not (field.column_type[0] == 'jsonb'):
            continue

        if not fld in trans:
            continue
        trans_fiels = trans[fld]
        translations = field._get_stored_translations(rec)
        if isinstance(translations, dict):
            for key in trans_fiels:
                # if key in trans_fiels:
                tr = trans_fiels[key]
                translations[key] = tr
                rec.env.cache.update_raw(
                    rec, field, [translations], dirty=True
                )
                rec.modified([fld])


def parse_data_from_request(kw=None):
    try:
        data = json.loads(http.request.httprequest.data)
        if 'params' not in data:
            data['params'] = data.copy()
    except:
        data = {'params': {}}

    return data['params'] if kw == None else data['params'], get_search_criterias(kw)


def get_search_criterias(kw):
    search_criterias = []
    for key, value in kw.items():
        if key == 'operator':
            search_criterias.insert(0, value)
            continue
        operator = value.get('operator', '=')
        arg = value.get('arg', value)
        new_key = 'date' if key in ['date_begin', 'date_end'] else key
        search_criterias.append((new_key, operator, arg))
    return search_criterias


def get_trans_from_request(kw):
    trans = {}
    keys_for_delete = []
    for key in kw:
        if 'lang' in key:
            arr = key.split('_')
            trans[arr[0]] = kw[key]
            keys_for_delete.append(key)
            # del kw[key]

    for i in keys_for_delete:
        del kw[i]

    return trans


def get_ids_from_request(kw):
    many2many = {}
    keys_for_delete = []

    for key in kw:
        if 'ids' in key:
            rs = get_recordset_from_ext_id(kw[key])
            if rs and not isinstance(rs, str):
                many2many[key] = [(4, rs.id)]
                keys_for_delete.append(key)

    for key in keys_for_delete:
        del kw[key]

    return many2many


def update_ids(rec, ids):
    if isinstance(ids, dict):
        for key, values in ids.items():
            if all(x[1] for x in values):
                rec[key] = values


def apply_moves_from_request(data_for_edit, partner_guid):
    # timezone_str = "Europe/Kiev"
    domain = expression.AND([[('guid', '=', partner_guid)], ['|', ('active', '=', True), ('active', '=', False)]])
    partner_sudo = http.request.env['res.partner'].sudo().search(domain)[:1]
    date_order = fields.Datetime.from_string(data_for_edit['date_order'])
    allow_cancel_done = data_for_edit.get('allow_cancel_done', False)
    # timezone = pytz.timezone(timezone_str)
    # localized_date = timezone.localize(date_order)
    if not partner_sudo:
        return {"success": False, 'error': 'Partner not found'}

    domain = expression.AND(
        [[('partner_id', '=', partner_sudo.id)], ['|', ('active', '=', True), ('active', '=', False)]])
    existing_distributor = http.request.env['distrib.distributors'].search(domain, limit=1)
    if not existing_distributor:
        return {"success": False, 'error': 'Distributor not found'}

    DistribMove = http.request.env['distrib.distributors.move'].sudo().search(
        ['&', ('distrib_id', '=', existing_distributor.id), ('date_order', '=', date_order)])
    if DistribMove:
        for move in DistribMove:
            if move.state == 'draft':
                res = move.write({'state': 'done'})
            elif move.state == 'done' and allow_cancel_done:
                res = move.write({'state': 'cancel'})
                # if res:
                #     move._run_recalculate_job(thread=False)
        return {"success": False, 'error': 'Distributor move already exists'}

    move_in, move_out, move_out_inventory, move_in_inventory = [], [], [], []
    for move in data_for_edit['moves']:
        domain = expression.AND(
            [[('guid', '=', move['product_guid'])], ['|', ('active', '=', True), ('active', '=', False)]])
        product_sudo = http.request.env['product.template'].sudo().search(domain)[:1]
        if not product_sudo:
            continue
        for row in move:
            if 'Channel' in row and move[row] != 0:
                channel_id = get_id_from_ext_id(CHANNEL_MAP[row])
                move_out.append((0, 0, {
                    'product_id': product_sudo.id,
                    'price_unit': move.get('price_unit', 0),
                    'name': product_sudo.display_name,
                    'display_type': 'product',
                    'product_uom_qty': move[row],
                    'channel_id': channel_id,
                }))
        if move['qtt_in'] > 0:
            move_in.append((0, 0, {
                'product_id': product_sudo.id,
                'price_unit': move.get('price_unit', 0),
                'name': product_sudo.display_name,
                'display_type': 'product',
                'product_uom_qty': move['qtt_in'],
            }))
        if move['qtt_inventory'] > 0:
            move_out_inventory.append((0, 0, {
                'product_id': product_sudo.id,
                'price_unit': move.get('price_unit', 0),
                'name': product_sudo.display_name,
                'display_type': 'product',
                'product_uom_qty': move['qtt_inventory'],
            }))
        elif move['qtt_inventory'] < 0:
            move_in_inventory.append((0, 0, {
                'product_id': product_sudo.id,
                'price_unit': move.get('price_unit', 0),
                'name': product_sudo.display_name,
                'display_type': 'product',
                'product_uom_qty': -move['qtt_inventory'],
            }))
    move_values = {
        'distrib_id': existing_distributor.id,
        'date_order': date_order,
    }
    DistribMove = http.request.env['distrib.distributors.move'].sudo()
    if len(move_out) > 0:
        so_val = move_values.copy()
        so_val.update({'operation': 'out', 'channel_id': move_out[0][2]['channel_id']})
        move_sudo = DistribMove.with_user(SUPERUSER_ID).create(so_val)
        move_sudo.move_line = move_out
    if len(move_in) > 0:
        so_val = move_values.copy()
        so_val.update({'operation': 'inc'})
        move_sudo = DistribMove.with_user(SUPERUSER_ID).create(so_val)
        move_sudo.move_line = move_in
    if len(move_out_inventory) > 0:
        so_val = move_values.copy()
        so_val.update({'operation': 'out', 'is_inventory': True})
        move_sudo = DistribMove.with_user(SUPERUSER_ID).create(so_val)
        move_sudo.move_line = move_out_inventory
    if len(move_in_inventory) > 0:
        so_val = move_values.copy()
        so_val.update({'operation': 'inc', 'is_inventory': True})
        move_sudo = DistribMove.with_user(SUPERUSER_ID).create(so_val)
        move_sudo.move_line = move_in_inventory
    return {"success": True}

def apply_expenses_from_request(data_for_edit, partner_guid):
    domain = expression.AND([[('guid', '=', partner_guid)], ['|', ('active', '=', True), ('active', '=', False)]])
    partner_sudo = http.request.env['res.partner'].sudo().search(domain)[:1]
    date_order = fields.Datetime.from_string(data_for_edit['date_order'])
    if not partner_sudo:
        return {"success": False, 'error': 'Partner not found'}

    domain = expression.AND(
        [[('partner_id', '=', partner_sudo.id)], ['|', ('active', '=', True), ('active', '=', False)]])
    existing_distributor = http.request.env['distrib.distributors'].search(domain, limit=1)
    if not existing_distributor:
        return {"success": False, 'error': 'Distributor not found'}

    DistribExpenses = http.request.env['distrib.marketing.expenses'].sudo().search(
        ['&', ('distrib_id', '=', existing_distributor.id), ('date_order', '=', date_order)])
    if DistribExpenses:
        return {"success": False, 'error': 'Distributor move already exists'}

    expenses = []
    for move in data_for_edit['expenses']:
        expense_id = get_id_from_ext_id(move['expense_id'])
        expense = http.request.env['distrib.types.marketings'].browse(expense_id)
        expenses.append((0, 0, {
            'expense_id': expense.id,
            'name': expense.name,
            'expense_total': move['expense_total'],
            'display_type': 'expense',
            'descr': expense.desc,
        }))

    move_values = {
        'distrib_id': existing_distributor.id,
        'date_order': date_order,
    }
    Expense = http.request.env['distrib.marketing.expenses'].sudo()
    if len(expenses) > 0:
        move_sudo = Expense.with_user(SUPERUSER_ID).create(move_values)
        move_sudo.move_line = expenses

    return {"success": True}


def get_inventory_move_values(self, out=False, date=None):
    # self.ensure_one()
    # if fields.Float.is_zero(qty, 0, precision_rounding=0.01):
    #     name = _('Product Quantity Confirmed')
    # else:
    #     name = _('Product Quantity Updated')

    return {
        'name': self.env.context.get('inventory_name'),
        'distrib_id': self.distrib_id.id,
        'state': 'draft',
        'is_inventory': True,
        'operation': 'out' if out else 'inc',
        'date_order': date if date else fields.Datetime.now(),
        # 'move_line': [(0, 0, {
        #     'product_id': product_id.id,
        #     # 'product_uom_id': product_uom_id.id,
        #     'distrib_id': self.distrib_id.id,
        #     'product_uom_qty': qty,
        #     'operation': 'out' if out else 'inc',
        # })]
    }

def apply_inventory_from_request(data_for_edit, partner_guid):
    domain = expression.AND([[('guid', '=', partner_guid)], ['|', ('active', '=', True), ('active', '=', False)]])
    partner_sudo = http.request.env['res.partner'].sudo().search(domain)[:1]
    date_order = fields.Datetime.from_string(data_for_edit['date_order'])
    allow_cancel_done = data_for_edit.get('allow_cancel_done', False)

    if not partner_sudo:
        return {"success": False, 'error': 'Partner not found'}

    domain = expression.AND(
        [[('partner_id', '=', partner_sudo.id)], ['|', ('active', '=', True), ('active', '=', False)]])
    existing_distributor = http.request.env['distrib.distributors'].search(domain, limit=1)
    if not existing_distributor:
        return {"success": False, 'error': 'Distributor not found'}

    DistribMove = http.request.env['distrib.distributors.move'].sudo().search(
        ['&', ('distrib_id', '=', existing_distributor.id), ('date_order', '=', date_order)])
    if DistribMove:
        for move in DistribMove:
            if move.state == 'draft':
                res = move.write({'state': 'done'})
            elif move.state == 'done' and allow_cancel_done:
                res = move.write({'state': 'cancel'})
                # if res:
                #     move._run_recalculate_job(thread=False)
        return {"success": False, 'error': 'Distributor move already exists'}

    QuantHistory = http.request.env['distrib.quant.history'].sudo()
    move_out = []
    move_in = []
    product_ids = []
    for move in data_for_edit['moves']:
        domain = expression.AND(
            [[('guid', '=', move['product_guid'])], ['|', ('active', '=', True), ('active', '=', False)]])
        product_sudo = http.request.env['product.template'].sudo().search(domain)[:1]
        if not product_sudo:
            continue
        move['product_id']  = product_sudo
        product_ids.append(product_sudo.id)
        qtt_on_date = QuantHistory.balance_product_on_date(
            product_sudo, existing_distributor, date_order)
        if move['qtt'] != qtt_on_date:
            qtt = move['qtt'] - qtt_on_date
            if float_compare(qtt, 0, precision_rounding=0.01) > 0:
                # move_vals.append(
                #     self._get_inventory_move_values(product_id=products.product_id, qty=qtt, date=self.date))
                move_in.append((0, 0, {
                    'product_id': product_sudo.id,
                    'name': product_sudo.get_product_multiline_description_sale(),
                    # 'product_uom_id': product_uom_id.id,
                    'distrib_id': existing_distributor.id,
                    'product_uom_qty': qtt,
                    'operation': 'inc',
                }))
            elif float_compare(qtt, 0, precision_rounding=0.01) < 0:
                # move_vals.append(self._get_inventory_move_values(product_id=products.product_id, qty=-qtt, out=True,
                #                                                  date=self.date))
                move_out.append((0, 0, {
                    'product_id': product_sudo.id,
                    'name': product_sudo.get_product_multiline_description_sale(),
                    # 'product_uom_id': product_uom_id.id,
                    'distrib_id': existing_distributor.id,
                    'product_uom_qty': -qtt,
                    'operation': 'out',
                }))
            else:
                return {"success": True}
    moves = http.request.env['distrib.distributors.move']
    if len(move_out) > 0:
        move_vals = get_inventory_move_values(
            out=True, date=date_order)
        res = moves.with_user(SUPERUSER_ID).create(move_vals)
        res.move_line = move_out
        # res.action_done()
    if len(move_in) > 0:
        move_vals = get_inventory_move_values(date=date_order)
        res = moves.with_user(SUPERUSER_ID).create(move_vals)
        res.move_line = move_in
        # res.action_done()
    Quants = http.request.env['distrib.quant'].sudo()
    domain = ['&', ('distrib_id', '=', existing_distributor.id),
              ('product_id', 'not in', product_ids)]
    quants_so = Quants.search(domain)
    move_out = []
    move_in = []
    for quant in quants_so:
        qtt_on_date = QuantHistory.balance_product_on_date(
            quant.product_id, existing_distributor, date_order)
        if float_compare(qtt_on_date, 0, precision_rounding=0.01) > 0:
            move_out.append((0, 0, {
                'product_id': quant.product_id.id,
                'name': quant.product_id.get_product_multiline_description_sale(),
                # 'product_uom_id': product_uom_id.id,
                'distrib_id': existing_distributor.id,
                'product_uom_qty': qtt_on_date,
                'operation': 'out',
            }))
        elif float_compare(qtt_on_date, 0, precision_rounding=0.01) < 0:
            move_in.append((0, 0, {
                'product_id': quant.product_id.id,
                'name': quant.product_id.get_product_multiline_description_sale(),
                # 'product_uom_id': product_uom_id.id,
                'distrib_id': existing_distributor.id,
                'product_uom_qty': -qtt_on_date,
                'operation': 'inc',
            }))
    if len(move_out) > 0:
        move_vals = get_inventory_move_values(
            out=True, date=date_order)
        res = moves.with_user(SUPERUSER_ID).create(move_vals)
        res.move_line = move_out
        # res.action_done()
    if len(move_in) > 0:
        move_vals = get_inventory_move_values(date=date_order)
        res = moves.with_user(SUPERUSER_ID).create(move_vals)
        res.move_line = move_in
        # res.action_done()

        # threaded_calculation = threading.Thread(
    #     target=moves._run_recalculate_job)
    # threaded_calculation.start()
    return {"success": True}