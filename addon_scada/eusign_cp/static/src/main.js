/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {_t} from "@web/core/l10n/translation";
import {mount, whenReady} from "@odoo/owl";
import {makeEnv, startServices, mountComponent} from "@web/env";
import {templates} from "@web/core/assets";
import {OwlSigner} from "./signer";

// Mount the Playground component when the document.body is ready
whenReady(async () => {
    let env = makeEnv();
    await startServices(env)
    env = {
        ...env, sharedState: {
            state: null
        }
    }
    // mount(OwlSigner, document.body, {templates, dev: true, name: "Owl EUSignCP", env});
    await mountComponent(OwlSigner, document.body, { name: "Owl EUSignCP", env })
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