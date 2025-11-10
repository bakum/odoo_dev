from odoo import models, fields

import logging

_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel' # <-- ИСПРАВЛЕНО

    ai_thread_id = fields.Many2one(
        'ai.thread', 
        string="AI Thread",
        help="Связанная ветка диалога из модуля AI Base.",
        ondelete='set null',
        copy=False
    )

    def notify_ai_action(self, action_data):
        """
        (V55) ИСПРАВЛЕНО: 'reading 'map' of undefined'
        
        Мы НЕ ДОЛЖНЫ добавлять 'channel_id' в 'action_data'.
        Вместо этого мы создаем "чистый" payload, который 
        *содержит* action_data.
        
        Payload будет: { 'action': {...}, 'channel_id': 123 }
        """
        self.ensure_one()
        
        # 1. Тип (Аргумент 2: notification_type)
        notification_type = 'ai_action'
        
        # --- (V55) КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
        # 2. Сообщение (Аргумент 3: message)
        notification_payload = {
            'action': action_data,  # "Чистый" action
            'channel_id': self.id   # Метаданные (на том же уровне)
        }
        # -----------------------------------
        
        # 3. Партнеры (Аргумент 1: channel)
        partners_to = self.channel_partner_ids
        
        if not partners_to:
            _logger.warning("AI Livechat (V55): AI Action - No partners found in channel %s to notify.", self.id)
            return

        _logger.info(f"AI Livechat (V55): Sending 'ai_action' payload to {len(partners_to)} partners via bus.bus._sendone")

        bus_service = self.env['bus.bus']
        
        for partner in partners_to:
            # (V45 - Код без изменений)
            bus_service._sendone(
                partner,
                notification_type,
                notification_payload
            )