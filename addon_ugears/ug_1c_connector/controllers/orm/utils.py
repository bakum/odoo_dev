# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import json
from typing import Any

from pydantic.utils import GetterDict

from odoo import fields, models, http


def parse_external_id(data_dict):
    code = None
    for key in data_dict:
        if key == 'id':
            code = data_dict[key]
        ext_id = http.request.env['ir.model.data'].sudo().search([('name', '=', data_dict[key])], limit=1)
        if len(ext_id) > 0:
            data_dict[key] = ext_id[0].res_id

    return data_dict, code


def apply_update_from_request(kw, search_criterias, modelname, guid=None):
    try:
        if guid:
            ext_id = http.request.env['ir.model.data'].sudo().search([('name', '=', guid)], limit=1)
            if len(ext_id) > 0:
                for line in ext_id:
                    id = line.res_id
                    moves = http.request.env[modelname].sudo().search([('id', '=', id)], limit=1)
            else:
                moves = http.request.env[modelname].sudo().search([('guid', '=', guid)], limit=1)
        else:
            moves = http.request.env[modelname].sudo().search(kw)
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
                found = http.request.env['ir.model.data'].sudo().search([('name', '=', id_ext)], limit=1)
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


def batch_update_from(data, modelname):
    res = []
    if type(data) != list:
        return res
    for line in data:
        ln, code = parse_external_id(line)
        moves = dict()

        if 'id' in ln:
            moves = http.request.env[modelname].sudo().search([('id', '=', ln['id'])], limit=1)
            del ln['id']
        if 'guid' in ln:
            if len(moves) == 0:
                moves = http.request.env[modelname].sudo().search([('guid', '=', ln['guid'])], limit=1)

        if moves and len(moves) > 0:
            written = moves[0].write(ln)
            res.append({
                'guid': moves[0].guid,
                'name': moves[0].name,
                'operation': 'update',
                'success': written
            })
        else:
            written = http.request.env[modelname].sudo().create(ln)
            if code:
                found = http.request.env['ir.model.data'].sudo().search([('name', '=', code)], limit=1)
                if len(found) == 0:
                    http.request.env['ir.model.data'].sudo().create({
                        'name': code,
                        'model': modelname,
                        'module': '__import__',
                        'res_id': written.id
                    })
            res.append({
                'guid': written.guid,
                'name': written.name,
                'operation': 'create',
                'success': True
            })
    return res


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


class GenericOdooGetter(GetterDict):
    """A generic GetterDict for Odoo models

    The getter take care of casting one2many and many2many
    field values to python list to allow the from_orm method from
    pydantic class to work on odoo models. This getter is to specify
    into the pydantic config.

    Usage:

     .. code-block:: python

        import pydantic
        from odoo.addons.pydantic import models, utils

        class Group(models.BaseModel):
            name: str

            class Config:
                orm_mode = True
                getter_dict = utils.GenericOdooGetter

        class UserInfo(models.BaseModel):
            name: str
            groups: List[Group] = pydantic.Field(alias="groups_id")

            class Config:
                orm_mode = True
                getter_dict = utils.GenericOdooGetter

        user = self.env.user
        user_info = UserInfo.from_orm(user)

    To avoid having to repeat the specific configuration required for the
    `from_orm` method into each pydantic model, "odoo_orm_mode" can be used
     as parent via the `_inherit` attribute

    """

    def get(self, key: Any, default: Any = None) -> Any:
        res = getattr(self._obj, key, default)
        if isinstance(self._obj, models.BaseModel) and key in self._obj._fields:
            field = self._obj._fields[key]
            if res is False and field.type != "boolean":
                return None
            if field.type == "date" and not res:
                return None
            if field.type == "datetime":
                if not res:
                    return None
                # Get the timestamp converted to the client's timezone.
                # This call also add the tzinfo into the datetime object
                return str(fields.Datetime.context_timestamp(self._obj, res))
            if field.type == "many2one" and not res:
                return None
            if field.type in ["one2many", "many2many"]:
                return list(res)
        return res
