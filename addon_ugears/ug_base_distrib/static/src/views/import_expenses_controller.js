/** @odoo-module */

import { session } from "@web/session";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class ImportExpensesController extends ListController {
    async onClickImport() {
        const activeIds = await this.model.orm.search(this.props.resModel, this.props.domain, {
            limit: session.active_ids_limit,
            context: this.props.context,
        });
        return this.actionService.doAction("ug_base_distrib.action_import_distrib_expenses", {
            additionalContext: {
                active_ids: activeIds,
            },
            onClose: () => {
                this.model.load();
            },
        });
    }
    OnDownload() {
        this.actionService.doAction({
            'type': 'ir.actions.act_url',
            'url': '/ug_base_distrib/static/xls/template_costs_distrib.xlsx',
            'target': 'new'
        })
    }
}

export const ImportExpensesListView = {
    ...listView,
    Controller: ImportExpensesController,
    buttonTemplate: 'ImportDistribExpenses.Buttons',
};

registry.category("views").add('import_distrib_expenses_list', ImportExpensesListView);