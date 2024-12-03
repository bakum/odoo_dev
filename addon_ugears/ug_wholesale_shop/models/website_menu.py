from odoo import models


class WebsiteMenu(models.Model):
   _inherit = 'website.menu'


   def _compute_visible(self):
       """Compute menu invisible"""
       super()._compute_visible()
       for menu in self:
           if not menu.is_visible:
               return
           if "shop" in menu.url and not self.env.user.user_has_groups(
                   'ug_base_distrib.group_distrib_user'):
               menu.is_visible = False