/** @odoo-module */

import {registry} from "@web/core/registry"
import { useService, useBus } from '@web/core/utils/hooks';
const {Component, useState} = owl

class BlockShop extends Component {}
BlockShop.template = 'owl.BlockShop';

export class StartShop extends Component {

    setup() {
        let params = this.props.action.params
        this.websiteService = useService('website');
        if (!params) {
            this.initialUrl = '/shop'
        } else {
            this.initialUrl = params.url
        }

        this.blockedState = useState({
            isBlocked: false,
            showLoader: false,
        });

        useBus(this.websiteService.bus, 'BLOCK', (event) => this.block(event.detail));
        useBus(this.websiteService.bus, 'UNBLOCK', () => this.unblock());
    }
    block({ showLoader = true } = {}) {
        this.blockedState.isBlocked = true;
        this.blockedState.showLoader = showLoader;
    }

    unblock() {
        this.blockedState.isBlocked = false;
        this.blockedState.showLoader = false;
    }
}

StartShop.template = "owl.StartShop"
StartShop.components = {
    BlockShop,
}
registry.category("actions").add("start_shop", StartShop)