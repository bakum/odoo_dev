/** @odoo-module */

import { session } from "@web/session";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class ImportBudgetController extends ListController {
    async onClickImport() {
        const activeIds = await this.model.orm.search(this.props.resModel, this.props.domain, {
            limit: session.active_ids_limit,
            context: this.props.context,
        });
        return this.actionService.doAction("ug_base_distrib.action_import_distrib_budget", {
            additionalContext: {
                active_ids: activeIds,
            },
            onClose: () => {
                this.model.load();
            },
        });
    }
    OnDownload() {
        // this.actionService.doAction({
        //     'type': 'ir.actions.act_url',
        //     'url': '/ug_base_distrib/static/xls/template_budget_distrib.xlsx',
        //     'target': 'new'
        // })
        return this.actionService.doAction("ug_base_distrib.report_export_sell_in_xls", {});
    }
}

export const ImportBudgetListView = {
    ...listView,
    Controller: ImportBudgetController,
    buttonTemplate: 'ImportBudget.Buttons',
}

registry.category("views").add('import_distrib_budget_list', ImportBudgetListView);