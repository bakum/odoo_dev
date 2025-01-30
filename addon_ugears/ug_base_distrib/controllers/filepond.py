import json
from base64 import b64encode, b64decode

import xlrd

from odoo import http
from odoo.http import request


class Filepond(http.Controller):
    _header = {}
    _header_reverse = {}

    @http.route('/filepond/process', type='http', auth='user', methods=["POST"], csrf=False)
    def filepond_process(self):
        filepond = http.request.params.get("filepond")

        file = b64encode(filepond.read())
        ir_attachment = http.request.env['ir.attachment']
        attachment = ir_attachment.create({
            'name': filepond.filename,
            'datas': file,
        })
        if not attachment:
            return False
        return str(attachment.id)

    @http.route('/filepond/revert', type='http', auth='user', methods=["DELETE"], csrf=False)
    def filepond_revert(self):
        id = json.loads(http.request.httprequest.data)
        ir_attachment = http.request.env['ir.attachment']
        attachment = ir_attachment.search([('id', '=', id)])
        if attachment:
            attachment.unlink()

        return ""

    @http.route('/filepond/import', type='json', methods=["POST"], auth="user")
    def filepond_import(self, file_id=None):
        if file_id:
            ir_attachment = http.request.env['ir.attachment']
            attachment = ir_attachment.search([('id', '=', file_id)])[:1]
            file_binary = b64decode(attachment.datas)
            return self.import_region_rel_from_excel(file_contents=file_binary)

        return {
            'status': 'failed',
            'message': 'No file provided'
        }

    def get_id_from_ext_id(self, ext_id):
        ext = request.env['ir.model.data'].sudo().search([('name', '=', ext_id)], limit=1)
        id = False
        if len(ext) > 0:
            for line in ext:
                id = line.res_id
        return ext_id if not id else id

    def _set_headers(self, headers):
        for counter, row in enumerate(headers):
            self._header[counter] = row
            self._header_reverse[row] = counter

    def _validate_array(self, data):
        new_data = []
        for counter, row in enumerate(data):
            header = self._header[counter]
            if 'description' in header:
                new_data.append(row)
                continue
            if 'id' in header:
                id = self.get_id_from_ext_id(row)
                if id != row:
                    new_data.append(id)
                else:
                    new_data.append('none')
                continue
            try:
                value = str(int(row))
            except ValueError:
                value = str(row)
            value = value.replace(' ', '')
            new_data.append(value)
        return new_data

    def _get_product(self, data):
        data = self._validate_array(data)
        log = {
            'data': data,
            'result': False,
            'description': '',
            'name': '',
        }
        name_idx = self._header_reverse['description']
        barcode_idx = self._header_reverse['barcode']
        default_code_idx = self._header_reverse['default_code']
        barcode = data[barcode_idx]
        default_code = data[default_code_idx]
        name = data[name_idx]
        log['name'] = name

        ProductRec = request.env['product.product']
        regions = []
        if barcode and default_code:
            domain = ['&', ('barcode', '=', barcode), ('default_code', '=', default_code)]
        elif barcode:
            domain = [('barcode', '=', barcode)]
        elif default_code:
            domain = [('default_code', '=', default_code)]
        else:
            log['description'] = 'No Product found'
            return log
        product = ProductRec.search(domain)[:1]
        for counter, row in enumerate(data):
            name_row = self._header[counter]
            if 'region_id' in name_row:
                if row == 'none':
                    continue
                regions.append(row)

        regions_ids = [(6, 0, regions)]
        if product:
            product.region_ids = regions_ids
            log['description'] = 'OK'
            log['result'] = True
            return log
        log['description'] = 'No Product found'
        return log

    def _get_distribution(self, data):
        data = self._validate_array(data)
        log = {
            'data': data,
            'result': False,
            'description': '',
            'name': 'No name found',
        }
        name_idx = self._header_reverse['description']
        id_idx = self._header_reverse['id']
        region_id_idx = self._header_reverse['region_id']
        region_id = data[region_id_idx]
        name = data[name_idx]
        log['name'] = name
        id_par = data[id_idx]
        if id_par == 'none':
            log['description'] = 'No Partner found'
            return log
        if region_id == 'none':
            region_id =  False

        PartnerRec = request.env['res.partner']
        domain = [('id', '=', id_par)]
        partner = PartnerRec.search(domain)[:1]
        if partner:
            if partner.distrib_ids:
                distrib = partner.distrib_ids[0]
                if region_id:
                    distrib.update({'region_id': region_id})
                    log['description'] = 'OK'
                    log['result'] = True
                    return log
                else:
                    log['description'] = 'No Region found'
                    return log
            else:
                log['description'] = 'No Distributor found'
                return log

        return log

    def import_region_rel_from_excel(self, file_contents=None):
        if not file_contents:
            return {
                'status': 'failed',
                'message': 'Please provide a file contents.',
                'log': {}
            }
        try:
            book = xlrd.open_workbook(file_contents=file_contents)
        except xlrd.biffh.XLRDError as e:
            return {'status': 'failed', 'message': repr(e), 'log': []}
        log = {}
        for sheet in book.sheets():
            self._header = {}
            self._header_reverse = {}
            index = 0
            try:
                if sheet.name == 'Products':
                    log['Product'] = []
                    for row in range(sheet.nrows):
                        row_values = sheet.row_values(row)
                        if row == 0:
                            self._set_headers(row_values)
                        elif row >= 1:
                            vals = self._get_product(row_values)
                            vals['id'] = index
                            index += 1
                            log['Product'].append(vals)
                elif sheet.name == 'Partners':
                    log['Partner'] = []
                    for row in range(sheet.nrows):
                        row_values = sheet.row_values(row)
                        if row == 0:
                            self._set_headers(row_values)
                        if row >= 1:
                            vals = self._get_distribution(row_values)
                            vals['id'] = index
                            index += 1
                            log['Partner'].append(vals)
            except IndexError as e:
                return {'status': 'failed', 'message': repr(e), 'log': log}
        if not log:
            return {'status': 'failed', 'message': 'Not supported template.', 'log': log}
        return {'status': 'success', 'message': 'File imported successfully.', 'log': log}
