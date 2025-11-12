import json
import textwrap
import re
from typing import Any

import odoo.release
from odoo import api, models, fields, _
from odoo.osv import expression
from odoo.tools import json_default, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError

from odoo.addons.iap.tools import iap_tools
from odoo.addons.web_editor.controllers.main import DEFAULT_OLG_ENDPOINT

from .tools import ai_spec, ai_tool


MESSAGE_TYPE_ROLE_MAP = {
    'system': 'system',
    'prompt': 'user',
    'response': 'assistant',
}


class AIThread(models.Model):
    _name = 'ai.thread'
    _description = 'AI Conversation Thread'
    _order = 'id desc'

    name = fields.Char(string="Thread Name", required=True)
    assistant_id = fields.Many2one('ai.assistant', string="Assistant", required=True, index=True)
    config_id = fields.Many2one('ai.config', string="Configuration", related='assistant_id.config_id')
    ai_user_id = fields.Many2one('res.users', string="AI User", related='assistant_id.user_id')
    ai_partner_id = fields.Many2one('res.partner', string="AI Partner", related='assistant_id.partner_id')
    context_id = fields.Many2one('ai.context', string="Thread Context", compute='_compute_context_id',
                                 precompute=True, store=True, readonly=False)
    prompt_template_id = fields.Many2one('ai.prompt.template', string="Prompt Template")
    prompt = fields.Text(string="Prompt")
    message_ids = fields.One2many('ai.message', 'thread_id', string="Messages")
    res_model = fields.Char(string='Res Model', index='btree_not_null', readonly=True)
    res_id = fields.Integer(string='Res ID', index='btree_not_null', readonly=True)

    @api.depends('assistant_id')
    def _compute_context_id(self):
        for r in self:
            r.context_id = r.assistant_id.context_id

    def _get_tools(self):
        self.ensure_one()
        result = []
        for method_name in dir(self):
            method = getattr(self, method_name, None)
            if callable(method) and getattr(method, 'ai_tool', False):
                condition = getattr(method, 'ai_condition', None)
                if condition is None or condition(self):
                    result.append(method)
        return result

    def _get_tools_spec(self):
        self.ensure_one()
        result = []
        for method in self._get_tools():
            result.append(ai_spec(method))
        return result

    def _get_thread_context(self):
        self.ensure_one()
        config = self.config_id.sudo()
        contexts = []

        contexts.append((
            "You are an AI assistant integrated in an Odoo system. Information of the system:\n"
            "- Odoo version: %s\n"
            "- Company name: %s\n"
            "- Company ID: %s\n"
            "- Current time: %s (UTC)\n"
        ) % (
            odoo.release.version,
            self.env.company.name,
            self.env.company.id,
            fields.Datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        )

        contexts.append((
            "Information of the user you are assisting:\n"
            "- User ID: %s\n"
            "- Partner ID: %s\n"
            "- User type: %s\n"
            "- Name: %s\n"
            "- Email: %s\n"
            "- Phone: %s\n"
            "- Company: %s\n"
            "- Timezone: %s\n"
        ) % (
            self.env.uid,
            self.env.user.partner_id.id,
            self.env.user._get_type(),
            self.env.user.name,
            self.env.user.email or '',
            self.env.user.phone or '',
            self.env.user.partner_id.parent_name or '',
            self.env.user.tz or 'UTC',
        ))

        if self.res_model and self.res_id:
            rec = self.env[self.res_model].browse(self.res_id)
            contexts.append((
                "Information of the thread/record you are discussing:\n"
                "- Display Name: %s\n"
                "- Model: %s\n"
                "- ID: %s\n"
            ) % (rec.display_name, rec._name, rec.id))

        if self.context_id:
            contexts.append("Your role: " + self.context_id.context.strip())

        if tools_spec := self._get_tools_spec():
            contexts.append((
                "When you don't know something or are unsure, use tool calling to get information from the system.\n"
                "You can make multiple tool calls consecutively if needed to gather the information you need. "
                "In that case, make a plan for the tool calls to be made, but describe the plan in a way that "
                "is easy to understand for the non-technical users.\n"
                "If the system does not provide the information you need, first review your plan and the tool calls "
                "you have made to check for any issues. Then, if necessary, create a new plan or make additional "
                "tool calls.\n"
                "If you still don't have enough information to answer, be honest and say 'I don't know'.\n"
                "If the user's request is unclear, ask them to clarify."))

            if config.type == 'odooai':
                contexts.append((
                    "Here is the specification of the available tools to call in OpenAPI format:\n"
                    "```\n"
                    "%s\n"
                    "```\n"
                    "To make a tool calling, include in the response a json string as the sample below: \n"
                    "```\n"
                    "{\n"
                    "    \"tool_call\": {\n"
                    "        \"name\": \"tool_name\",\n"
                    "        \"kwargs\": {\n"
                    "            \"arg1\": \"value1\",\n"
                    "            \"arg2\": \"value2\"\n"
                    "        }\n"
                    "    }\n"
                    "}\n"
                    "```"
                    ) % json.dumps(tools_spec, ensure_ascii=False, indent=2))

            if data_sources_info := self.assistant_id._get_accessible_data_sources_info():
                contexts.append((
                    "Here is the list of data sources that you can retrieve data from by "
                    "using the `_semantic_search` tool:\n"
                    "```\n"
                    "%s\n"
                    "```"
                ) % json.dumps(data_sources_info, ensure_ascii=False, indent=2))

            if models_info := self.assistant_id._get_accessible_models_info():
                contexts.append((
                    "Here is the list of models that you can retrieve data from by using "
                    "the `_model_search`, `_model_read` or `_model_read_group` tools:\n"
                    "```\n"
                    "%s\n"
                    "```\n"
                    "If you are not sure about any model you plan to work with, use the "
                    "`_get_model_specs` tool to retrieve the specifications of that model, "
                    "unless the model specifications have already been retrieved earlier "
                    "in the current conversation."
                ) % json.dumps(models_info, ensure_ascii=False, indent=2))

        contexts.append(
            "Always try to determine the language of the user's prompt and respond in the same language.\n"
            "Always present your text response in standard Markdown format."
        )

        return "\n\n".join(contexts)

    def action_send_request(self):
        if not self.prompt:
            raise UserError(_("Please enter a prompt."))
        res = self._send_request(self.prompt, template_id=self.prompt_template_id.id)
        self.prompt = False
        return res

    def _send_request(self, prompt, prompt_message_id=None, template_id=None, **kwargs):
        """
        Send a request to the AI and return the response content.
        :param str prompt: User prompt
        :param int template_id: ID of the prompt template to use
        :return: tuple of prompt message and response message
        """
        self.ensure_one()
        config = self.config_id.sudo()

        if not prompt_message_id:
            prompt_message = self._create_prompt_message(prompt, template_id, **kwargs)
        else:
            prompt_message = self.env['ai.message'].sudo().browse(prompt_message_id)

        if not self.env.su:
            prompt_message = prompt_message.sudo(False)

        response = getattr(self, f'_do_request_{config.type}')(prompt_message)
        func_call = getattr(self, f'_parse_response_tool_{config.type}')(response)
        text = getattr(self, f'_parse_response_text_{config.type}')(response)
        response_message = self.env['ai.message'].create({
            'thread_id': self.id,
            'message_type': 'response',
            'content': text and text.strip() or "",
            'func_call': json.dumps(func_call, ensure_ascii=False, indent=2) if func_call else False,
            'author_id': self.ai_partner_id.id,
        })

        while func_call:
            func_res = getattr(self, f'_execute_tool_{config.type}')(func_call)
            result_message = self._create_tool_result(prompt, func_call, func_res)
            response = getattr(self, f'_do_request_{config.type}')(result_message)
            func_call = getattr(self, f'_parse_response_tool_{config.type}')(response)
            text = getattr(self, f'_parse_response_text_{config.type}')(response)
            response_message = self.env['ai.message'].create({
                'thread_id': self.id,
                'message_type': 'response',
                'content': text and text.strip() or "",
                'func_call': json.dumps(func_call, ensure_ascii=False, indent=2) if func_call else False,
                'author_id': self.ai_partner_id.id,
            })

        self._post_request_hook(prompt_message, response_message)
        return prompt_message, response_message

    def _get_attachments_to_request(self, kwargs):
        self.ensure_one()
        return kwargs.get('attachments', False)

    def _create_prompt_message(self, prompt, template_id=None, **kwargs):
        self.ensure_one()
        config = self.config_id.sudo()
        if template_id:
            prompt = self.env['ai.prompt.template'].browse(template_id).generate_prompt(
                prompt,
                **kwargs.pop('template_kwargs', {})
            )

        attachments = config.allow_files and self._get_attachments_to_request(kwargs)
        return self.env['ai.message'].sudo().create({
            'thread_id': self.id,
            'message_type': 'prompt',
            'content': prompt.strip(),
            'author_id': self.env.user.partner_id.id,
            'attachment_ids': attachments and [(6, 0, attachments.ids)] or False
        })

    def _do_request_odooai(self, message):
        self.ensure_one()
        message_history = self._prepare_message_history_odooai(self.message_ids - message)
        if thread_context := self._get_thread_context():
            message_history.insert(0, {'role': 'system', 'content': thread_context})

        try:
            IrConfigParameter = self.env['ir.config_parameter'].sudo()
            olg_api_endpoint = IrConfigParameter.get_param('web_editor.olg_api_endpoint', DEFAULT_OLG_ENDPOINT)
            database_id = IrConfigParameter.get_param('database.uuid')
            response = iap_tools.iap_jsonrpc(olg_api_endpoint + "/api/olg/1/chat", params={
                'prompt': message.content,
                'conversation_history': message_history or [],
                'database_id': database_id,
            }, timeout=30)
            if response['status'] == 'success':
                return response['content']
            elif response['status'] == 'error_prompt_too_long':
                raise UserError(_("Sorry, your prompt is too long. Try to say it in fewer words."))
            elif response['status'] == 'limit_call_reached':
                raise UserError(
                    _("You have reached the maximum number of requests for this service. Try again later."))
            else:
                raise UserError(_("Sorry, we could not generate a response. Please try again later."))
        except AccessError:
            raise AccessError(_("Oops, it looks like our AI is unreachable!"))

    def _prepare_message_history_odooai(self, messages):
        self.ensure_one()
        message_history = [
            {'role': MESSAGE_TYPE_ROLE_MAP[msg.message_type], 'content': msg.content_full}
            for msg in messages
        ]
        return message_history

    def _parse_response_tool_odooai(self, response):
        self.ensure_one()
        match = re.search(r'\{\s*"tool_call":\s*{.*}\s*}', response, re.DOTALL)
        if match:
            try:
                func_call = json.loads(match.group(0))
                return func_call.get('tool_call')
            except json.JSONDecodeError:
                return False
        return False

    def _execute_tool_odooai(self, func_call):
        return self._run_tool(func_call['name'], **func_call['kwargs'])

    def _run_tool(self, tool_name, **kwargs):
        self.ensure_one()
        try:
            if method := getattr(self, tool_name):
                if not getattr(method, 'ai_tool', False):
                    raise AccessError(_("Tool %s does not exist.") % tool_name)
            return getattr(self, tool_name)(**kwargs)
        except Exception as e:
            return {'error': str(e)}

    def _create_tool_result(self, prompt, func_call, func_res):
        self.ensure_one()
        config = self.config_id.sudo()
        vals = {
            'thread_id': self.id,
            'message_type': 'system',
            'func_call': json.dumps(func_call, ensure_ascii=False, indent=2, default=json_default),
            'func_result': json.dumps(func_res, ensure_ascii=False, indent=2, default=json_default),
            'author_id': self.env.ref('base.partner_root').id,
        }
        if config.type == 'odooai':
            vals['content'] = (
                "Here is the result of your tool call:\n"
                "```\n"
                "%s\n"
                "```\n\n"
                "From that result, make a response for the previous user's prompt, "
                "or make another tool call to get further information. The previous "
                "user's prompt is:\n"
                "%s"
            ) % (
                json.dumps(func_res, ensure_ascii=False, indent=2, default=json_default),
                textwrap.indent(prompt.strip(), '> ')
            )
        return self.env['ai.message'].create(vals)

    def _parse_response_text_odooai(self, response):
        self.ensure_one()
        # Remove JSON function call from response text (with or without markdown code blocks)
        clean_response = re.sub(r'```\w*\s*\{\s*"tool_call":\s*{.*}\s*\}\s*```|\{\s*"tool_call":\s*{.*}\s*\}', '', response, flags=re.DOTALL)
        return clean_response.strip()

    def _post_request_hook(self, prompt_message, response_message):
        """
        Hook that is called after the request is processed.
        """
        pass

    @ai_tool(condition=lambda thread: thread.assistant_id.has_vector_access)
    def _semantic_search(self, query: str, top_k: int = 5, data_source_ids: list[int] = []) -> list[dict]:
        """
        Search all data sources associated with the assistant for items semantically similar to the given query.
        Can only be used with the data sources that have indexed data.

        When to use this tool:
        - When searching for content based on meaning, context, or semantic similarity
        - When looking for documents, text, or unstructured data related to a concept
        - When you need to find information that might be described in different words but has similar meaning
        - When doing research or knowledge discovery across text-based content
        - When the user asks questions like "find information about...", "what do you know about...", "search for content related to..."

        Do NOT use this tool for:
        - Structured data queries with specific filters or conditions
        - Exact record lookups by ID or specific field values
        - Statistical analysis or aggregated data retrieval

        Args:
            query (str): The query string to search for. Should be concise and to the point.
            top_k (int): The number of top similar results to return, defaults to 5. Should be between 1 and 10.
            data_source_ids (list[int]): The IDs of the specific data sources to filter results. If empty, all data sources will be queried.

        Returns:
            list[dict]: A list of dictionaries containing the search results, sorted by similarity.
        """

        self.ensure_one()
        data_sources = self.assistant_id.accessible_data_source_ids
        if data_source_ids:
            data_sources = data_sources.filtered(lambda ds: ds.id in data_source_ids)
        if not data_sources:
            return []

        return self.env['ai.data.item']._search_similar(
            query=query,
            data_sources=data_sources,
            limit=top_k
        )

    @ai_tool(condition=lambda thread: thread.assistant_id.has_model_access)
    def _get_model_specs(self, models: list[str]) -> list[dict]:
        """
        Get the specification of the models. The specification includes the model technical name,
        description, accessible fields details and access domain.

        Args:
            models (list[str]): The list of model technical names to get the specification for.

        Returns:
            list[dict]: A list of dictionaries containing the specification for each model.
        """
        self.ensure_one()
        result = []
        is_superuser = self.assistant_id.is_superuser
        for model in models:
            if model not in self.env.registry:
                continue
            Model = self.env[model]
            if is_superuser:
                result.append({
                    'model': model,
                    'name': Model._description,
                    'fields': Model.fields_get(),
                    'domain': [],
                })
            else:
                data_sources = self.assistant_id.data_source_ids.filtered(
                    lambda ds: ds.type == 'model' and ds.model == model
                )
                if not data_sources:
                    continue
                access_fields = set()
                domains = []
                for ds in data_sources:
                    access_fields.update(ds._get_access_fields())
                    domains.append(ds._get_model_domain())
                domain = expression.OR(domains)
                result.append({
                    'model': model,
                    'name': Model._description,
                    'fields': access_fields and Model.fields_get(list(access_fields)) or {},
                    'domain': domain,
                })
        return result

    @ai_tool(condition=lambda thread: thread.assistant_id.has_model_access)
    def _model_search(self, model_name: str, domain: list[Any], fields: list[str], offset: int = 0, limit: int = 10, order: str = '') -> dict:
        """
        Similar to Odoo's `search_read` method, but with access restricted to the models and fields
        defined in data sources of type 'model'.

        When to use this tool:
        - When you need to query structured data from Odoo models with specific criteria
        - When looking for records that match exact conditions or filters
        - When you need to retrieve specific fields from database records
        - When doing data analysis, reporting, or statistical queries
        - When the user asks for specific records, lists, or data with conditions like "show me all...", "find records where...", "get data from..."
        - When you need to sort, limit, or paginate results from structured data

        Do NOT use this tool for:
        - Content-based or semantic searches across unstructured text
        - When you're looking for information based on meaning rather than exact field matches
        - When searching for general knowledge or concepts

        Args:
            model_name (str): The technical name of the Odoo model to search in.
            domain (list): The search domain to filter records. The data type of the value element must be the same as the field type.
            fields (list): The list of field names to return in the results. If empty, all fields will be returned.
            offset (int): The number of records to skip, defaults to 0.
            limit (int): The maximum number of records to return, defaults to 10.
            order (str): The field to sort results by, must be a stored field. Defaults to empty string.

        Returns:
            dict:
                - total_records (int): The total number of records matching the domain.
                - limit (int): The limit value provided.
                - offset (int): The offset value provided.
                - order (str): The order of the records.
                - records (list): A list of dictionaries containing the requested fields for each matching record.
        """
        self.ensure_one()
        allowed_fields = self.assistant_id._check_model_fields_access(model_name, fields)
        if not fields:
            fields = self.env[model_name].check_field_access_rights('read', allowed_fields)
        domain = expression.AND([self.assistant_id._get_model_domain_access(model_name), domain])
        return {
            'total_records': self.env[model_name].search_count(domain),
            'limit': limit,
            'offset': offset,
            'order': order or self.env[model_name]._order,
            'records': self.env[model_name].search_read(domain, fields, offset, limit, order)
        }

    @ai_tool(condition=lambda thread: thread.assistant_id.has_model_access)
    def _model_read(self, model_name: str, res_ids: list[int], fields: list[str]) -> list[dict]:
        """
        Similar to Odoo's `read` method, but with access restricted to the models and fields
        defined in data sources of type 'model'.

        Args:
            model_name (str): The technical name of the Odoo model to read from.
            res_ids (list): The list of record IDs to read.
            fields (list): The list of field names to return in the result. If empty, all allowed fields will be returned.

        Returns:
            list[dict]: A list of dictionaries, each containing the requested fields for a record.
        """
        self.ensure_one()
        if not res_ids:
            return []
        allowed_fields = self.assistant_id._check_model_fields_access(model_name, fields)
        if not fields:
            fields = self.env[model_name].check_field_access_rights('read', allowed_fields)
        domain = expression.AND([self.assistant_id._get_model_domain_access(model_name), [('id', 'in', res_ids)]])
        recs = self.env[model_name].search(domain)
        missing_ids = set(res_ids) - set(recs.ids)
        if missing_ids:
            raise UserError(_("Records with ids %s in model %s do not exist or cannot be accessed.") % (', '.join(map(str, missing_ids)), model_name))
        return recs.read(fields)

    @ai_tool(condition=lambda thread: thread.assistant_id.has_model_access)
    def _model_read_group(self, model_name: str, domain: list[Any], fields: list[str], groupby: list[str], offset: int = 0, limit: int = 0, orderby: str = '') -> list[dict]:
        """
        Similar to Odoo's `read_group` method, but with access restricted to the models and fields
        defined in data sources of type 'model'.

        Args:
            model_name (str): The technical name of the Odoo model to group on.
            domain (list): The search domain to filter records. The data type of the value element must be the same as the field type.
            fields (list): The list of field names to return in the results.
            groupby (list): The list of field names to group by.
            offset (int): The number of records to skip, defaults to 0.
            limit (int): The maximum number of records to return, defaults to 0 (no limit).
            orderby (str): The field to sort results by, defaults to empty string.

        Returns:
            list[dict]: A list of dictionaries containing the grouped results, each dict containing the requested fields for each group.
        """
        self.ensure_one()
        # Check both fields and groupby fields
        check_fields = (fields or []) + (groupby or [])
        self.assistant_id._check_model_fields_access(model_name, check_fields)
        domain = expression.AND([self.assistant_id._get_model_domain_access(model_name), domain])
        return self.env[model_name].read_group(domain, fields, groupby, offset, limit, orderby, lazy=False)
