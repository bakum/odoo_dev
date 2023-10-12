/** @odoo-module */

import { session } from "@web/session";
import { ListController } from "@web/views/list/list_controller";

export class ResCurrencyListController extends ListController {

    /**
     * Handler called when the user clicked on the 'Download Invoices' button.
     */
    async onClickImportCurrencyFromNbu() {
        const activeIds = await this.model.orm.search(this.props.resModel, this.props.domain, {
            limit: session.active_ids_limit,
            context: this.props.context,
        });
        return this.actionService.doAction("ug_import_rates_from_nbu.action_import_rates_from_nbu", {
            additionalContext: {
                active_ids: activeIds,
            },
            onClose: () => {
                this.model.load();
            },
        });
    }
}
