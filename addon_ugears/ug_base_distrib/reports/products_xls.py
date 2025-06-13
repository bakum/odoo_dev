from odoo import models


class ProductsOutXlsx(models.AbstractModel):
    _name = 'report.ug_base_distrib.export_products_out_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, products):
        Rules = self.env['distrib.template.rules'].search([])[:1]
        Channels = self.env['distrib.sales.channels'].search([])

        domain = [('sale_ok', '=', True), ('detailed_type', '!=', 'service'), ('is_published', '=', True)]
        if Rules:
            excluded_categories = Rules.get_excluded_categories()
            if excluded_categories:
                domain += [('categ_id', 'not in', excluded_categories)]

        Products = products.search(domain)
        sheet = workbook.add_worksheet('Distr Sales')

        bold_head = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_name': 'Arial', 'font_size': 10})
        head.set_bg_color('silver')
        bold_head.set_bg_color('silver')
        txt = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'align': 'center'})
        txt1 = workbook.add_format({'font_size': 10, 'font_name': 'Arial'})

        sheet.write(0, 0, 'Barcode', head)
        sheet.write(0, 1, 'Art', head)
        sheet.write(0, 2, 'Description', head)
        for count, channel in enumerate(Channels):
            sheet.write(0, 3 + count, channel.name, head)
            width = len(channel.name) + 5
            sheet.set_column(3 + count, 3 + count, width)
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 65)

        for num, product in enumerate(Products):
            if product.barcode:
                sheet.write(num + 1, 0, product.barcode, txt)
            if product.default_code:
                sheet.write(num + 1, 1, product.default_code, txt)

            field = product._fields
            translations = field['name']._get_stored_translations(product)
            if translations and 'en_US' in translations:
                sheet.write(num + 1, 2, translations['en_US'], txt1)
            else:
                sheet.write(num + 1, 2, product.display_name, txt1)
            for count, channel in enumerate(Channels):
                sheet.write(num + 1, 3 + count, 0, txt1)


class ProductsInXlsx(models.AbstractModel):
    _name = 'report.ug_base_distrib.export_products_in_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, products):
        Rules = self.env['distrib.template.rules'].search([])[:1]
        domain = [('sale_ok', '=', True), ('detailed_type', '!=', 'service'), ('is_published', '=', True)]
        if Rules:
            excluded_categories = Rules.get_excluded_categories()
            if excluded_categories:
                domain += [('categ_id', 'not in', excluded_categories)]

        Products = products.with_context(lang='en_US').search(domain)
        sheet = workbook.add_worksheet('Distr Incomes')

        bold_head = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_name': 'Arial', 'font_size': 10})
        head.set_bg_color('silver')
        bold_head.set_bg_color('silver')
        txt = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'align': 'center'})
        txt1 = workbook.add_format({'font_size': 10, 'font_name': 'Arial'})

        sheet.write(0, 0, 'Barcode', head)
        sheet.write(0, 1, 'Art', head)
        sheet.write(0, 2, 'Description', head)
        sheet.write(0, 3, 'Qtt', head)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 65)
        sheet.set_column(3, 3, 5)

        for num, product in enumerate(Products):
            if product.barcode:
                sheet.write(num + 1, 0, product.barcode, txt)
            if product.default_code:
                sheet.write(num + 1, 1, product.default_code, txt)

            field = product._fields
            translations = field['name']._get_stored_translations(product)
            if translations and 'en_US' in translations:
                sheet.write(num + 1, 2, translations['en_US'], txt1)
            else:
                sheet.write(num + 1, 2, product.display_name, txt1)
            sheet.write(num + 1, 3, 0, txt1)
