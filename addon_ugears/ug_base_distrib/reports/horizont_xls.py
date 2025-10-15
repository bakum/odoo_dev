from odoo import models


class HorizontXlsx(models.AbstractModel):
    _name = 'report.ug_base_distrib.export_horizont_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, orders):
        for obj in orders:
            report_name = obj.name
            # One sheet by partner
            sheet = workbook.add_worksheet('Veidne_ Dokumenta rindas1')

            bold = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10})
            bold_head = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10, 'align': 'center'})
            cell_format = workbook.add_format(
                {'font_name': 'Arial', 'font_size': 10, 'align': 'center'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_name': 'Arial', 'font_size': 10})
            head.set_bg_color('yellow')
            txt = workbook.add_format({'font_size': 10, 'font_name': 'Arial'})
            # sheet.merge_range('A1:C1', 'Veidne: Dokumenta rindas', bold)
            # sheet.set_row(0, 70)
            sheet.set_column('A:C', 15)
            # sheet.set_column('B:B', 20)
            # sheet.set_column('C:C', 20)
            # row = 0

            # sheet.write(0, 0, 'Veidne: Dokumenta rindas', bold)
            # sheet.write(2, 0, 'Obligātie dzeltenie lauki: Kods;Daudzums;', txt)
            # sheet.write(3, 0, 'Obligāti aizpildāmi zaļie lauki: <nav>', txt)
            # sheet.write(4, 0, 'Pārējos laukus var dzēst; Var lietot papildus informatīvos laukus;', txt)
            # sheet.write(5, 0, 'Dimensiju lauku nosaukumus veido "Dim-<Dimensijas nosaukums>"', txt)

            # sheet.write(8, 0, 'Kods', head)
            # sheet.write(8, 1, 'Daudzums', head)
            # sheet.write(8, 2, 'Cena', bold_head)
            sheet.write(0, 0, 'Kods', head)
            sheet.write(0, 1, 'Daudzums', head)
            sheet.write(0, 2, 'Cena', bold_head)
            line_counter = 1
            for line in obj.order_line:
                if line.display_type in ('line_section', 'line_note'):
                    continue
                if line.product_template_id.barcode:
                    sheet.write(line_counter, 0, line.product_template_id.barcode, cell_format)
                else:
                    sheet.write(line_counter, 0, '', cell_format)
                sheet.write(line_counter, 1, line.product_uom_qty, cell_format)
                if line.discount > 0:
                    sheet.write(line_counter, 2, round(line.price_total/line.product_uom_qty, 3), cell_format)
                else:
                    sheet.write(line_counter, 2, line.price_unit, cell_format)
                line_counter += 1


class OrderToXlsx(models.AbstractModel):
    _name = 'report.ug_base_distrib.export_order_to_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, orders):
        for obj in orders:
            report_name = obj.name
            sheet = workbook.add_worksheet(report_name)
            bold = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10})
            bold_head = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10})
            cell_format = workbook.add_format(
                {'font_name': 'Arial', 'font_size': 10, 'align': 'center'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_name': 'Arial', 'font_size': 10})
            head.set_bg_color('silver')
            bold_head.set_bg_color('silver')
            txt = workbook.add_format({'font_size': 10, 'font_name': 'Arial'})

            price_title = 'Price per 1 pcs, %s' % (obj.currency_id.name)
            price_total_title = 'Total, %s excl. VAT' % (obj.currency_id.name)
            all_qtt = 0
            all_boxes = 0
            sheet.set_column('A:K', 20)
            # sheet.set_column('A:A', 10)
            # sheet.set_column('F:G', 10)

            sheet.write(0, 0, 'Order Confirmation #', bold)
            sheet.write(0, 1, report_name, bold)

            sheet.write(2, 0, 'The Supplier:', bold)
            sheet.write(2, 1, obj.company_id.partner_id.name, txt)

            sheet.write(4, 0, 'The Buyer:', bold)
            sheet.write(4, 1, obj.partner_id.name, txt)

            sheet.write(6, 0, 'Dated:', bold)
            sheet.write(6, 1, obj.date_order.strftime('%Y-%m-%d'), txt)
            sheet.write(7, 0, 'Currency:', bold)
            sheet.write(7, 1, obj.currency_id.name, txt)

            sheet.write(9, 0, '#', head)
            sheet.write(9, 1, 'Customs tariff number', head)
            sheet.write(9, 2, 'Country of origin', head)
            sheet.write(9, 3, 'Barcode', head)
            sheet.write(9, 4, 'Description', head)
            sheet.write(9, 5, 'Q-ty', head)
            sheet.write(9, 6, 'Unit', head)
            sheet.write(9, 7, 'Pieces of boxes in box', head)
            sheet.write(9, 8, 'Number of boxes', head)
            sheet.write(9, 9, price_title, head)
            sheet.write(9, 10, price_total_title, head)
            row_n = 0
            for count, line in enumerate(obj.order_line):
                if line.display_type in ('line_section', 'line_note'):
                    continue
                row_n = 9 + count + 1
                sheet.write(row_n, 0, count + 1, txt)
                sheet.write(row_n, 1, '' if not line.product_id.customscode else line.product_id.customscode, txt)
                field = obj.company_id.country_id._fields
                translations = field['name']._get_stored_translations(obj.company_id.country_id)
                if translations and 'en_US' in translations:
                    sheet.write(row_n, 2, translations['en_US'], txt)
                else:
                    sheet.write(row_n, 2, '' if not obj.company_id.country_id.display_name else obj.company_id.country_id.display_name, txt)
                sheet.write(row_n, 3, '' if not line.product_id.barcode else line.product_id.barcode, txt)
                field = line.product_id.product_tmpl_id._fields
                translations = field['name']._get_stored_translations(line.product_id.product_tmpl_id)
                if translations and 'en_US' in translations:
                    sheet.write(row_n, 4, translations['en_US'], txt)
                else:
                    sheet.write(row_n, 4, line.product_id.display_name, txt)
                sheet.write(row_n, 5, line.product_uom_qty, txt)
                all_qtt += line.product_uom_qty
                sheet.write(row_n, 6, 'pcs', txt)
                sheet.write(row_n, 7, line.product_id.qty_in_cartoon, txt)
                boxes = 0 if line.product_id.qty_in_cartoon == 0 else line.product_uom_qty//line.product_id.qty_in_cartoon
                all_boxes += boxes
                sheet.write(row_n, 8, boxes, txt)
                if line.discount > 0:
                    sheet.write(row_n, 9, round(line.price_total/line.product_uom_qty, 3), txt)
                else:
                    sheet.write(row_n, 9, line.price_unit, txt)
                sheet.write(row_n, 10, line.price_total, txt)

            row_n += 1
            sheet.write(row_n, 4, 'Total Invoice', bold_head)
            sheet.write(row_n, 5, all_qtt, bold_head)
            sheet.write(row_n, 8, all_boxes, bold_head)
            sheet.write(row_n, 10, obj.amount_total, bold_head)

            if obj.discount_total > 0:
                row_n += 1
                sheet.write(row_n, 8, 'Discount', bold)
                sheet.write(row_n, 10, obj.discount_total, bold)
                row_n += 1
                sheet.write(row_n, 8, 'Subtotal without discount', bold)
                sheet.write(row_n, 10, obj.price_total_no_discount, bold)

            row_n += 2
            sheet.write(row_n, 4, 'Gross / Net weight of Shipment (kg):', bold)
            sheet.write(row_n, 5, '%s/%s' % (round(obj.brutto_total/1000,2),round(obj.netto_total/1000,2)), bold)
            row_n += 2
            sheet.write(row_n, 4, 'Net weight of Shipment (kg):', bold)
            sheet.write(row_n, 5, round(obj.netto_total/1000,2), bold)

            # row_n += 2
            # sheet.write(row_n, 4, 'Number of pallets:', bold)
            # sheet.write(row_n, 5, len(palettes_list['palettes']) if palettes_list and palettes_list['palettes'] else '', bold)

