/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {_t} from "@web/core/l10n/translation";
import {mount, whenReady} from "@odoo/owl";
import { session } from "@web/session";
import {makeEnv, startServices, mountComponent} from "@web/env";
import {templates} from "@web/core/assets";
import {OwlSigner} from "./signer";

// Mount the Playground component when the document.body is ready
whenReady(async () => {
    // odoo.info = {
    //     db: session.db,
    //     server_version: session.server_version,
    //     server_version_info: session.server_version_info,
    //     isEnterprise: session.server_version_info ? session.server_version_info.slice(-1)[0] === "e" : undefined,
    // };
    // odoo.isReady = false;
    const root = document.getElementById('eusign_cp_signer');
    if (!root) {
        return;
    }

    let env = makeEnv();
    await startServices(env)
    env = {
        ...env, sharedState: {
            state: null
        }
    }
    // const root = await mount(OwlSigner, document.body, {templates, dev: env.debug, name: "Owl EUSignCP", env});
    // odoo.__WOWL_DEBUG__ = { root };
    const root_mounted = await mountComponent(OwlSigner, root, { name: "Owl EUSignCP", env })
    odoo.__WOWL_DEBUG__ = { root_mounted };
    // odoo.isReady = true;
})

/**
 * This code is iterating over the cause property of an error object to console.error a string
 * containing the stack trace of the error and any errors that caused it.
 * @param {Event} ev
 */
function logError(ev) {
    ev.preventDefault();
    let error = ev?.error || ev.reason;

    if (error.seen) {
        // If an error causes the mount to crash, Owl will reject the mount promise and throw the
        // error. Therefore, this if statement prevents the same error from appearing twice.
        return;
    }
    error.seen = true;

    let errorMessage = error.stack;
    while (error.cause) {
        errorMessage += "\nCaused by: "
        errorMessage += error.cause.stack;
        error = error.cause;
    }
    console.error(errorMessage);
}

browser.addEventListener("error", (ev) => {
    logError(ev)
});
browser.addEventListener("unhandledrejection", (ev) => {
    logError(ev)
});