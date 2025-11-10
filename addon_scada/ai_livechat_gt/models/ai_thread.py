# ai_livechat_gt/models/ai_thread.py
from odoo import models, api, _
import logging
import json # <-- Добавлено
from odoo.tools import html_escape # <-- Добавлено
import re  # <-- ДОБАВЛЕНО

# v-- Убедитесь, что вы импортировали ai_tool --v
try:
    from odoo.addons.ai_base_gt.models.tools import ai_tool
except ImportError:
    _logger = logging.getLogger(__name__)
    _logger.warning("Could not import @ai_tool decorator. AI Tools will not be available.")
    # Создаем "фальшивый" декоратор, чтобы код не падал
    def ai_tool(func=None, *, condition=None):
        if func:
            return func
        return lambda f: f

_logger = logging.getLogger(__name__)

class AiThreadLivechat(models.Model):
    _inherit = 'ai.thread'
    # 
    # --- НАЧАЛО: НОВЫЙ ИНСТРУМЕНТ (ШАГ 1) ---
    #
    
    @ai_tool(condition=lambda thread: thread.assistant_id.has_model_access)
    def _generate_view_action(self, model_name: str, domain: list, name: str, view_mode: str = 'tree,form') -> dict:
        """
        Use this tool when the user asks to 'show', 'open',
        'find', or 'go to' a list of records.

        This tool does NOT search data, but generates a DICTIONARY (dict)
        for opening an Odoo View.

        IMPORTANT: Before using this tool, you MUST first
        use `_get_model_specs` to get the correct field names for constructing the `domain`.

        Your final answer to the user MUST ONLY be the JSON dictionary returned by this tool.

        Args:
        model_name (str): Technical name of the model to open (e.g., 'sale.order', 'account.move').
        domain (list): Odoo domain (list of lists) for filtering records (e.g., [['state', '=', 'posted']]).
        name (str): A descriptive name for this view (e.g., 'Open Accounts').
        view_mode (str): The display mode, defaulting to 'tree,form'.

        Returns:
        dict: A dictionary representing ir.actions.act_window.
        """
        self.ensure_one()
        
        # (Здесь можно добавить проверку безопасности, 
        # что 'model_name' разрешен ассистенту)
        self.ensure_one()
        _logger.info(f"AI Livechat (V54): _generate_view_action called for model {model_name} with domain {domain}")
        
        # --- (V54) КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
        
        view_types = view_mode.split(',')
        views_list = []
        for vt in view_types:
            if vt.strip(): # Убираем пробелы
                views_list.append([False, vt.strip()]) # e.g., [False, 'tree']
        
        # --------------------------------

        # --- (V59) КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
        
        action_context = {}
        
        # Odoo ПОКАЗЫВАЕТ фильтры в поиске через 'search_default_'
        # Мы поддерживаем простые фильтры: ['field', '=', 'value']
        for filter_term in domain:
            if isinstance(filter_term, (list, tuple)) and len(filter_term) == 3:
                field_name, operator, value = filter_term
                
                # Добавляем только простые фильтры ('='), которые 
                # строка поиска может легко отобразить
                if operator == '=':
                     action_context[f'search_default_{field_name}'] = value
        
        # --------------------------------
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model_name,
            'domain': domain,
            # 'view_mode': view_mode, # 'views' заменяет 'view_mode' для JS
            'views': views_list, # <-- Вот исправление
            'target': 'main', # 'main' открывает в главном окне, 'new' - в модальном
            'context': action_context, # <-- Теперь содержит 'search_default_'
        }

    #
    # --- КОНЕЦ: НОВОГО ИНСТРУМЕНТА ---
    #

    #
    # --- НАЧАЛО: НОВЫЙ ИНСТРУМЕНТ (V57) ---
    #
    
    @ai_tool(condition=lambda thread: thread.assistant_id.has_model_access)
    def _generate_group_by_action(self, model_name: str, domain: list, group_by_fields: list[str], name: str, view_mode: str = 'tree,form') -> dict:
        """
        Use this tool when the user asks to 'group', 'sort by', 'categorize', or 'summarize' data.

        This tool generates a DICTIONARY (dict) for opening an Odoo View
        with the grouping already applied.

        IMPORTANT: Before using this tool, you MUST first
        use `_get_model_specs` to get the correct
        field names for `domain` and `group_by_fields`.

        Your final answer to the user MUST
        ONLY be the JSON dictionary returned by this tool.

        Args:
        model_name (str): Technical name of the model (e.g., 'res.partner').
        domain (list): Odoo domain to filter on (e.g., [['customer_rank', '>', 0]]).
        group_by_fields (list[str]): List of fields to group by (e.g., ['country_id', 'state_id']).
        name (str): Descriptive name of the view (e.g., 'Customers by Country').
        view_mode (str): Display mode, defaults to 'tree,form'.

        Returns:
        dict: A dictionary representing ir.actions.act_window.
        """
        self.ensure_one()
        _logger.info(f"AI Livechat (V57): _generate_group_by_action called for model {model_name} with group_by {group_by_fields}")

        # (V56) Преобразуем 'view_mode' в 'views'
        view_types = view_mode.split(',')
        views_list = []
        for vt in view_types:
            if vt.strip():
                views_list.append([False, vt.strip()])

        # --- (V58) КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
        
        # 1. Odoo применяет группировку через 'group_by'
        action_context = {
            'group_by': group_by_fields
        }
        
        # 2. Odoo ПОКАЗЫВАЕТ группировку в поиске через 'search_default_'
        for field in group_by_fields:
            # e.g., 'country_id' -> 'search_default_group_by_country_id': 1
            action_context[f'search_default_group_by_{field}'] = 1
        
        # --------------------------------
        # 2. (V59) Контекст для Фильтров (Domain)
        for filter_term in domain:
            if isinstance(filter_term, (list, tuple)) and len(filter_term) == 3:
                field_name, operator, value = filter_term
                if operator == '=':
                     action_context[f'search_default_{field_name}'] = value
        
        # --------------------------------

        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model_name,
            'domain': domain,
            'views': views_list,
            'context': action_context, # <-- Вот и все!
            'target': 'main', 
        }

    #
    # --- КОНЕЦ: НОВОГО ИНСТРУМЕНТА ---
    #
    """
    (V32) Это НОВЫЙ, чистый способ публикации ответа в чат.
    Мы "цепляемся" к _post_request_hook, который ai_base_gt
    вызывает, когда у него есть ФИНАЛЬНЫЙ ответ.
    """
    def _post_request_hook(self, prompt_message, response_message):
        """
        Этот hook вызывается ПОСЛЕ того, как _send_request 
        (включая все func_call) завершил работу.
        """
        # Сначала вызываем super(), чтобы не сломать 
        # другие модули (если они есть).
        super()._post_request_hook(prompt_message, response_message)

        # 1. Проверяем, что у нас есть финальный ответ
        if (not response_message or 
            not response_message.content or 
            response_message.func_call): # На всякий случай
            return

        # 2. Находим наш канал
        # (self - это 'ai.thread', который мы ищем)
        channel = self.env['discuss.channel'].search([
            ('ai_thread_id', '=', self.id)
        ], limit=1)

        if channel:
            ai_partner = self.ai_partner_id
            ai_user = ai_partner.user_ids[:1] # (используем [:1] вместо [0])
            
            if not ai_user:
                _logger.warning(f"AI Livechat (V32-Hook): AI Partner {ai_partner.name} has no 'res.user'. Cannot post.")
                return

            content = response_message.content.strip()
            body_to_post = content # По умолчанию - обычный текст 
            action_json = None
            # --- НОВАЯ ЛОГИКА (V37) ---
            ai_comment = None # Здесь будет храниться комментарий AI
            match_string = None # Здесь будет строка, которую нужно удалить
            # ------------------------

            try:
                # 1. Ищем ```json ... ```
                match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                
                if match:
                    action_json_str = match.group(1)
                    match_string = match.group(0) # group(0) - это вся найденная строка
                    action_json = json.loads(action_json_str)

                if not match:
                    # 2. Ищем "сырой" JSON-объект
                    match = re.search(r'(\{\s*"type":\s*"ir\.actions\.act_window".*?\})', content, re.DOTALL)
                    if match:
                        action_json_str = match.group(1)
                        match_string = match.group(1) # group(1) - это и есть вся строка
                        action_json = json.loads(action_json_str)

                # (V36 - Проверка)
                if action_json and isinstance(action_json, dict) and action_json.get('type') == 'ir.actions.act_window':
                    
                    # --- НОВАЯ ЛОГИКА (V37) ---
                    if match_string:
                        # Удаляем JSON из контента, чтобы получить "чистый" комментарий AI
                        ai_comment = content.replace(match_string, "").strip()
                    
                    # Если комментария нет (AI вернул ТОЛЬКО JSON)
                    if not ai_comment:
                        ai_comment = "Я подготовил для вас представление. Нажмите, чтобы открыть:"
                    # ------------------------

                    # 2. Публикуем ТОЛЬКО ТЕКСТ в чат
                    body_to_post = ai_comment
                    
                    # 3. Отправляем JSON-действие через Odoo Bus
                    #    (Мы добавим 'notify_ai_action' в Шаге 2)
                    _logger.info(f"AI Livechat (V38-Hook): Sending ACTION via Bus to channel {channel.id}")
                    channel.notify_ai_action(action_json)

                    # action_name = action_json.get('name', 'Нажмите, чтобы открыть')
                    # escaped_action_data = html_escape(json.dumps(action_json))
                    
                    # body_to_post = (
                    #     # --- ИСПОЛЬЗУЕМ КОММЕНТАРИЙ AI ---
                    #     f"<p>{html_escape(ai_comment)}</p>"
                        
                    #     # --- НАША КНОПКА ---
                    #     f"<a href='#' class='btn btn-primary btn-sm o_ai_action_link' "
                    #     f"data-action='{escaped_action_data}'>"
                    #     f"<i class='fa fa-arrow-right'/> {html_escape(action_name)}"
                    #     f"</a>"
                    # )
                    # _logger.info(f"AI Livechat (V37-Hook): Extracted ACTION and COMMENT. Posting link.")
                
                else:
                    _logger.info(f"AI Livechat (V37-Hook): No valid action JSON found. Posting as text.")

            except json.JSONDecodeError:
                _logger.warning(f"AI Livechat (V37-Hook): JSONDecodeError. Posting as raw text.")
                body_to_post = content
                # _logger.info(f"AI Livechat (V32-Hook): Posting final response {response_message.id} to channel {channel.id}")
            
            # 3. Публикуем сообщение в чат
            channel.with_user(ai_user).message_post(
                body=body_to_post,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )