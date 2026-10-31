from odoo import models, fields, _
from odoo.exceptions import UserError

from .order_xls import write_product_to_xlsx


class DistribPricelistXlsx(models.AbstractModel):
    _name = 'report.ug_wholesale_shop.export_distrib_pricelist_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, products):
        pricelist = self.env.user.distrib_id.pricelist_id
        if not pricelist:
            raise UserError(_("No pricelist is assigned to your distributor."))

        sheet_obj = write_product_to_xlsx(workbook, products, 'Price list')
        sheet = sheet_obj['sheet']
        head = sheet_obj['head']
        bold_head = sheet_obj['bold_head']
        Products = sheet_obj['products']
        txt = sheet_obj['txt']
        txt1 = sheet_obj['txt1']
        price_format = workbook.add_format({'font_size': 10, 'font_name': 'Arial', 'num_format': '#,##0.00'})

        sheet.write(0, 3, 'Qty in box', head)
        sheet.write(0, 4, 'Price', head)
        sheet.write(0, 5, 'Currency', head)
        sheet.set_column(3, 3, 10)
        sheet.set_column(4, 4, 12)
        sheet.set_column(5, 5, 10)

        sheet.write(0, 7, 'Pricelist', bold_head)
        sheet.write(0, 8, pricelist.name, txt1)
        sheet.write(1, 7, 'Date', bold_head)
        sheet.write(1, 8, fields.Date.to_string(fields.Date.context_today(self)), txt1)
        sheet.set_column(7, 7, 10)
        sheet.set_column(8, 8, 30)

        # Права на правила прайс-листа у дистриб'ютора немає, тому ціни рахуємо через sudo
        prices = pricelist.sudo()._get_products_price(Products, 1.0)
        currency = pricelist.currency_id.name
        for num, product in enumerate(Products):
            sheet.write(num + 1, 3, product.qty_in_cartoon, txt)
            sheet.write(num + 1, 4, prices.get(product.id, 0.0), price_format)
            sheet.write(num + 1, 5, currency, txt)
