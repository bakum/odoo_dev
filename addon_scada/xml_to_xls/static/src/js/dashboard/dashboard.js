/** @odoo-module **/

import {Component, useState, useRef, useEffect} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import {registry} from "@web/core/registry";
import {useAutoFocus} from "../hooks/hooks";
import {PDFViewer} from "../components/PDFViewer/PDFViewer";

export class XmlDashboard extends Component {
    static components = {PDFViewer};

    setup() {
        this.rpc = rpc;
        this.orm = useService("orm");
        this.state = useState({
            xml_filename: "",
            xls_filename: "#", //http://localhost:8017/web/content/xml.import/53/xls_file/?download=false
            import_id: null,
            hasSearched: false,
            import: [],
            isLoading: false,
        });
        // this.xmlFileInputRef = useRef('xmlFileInput'); // Ссылка на input для выбора XML файла
        this.queryInputRef = useRef('queryInput'); // Ссылка на input для автофокуса
        this.queryInputRef1 = useRef('queryInput1'); // Ссылка на input для автофокуса
        useAutoFocus(this.queryInputRef);
        useEffect((state, xml_filename) => {
            if (state || xml_filename) 
                this.queryInputRef1.el.value = this.state.xml_filename;
        }, () => [this.state.hasSearched, this.state.xml_filename]);
        useEffect((id) => {
            if (id) 
                this.state.xls_filename = `/web/content/xml.import/${id}/xls_file/?download=false`;
            else
                this.state.xls_filename = "#";
        }, () => [this.state.import_id]);
    }

    selectXmlFile(event) {
        const enable = (event.target.files.length == 1);  
        if (!this.state.hasSearched) 
            this.queryInputRef.el.value = enable ? event.target.files[0].name : ''
        else
            this.queryInputRef1.el.value = enable ? event.target.files[0].name : ''

        if (!enable) {
            this.state.import_id = null;
            this.state.xml_filename = "";
            this.state.import = [];
            return;
        }
        // const self = this;
        this.state.isLoading = true;
        const reader = new FileReader();
        reader.onload = async (e) => {
            const dataUrl = e.target.result;  
            // "data:text/xml;base64,...."
            const base64 = dataUrl.split(",")[1];  
            // console.log("Base64 content:", base64);

            const raw = await this.rpc("/xml_to_xls/upload_xml", {
                data: base64,  // содержимое файла в base64
                filename: event.target.files[0].name
            });
            // console.log("Server response:", raw);
            if (raw.error) {
                this.state.import_id = null;
                this.state.xml_filename = "";
                console.error("Search error:", raw.error);
                alert("Error converting: " + raw.error); // или другой способ уведомления пользователя
                return
            }
            this.state.import_id = raw.id;
            this.state.xml_filename = event.target.files[0].name;
            this.state.hasSearched = true;
            // Теперь у нас есть ID созданной записи xml.import
            // console.log("Created xml.import ID:", this.state.import_id);
            // Если нужно передать на сервер:
            // this.rpc("/your/endpoint", {data: base64});
            this.state.import = await this.orm.searchRead("xml.import", [['id', '=', this.state.import_id]], ["id", "xls_file", "name", "xls_filename", "partner_id"]);
            // console.log("Import record:", this.state.import);
            this.state.isLoading = false;
        };
        reader.readAsDataURL(event.target.files[0]);
    }
}

XmlDashboard.template = "xml_to_xls.XmlDashboard";
registry.category("actions").add("xml_to_xls.xml_dashboard", XmlDashboard);