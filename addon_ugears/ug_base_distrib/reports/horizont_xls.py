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
            #row = 0

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
                if line.product_template_id.barcode:
                    sheet.write(line_counter, 0, line.product_template_id.barcode, cell_format)
                else:
                    sheet.write(line_counter, 0, '', cell_format)
                sheet.write(line_counter, 1, line.product_uom_qty, cell_format)
                sheet.write(line_counter, 2, line.price_unit, cell_format)
                line_counter += 1
