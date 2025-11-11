from odoo import models, api, _, registry
from odoo.tools import html2plaintext
import logging

_logger = logging.getLogger(__name__)

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *,
                     body='', subject=None, message_type='notification',
                     email_from=None, author_id=None, parent_id=False,
                     subtype_xmlid=None, subtype_id=False, partner_ids=None,
                     attachments=None, attachment_ids=None, body_is_html=False,
                     **kwargs):
        
        mail_message = super().message_post(
            body=body, subject=subject, message_type=message_type,
            email_from=email_from, author_id=author_id, parent_id=parent_id,
            subtype_xmlid=subtype_xmlid, subtype_id=subtype_id, partner_ids=partner_ids,
            attachments=attachments, attachment_ids=attachment_ids, body_is_html=body_is_html,
            **kwargs
        )

        if self._name != 'discuss.channel' or message_type != 'comment':
            return mail_message

        for channel in self:
            if (channel.channel_type == 'chat' and len(channel.channel_partner_ids) == 2):
                
                ai_partner = channel.channel_partner_ids.filtered(lambda p: p.is_ai)
                author_partner = mail_message.author_id
                
                if (ai_partner and author_partner.id != ai_partner.id):
                    
                    assistant = ai_partner.ai_assistant_ids[0] 
                    _logger.info(f"AI Livechat (V16-Clean): Queuing AI request for {assistant.name}")

                    # 1. Собираем ID
                    db_name = self.env.cr.dbname
                    user_id = self.env.user.id
                    channel_id = channel.id
                    message_body = mail_message.body
                    assistant_id = assistant.id
                    author_partner_id = author_partner.id
                    
                    # 2. Создаем lambda-функцию для postcommit
                    callback_function = lambda: self.env[self._name]._run_ai_request_postcommit(
                        db_name,
                        user_id,
                        channel_id,
                        message_body,
                        assistant_id,
                        author_partner_id
                    )
                    
                    # 3. Передаем функцию в postcommit
                    self.env.cr.postcommit.add(callback_function)
                
        return mail_message

    @api.model
    def _run_ai_request_postcommit(self, db_name, user_id, channel_id, body, assistant_id, author_partner_id):
        """
        (V16-Clean) Чистая логика: только вызов _send_request, без "замков" V30.
        """
        new_cr = None
        try:
            new_cr = registry(db_name).cursor()
            new_env = api.Environment(new_cr, user_id, {})
            
            channel = new_env['discuss.channel'].browse(channel_id)
            assistant = new_env['ai.assistant'].browse(assistant_id)
            ai_partner_user = assistant.partner_id.user_ids[0] if assistant.partner_id.user_ids else None
            author_partner = new_env['res.partner'].browse(author_partner_id)
            chat_user = author_partner.user_ids[0] if author_partner.user_ids else None
            
            if not chat_user or not ai_partner_user:
                new_cr.close()
                return

            ai_thread = channel.ai_thread_id
            if not ai_thread:
                ai_thread = new_env['ai.thread'].create({
                    'assistant_id': assistant.id,
                    'name': channel.name,
                })
                channel.write({'ai_thread_id': ai_thread.id})

            content = html2plaintext(body)
            # content = body
            if not content:
                new_cr.close()
                return

            try:
                _logger.info(f"AI Livechat (V16-Clean): Calling _send_request for thread {ai_thread.id} as user {chat_user.name}")
                
                # Вызов основного API
                ai_thread.with_user(chat_user)._send_request(prompt=content)
                
                _logger.info(f"AI Livechat (V16-Clean): _send_request completed for thread {ai_thread.id}")

            except Exception as e:
                _logger.error(f"AI Livechat (V16-Clean): Error during _send_request: {e}", exc_info=True)
                
                # Отправка сообщения об ошибке
                channel.with_user(ai_partner_user).message_post(
                    body=_("К сожалению, у меня произошла ошибка: %s", e),
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
        
        except Exception as e:
            _logger.error(f"AI Livechat (V16-Clean - postcommit): Failed to run AI request: {e}", exc_info=True)
        finally:
            if new_cr:
                new_cr.commit()
                new_cr.close()