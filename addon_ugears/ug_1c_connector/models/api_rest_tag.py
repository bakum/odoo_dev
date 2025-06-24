# -*- coding: utf-8 -*-

from odoo import fields, models


class ApiRestTag(models.Model):
    _name = 'api.rest.tag'
    _description = "Api Rest Tag"

    name = fields.Char(required=True)
    description = fields.Char()
