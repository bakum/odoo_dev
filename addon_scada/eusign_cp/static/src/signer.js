/** @odoo-module **/

import {browser} from "@web/core/browser/browser"
import {Component, useState} from "@odoo/owl";
import {Verifier} from "./components/verifier/verifier";
import {EUSigner} from "./components/signer/eusigner";


export class OwlSigner extends Component {
    static template = "eusign_cp.owl_signer"
    static components = {Verifier, EUSigner}

    toggleMenu(ev) {
        const allPanels = document.getElementsByClassName("nav-link");
        const id = ev.target.id;

        if (id === "home") {
            browser.location.href = '/';
            return;
        }

        Array.from(allPanels).forEach(panel => panel.classList.remove("active"));

        this.state.signmode = id === "sign";
        ev.target.classList.toggle("active");
    }

    setup() {
        this.state = useState({
            loaded: false,
            signmode: true,
            status_key: '',
        })
        this.env.sharedState.state = this.state;
    }
}