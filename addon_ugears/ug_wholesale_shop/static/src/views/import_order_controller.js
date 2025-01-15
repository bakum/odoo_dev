/** @odoo-module */

import { session } from "@web/session";
import { ListController } from "@web/views/list/list_controller";

export class ImportOrderController extends ListController {
    async onClickImportOrder() {
        const activeIds = await this.model.orm.search(this.props.resModel, this.props.domain, {
            limit: session.active_ids_limit,
            context: this.props.context,
        });
        return this.actionService.doAction("ug_wholesale_shop.action_import_order", {
            additionalContext: {
                active_ids: activeIds,
            },
            onClose: () => {
                this.model.load();
                // await this.model.orm.call('ug.wholesale.import.order', 'load_order_from_xls', [], {})
                // this.model.load_order_from_xls()
            },
        });
    }
    OnDownload() {
        this.actionService.doAction({
            'type': 'ir.actions.act_url',
            'url': '/ug_wholesale_shop/static/xls/order_template.xlsx',
            'target': 'new'
        })
    }
}