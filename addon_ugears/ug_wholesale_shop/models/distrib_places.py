from odoo import models, fields, _


class DistribPlaces(models.Model):
    _name = 'distrib.places'
    _description = 'Geographic Places'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name", copy=False)
    places_type = fields.Selection(
        selection=[
            ('warehouse', "Warehouse"),
            ('point_of_load', "Place of taking over the goods"),
            ('custom', "Custom Place"),
        ],
        string="Type of place",
        copy=True, default='warehouse')

    def name_get(self):
        result = []
        for sizes in self:
            if sizes.places_type == 'warehouse':
                name_type = 'Warehouse'
            elif sizes.places_type == 'point_of_load':
                name_type = 'Place of taking over the goods'
            else:
                name_type = 'Custom Place'
            name = '%s  %s' % (name_type, sizes.name)
            result.append((sizes.id, name))
        return result