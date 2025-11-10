from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)

class AiMessage(models.Model):
    _inherit = 'ai.message'

    @api.model_create_multi
    def create(self, vals_list):
        ai_messages = super().create(vals_list)
        
        for msg in ai_messages:
            
           # --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ (V26) ---
            # Мы публикуем, только если:
            # 1. Это ответ ('response')
            # 2. И в нем НЕТ 'func_call' (т.е. это *финальный* ответ)
            # 3. И в нем ЕСТЬ 'content' (чтобы не публиковать пустые)
            
            # if (msg.message_type == 'response' and 
            #     msg.thread_id and
            #     msg.content and 
            #     not msg.func_call): # <-- НОВАЯ ПРОВЕРКА
            if msg.message_type == 'response' and msg.thread_id:
            
            # -----------------------------------
            
                _logger.info(f"AI Livechat (V4): Intercepted AI 'response' for thread {msg.thread_id.id}")
                
                # msg.author_id - это res.partner ассистента, который ответил.
                # Нам нужен res.user, связанный с этим res.partner.
                ai_partner = msg.author_id
                ai_user = ai_partner.user_ids[0] if ai_partner.user_ids else None
                
                if not ai_user:
                    _logger.warning(f"AI Livechat (V4): AI Partner {ai_partner.name} has no 'res.user'. Cannot post.")
                    continue 

                channel = self.env['discuss.channel'].search([
                    ('ai_thread_id', '=', msg.thread_id.id)
                ], limit=1)
                
                if channel:
                    _logger.info(f"AI Livechat (V4): Posting response to channel {channel.id} as user {ai_user.name}")
                    channel_as_ai_user = channel.with_user(ai_user.id)
                    
                    # Используем 'msg.content', как в вашей модели
                    channel_as_ai_user.message_post(
                        body=msg.content,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
                else:
                    _logger.warning(f"AI Livechat (V4): Could not find channel for AI thread {msg.thread_id.id}")
                    
        return ai_messages