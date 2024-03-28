import json

from odoo import http


def apply_update_from_request(kw, search_criterias, modelname, guid=None):
    try:
        if guid:
            ext_id = http.request.env['ir.model.data'].sudo().search_read([('name', '=', guid)], limit=1)
            if len(ext_id) > 0:
                for line in ext_id:
                    id = line.res_id
                    moves = http.request.env[modelname].sudo().search_read([('id', '=', id)], limit=1)
            else:
                moves = http.request.env[modelname].sudo().search_read([('guid', '=', guid)], limit=1)
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
            return mod
        else:
            written = http.request.env[modelname].sudo().create(search_criterias)
            if id_ext:
                found = http.request.env['ir.model.data'].sudo().search_read([('name', '=', id_ext)], limit=1)
                if len(found) == 0:
                    http.request.env['ir.model.data'].sudo().create({
                        'name': id_ext,
                        'model': modelname,
                        'module': '__import__',
                        'res_id': written.id
                    })

            return written
    elif http.request.httprequest.method == 'PUT':
        if (len(moves) > 0) and guid:
            written = moves[0].write(search_criterias)
        else:
            written = False
        return {"success": written}
    elif http.request.httprequest.method == 'DELETE':
        if (len(moves) > 0) and guid:
            deleted = moves[0].unlink()
        else:
            deleted = False
        return {"success": deleted}


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
