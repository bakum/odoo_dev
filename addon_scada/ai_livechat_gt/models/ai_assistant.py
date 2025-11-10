from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AiAssistant(models.Model):
    _inherit = 'ai.assistant'

    def action_start_chat(self):
        """
        Вызывается кнопкой 'Начать чат' из списка.
        (V25) Финальное исправление. Используем 'ir.actions.client'
        с тегом 'mail.action_discuss', как подсказал пользователь.
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("Этот асситент (%s) не связан с Контрагентом (Partner) и не может участвовать в чате.", self.name))

        current_user_partner_id = self.env.user.partner_id.id
        ai_partner_id = self.partner_id.id

        # (Логика V20 - она была правильной)
        search_domain = [
            ('channel_type', '=', 'chat'),
            ('channel_partner_ids', 'in', [current_user_partner_id]),
            ('channel_partner_ids', 'in', [ai_partner_id]),
        ]
        channels_found = self.env['discuss.channel'].search(search_domain)

        channel = None
        for ch in channels_found:
            if len(ch.channel_partner_ids) == 2:
                channel = ch
                break 
        
        if not channel:
            _logger.info(f"AI Livechat (V25): No 1-on-1 channel found, creating new one.")
            
            # (Логика V18 - она была правильной)
            partner_commands = [
                (4, current_user_partner_id, 0),
                (4, ai_partner_id, 0)
            ]
            
            channel = self.env['discuss.channel'].create({
                'channel_type': 'chat',
                'name': f"{self.env.user.name}, {self.name}",
                'channel_partner_ids': partner_commands
            })
            
        # --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ (V25) ---
        # Этот код основан на вашем примере из 'rating'
        # Он возвращает 'client action', а не 'window action'.
        
        ctx = self.env.context.copy()
        ctx.update({
            'active_id': channel.id,
            'active_model': 'discuss.channel'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'mail.action_discuss',
            'context': ctx,
            'name': _('Chat with %s', self.name), # Имя для окна
        }