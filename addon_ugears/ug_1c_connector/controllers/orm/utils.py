import json

from odoo import http


def apply_update_from_request(kw, search_criterias, modelname, guid=None, trans=None):
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
                    moves = http.request.env[modelname].sudo().search_read([('guid', '=', guid)], limit=1)
                else:
                    moves = http.request.env[modelname].sudo().search([('guid', '=', guid)], limit=1)
        else:
            moves = http.request.env[modelname].sudo().search_read(kw)
    except Exception:
        raise http.BadRequest("Bad request")

    id_ext = None
    if 'id' in search_criterias:
        id_ext = search_criterias.get('id')
        del search_criterias['id']

    if http.request.httprequest.method == 'GET':
        return moves
    elif http.request.httprequest.method == 'POST':
        if (len(kw) != 0 or guid) and len(moves) > 0:
            written = moves[0].write(search_criterias)
            mod = {"success": written}
            for model in moves:
                translate_field(model, trans)
                new_dict = model.read(list(set(http.request.env[modelname]._fields)))
                mod['result'] = new_dict
                # print(new_dict)
            return mod
        else:
            written = http.request.env[modelname].sudo().create(search_criterias)
            mod = {"success": False}
            for model in written:
                translate_field(model, trans)
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
                new_dict = model.read(list(set(http.request.env[modelname]._fields)))
                mod['result'] = new_dict
                mod['success'] = written
                # print(new_dict)
        # else:
        #     written = False
        return mod
    elif http.request.httprequest.method == 'DELETE':
        if (len(moves) > 0) and guid:
            deleted = moves[0].unlink()
        else:
            deleted = False
        return {"success": deleted}


def translate_field(rec, trans):
    for fld in rec._fields:
        field = rec._fields[fld]
        if field.column_type is None:
            continue
        if not (field.column_type[0] == 'jsonb'):
            continue
        # if field.compute:
        #     continue
        # if not isinstance(rec[fld], str):
        #     continue
        # try:
        #     translations = field._get_stored_translations(rec)
        #     if isinstance(translations, dict):
        #         for key in translations:
        #             pass
        # except:
        #     pass
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
    for key in kw:
        new_key = key
        if key == 'operator':
            search_criterias.insert(0, kw[key])
            continue
        sent = kw[key]
        operator = '='
        arg = kw[key]
        try:
            operator = sent['operator']
        except:
            pass
        try:
            arg = sent['arg']
        except:
            pass
        if key == 'date_begin' or key == 'date_end':
            new_key = 'date'
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
