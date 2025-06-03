/** @odoo-module */

import {Component} from "@odoo/owl"

export class Downloader extends Component {
    static template = "eusign_cp.owl_downloader"
    saveFile(fileName, array) {
        const blob = new Blob([array], {type: "application/octet-stream"});
        saveAs(blob, fileName);
    }
    onLoadCertificate(el) {
        // console.log("onLoadCertificate", el.target);
        // console.log("props", this.props.certificates);
        const elem = this.props.certificates.find(x => x.serial === el.target.innerHTML)
        if (elem) {
            this.saveFile(elem.serial, elem.certificate);
        }
    }
}