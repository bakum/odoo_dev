/** @odoo-module */

import {registry} from "@web/core/registry"
import {useService, useBus} from '@web/core/utils/hooks';

const {Component, onWillStart, onMounted, onWillUnmount, useRef, useState} = owl

class BlockShop extends Component {
}

BlockShop.template = 'owl.BlockShop';

export class StartShop extends Component {

    setup() {
        this.params = this.props.action.params
        this.websiteService = useService('website');
        this.router = useService('router');
        this.iframe = useRef('iframe');
        this.container = useRef('container');


        this.blockedState = useState({
            isBlocked: false,
            showLoader: false,
        });

        useBus(this.websiteService.bus, 'BLOCK', (event) => this.block(event.detail));
        useBus(this.websiteService.bus, 'UNBLOCK', () => this.unblock());
        onWillStart(() => {
            if (!this.params) {
                this.initialUrl = '/shop'
            } else {
                this.initialUrl = this.params.url
            }
        })
        onMounted(() => {
            this.websiteService.blockPreview(true, 'load-iframe');
            this.iframe.el.addEventListener('load', () => this.websiteService.unblockPreview('load-iframe'), {once: true});
            // For a frontend page, it is better to use the
            // OdooFrameContentLoaded event to unblock the iframe, as it is
            // triggered faster than the load event.
            this.iframe.el.addEventListener('OdooFrameContentLoaded', () => this.websiteService.unblockPreview('load-iframe'), {once: true});
            this.env.services.messaging.modelManager.messagingCreatedPromise.then(() => {
                this.env.services.messaging.modelManager.messaging.update({isWebsitePreviewOpen: true});
            });
        })
        onWillUnmount(() => {
            this.env.services.messaging.modelManager.messagingCreatedPromise.then(() => {
                this.env.services.messaging.modelManager.messaging.update({isWebsitePreviewOpen: false});
            });
            const {pathname, search, hash} = this.iframe.el.contentWindow.location;
            this.websiteService.lastUrl = `${pathname}${search}${hash}`;
            this.websiteService.currentWebsiteId = null;
            this.websiteService.websiteRootInstance = undefined;
            this.websiteService.pageDocument = null;
        });
    }

    block({showLoader = true} = {}) {
        this.blockedState.isBlocked = true;
        this.blockedState.showLoader = showLoader;
    }

    unblock() {
        this.blockedState.isBlocked = false;
        this.blockedState.showLoader = false;
    }

    _isTopWindowURL({host, pathname}) {
        const backendRoutes = ['/web', '/web/session/logout'];
        return host !== window.location.host
            || (pathname
                && (backendRoutes.includes(pathname)
                ));
    }

    _onPageLoaded(ev) {
        if (
            navigator.userAgent.toLowerCase().includes("chrome")
            && !this.iframe.el.src.includes("iframe_reload")
        ) {
            try {
                /* eslint-disable no-unused-expressions */
                this.iframe.el.contentWindow.location.href;
            } catch (err) {
                if (err.name === "SecurityError") {
                    ev.stopImmediatePropagation();
                    // Note that iframe's `src` is the URL used to start the
                    // website preview, it's not sync'd with iframe navigation.
                    const srcUrl = new URL(this.iframe.el.src);
                    const pathUrl = new URL(srcUrl.searchParams.get("path"), srcUrl.origin);
                    pathUrl.searchParams.set("iframe_reload", "1");
                    srcUrl.searchParams.set("path", `${pathUrl.pathname}${pathUrl.search}`);
                    // We could inject `pathUrl` directly but keep the same
                    // expected URL format `/website/force/1?path=..`
                    this.iframe.el.src = srcUrl.toString();
                    return;
                }
            }
        }

        this.iframe.el.contentDocument.addEventListener('click', (ev) => {
            const linkEl = ev.target.closest('[href]');
            if (!linkEl) {
                return;
            }
            const {href, target, classList} = linkEl;
            if (href && target !== '_blank') {
                if (this._isTopWindowURL(linkEl)) {
                    ev.preventDefault();
                    this.router.redirect(href);
                } else if (this.iframe.el.contentWindow.location.pathname !== new URL(href).pathname) {
                    // This scenario triggers a navigation inside the iframe.
                    this.websiteService.websiteRootInstance = undefined;
                }
            }
        });
    }
}

StartShop.template = "owl.StartShop"
StartShop.components = {
    BlockShop,
}
registry.category("actions").add("start_shop", StartShop)