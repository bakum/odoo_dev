from odoo import models


class IeFilters(models.Model):
    _inherit = "ir.filters"

    def unlink(self):
        return super(IeFilters, self).unlink()