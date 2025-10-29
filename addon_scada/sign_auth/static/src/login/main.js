/** @odoo-module **/

import {mount, whenReady} from "@odoo/owl";
import { CertLoginApp } from "./components/CertLoginApp";
import {templates} from "@web/core/assets";
import { makeEnv } from "@web/env";

whenReady(async () => {
    const root = document.getElementById('cert_login_mount');
    if (!root) {
        return;
    }
    let env = makeEnv();
    
    await mount(CertLoginApp, root, {templates, env, name: "Owl Sign Authorization Login", props: {
        url_xml_http_proxy_service: '/sign_auth/proxyHandler',
        // url_get_certificates: '/sign_auth/static/data/CACertificates.p7b',
        url_get_certificates: 'https://ca.diia.gov.ua/download/Soft/CACertificates.p7b',
        // url_cas: '/sign_auth/static/data/CAs.json',
        url_cas: 'https://ca.diia.gov.ua/download/Soft/CAs.json',
    }});
});