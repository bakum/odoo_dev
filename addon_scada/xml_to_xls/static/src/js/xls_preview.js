/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillUpdateProps } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks"

// глобальная переменная XLSX берётся из подключённой библиотеки
class XlsPreview extends Component {
    static template = "xml_to_xsl.Preview";
    static props = { ...standardFieldProps };
    
    setup() {
        this.previewRef = useRef("previewContainer");
        this.orm = useService("orm")
        onWillUpdateProps((nextProps) => {
            // const oldData = this.props.record?.data;
            // const newData = nextProps.record?.data;
            // if (oldData[this.props.name] !== newData[this.props.name]) {
            //     this.renderPreview(newData);
            // }
            if (this.props.record.id !== nextProps.record.id) {
                this.renderPreview(nextProps);
            }
        });
        // console.log(this.props)
        onMounted(() => this.renderPreview(this.props));
    }

    async renderPreview(newProps) {
        const container = this.previewRef.el
        // console.log("model", this.props.record.model.config.resModel)
        // console.log("props", this.props)
        // if (!container) {
        //         console.error("Preview container not found!");
        //         return;
        //     }
        if (!newProps.record.data || !newProps.record.data[newProps.name]) {
            container.innerHTML = "<em>XLS preview will appear after generation</em>";
            return;
        }
        // const recordId = this.props.record.data.id;
        // console.log(this.props.record.data.id)
        if (!newProps.record || !newProps.record.data || !newProps.record.data.id) {
            container.innerHTML = "Record ID not available for preview";
            return;
        }
        // console.log("id", newProps.record.data.id)
        // console.log("id", newProps.record.id)
        let domain = [['id', '=', newProps.record.data.id]], model = newProps.record.model.config.resModel, fields = ['id', newProps.name];
    
        const data = await this.orm.searchRead(model, domain, fields, { limit: 1 })
        // console.log("data", data[0])
        const base64Data = data[0][newProps.name]; // замените на своё поле
        if (!base64Data) {
            container.innerHTML = "Нет данных для предпросмотра XLS";
            return;
        }

        try {
            // конвертируем Base64 в Uint8Array
            // const cleanedBase64 = base64Data.replace(/\s/g, ""); // удаляем пробелы и переносы
            const binary = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));

            // Используем .buffer для совместимости
            const workbook = XLSX.read(binary.buffer, { type: "array" });
            const sheet = workbook.Sheets[workbook.SheetNames[0]];

            const range = XLSX.utils.decode_range(sheet['!ref']);
            let html = `<table border="1" style="border-collapse:collapse;width:100%;">`;
            for (let R = range.s.r; R <= range.e.r; ++R) {
                html += `<tr>`;
                for (let C = range.s.c; C <= range.e.c; ++C) {
                    const cellAddress = { c: C, r: R };
                    const cellRef = XLSX.utils.encode_cell(cellAddress);
                    const cell = sheet[cellRef];

                    let value = cell ? cell.v : "";
                    let style = "";

                    if (cell && cell.s) {
                        const s = cell.s;
                        if (s.fgColor) style += `background-color:#${s.fgColor.rgb};`;
                        if (s.color) style += `color:#${s.color.rgb};`;
                        if (s.bold) style += "font-weight:bold;";
                        if (s.italic) style += "font-style:italic;";
                        if (s.hAlign) style += `text-align:${s.hAlign};`;
                        if (s.vAlign) style += `vertical-align:${s.vAlign};`;
                    }

                    html += `<td style="${style}">${value}</td>`;
                }
                html += `</tr>`;
            }

            html += `</table>`;
            // const html = XLSX.utils.sheet_to_html(sheet);

            container.innerHTML = html;
            //  Конвертируем в JSON для Handsontable
            // const data = XLSX.utils.sheet_to_json(firstSheet, { header: 1, raw: false });
            // const colWidths = data[0] ? new Array(data[0].length).fill(100) : [];

            // // Рендерим через Handsontable
            // new Handsontable(container, {
            //     data: data,
            //     rowHeaders: false,
            //     colHeaders: false,
            //     colWidths: colWidths,
            //     licenseKey: "non-commercial-and-evaluation", // CE
            //     readOnly: true,
            //     stretchH: 'all',
            //     width: '100%',
            //     height: 1200,
            //     manualColumnResize: true,
            //     manualRowResize: true,
            // });
        } catch (e) {
            console.error("Error rendering XLS preview:", e);
            container.innerHTML = "<em>Error rendering XLS preview</em>";
        }
    }
}

export const xlsPreview = {
    component: XlsPreview,
};

registry.category("fields").add("xls_preview", xlsPreview);
