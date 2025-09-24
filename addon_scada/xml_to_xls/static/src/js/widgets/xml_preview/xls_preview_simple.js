/** @odoo-module **/


function initXlsPreview() {
    // находим все кнопки предпросмотра
    document.querySelectorAll(".o_xls_preview_btn").forEach(btn => {
        btn.onclick = async () => {
            // ищем контейнер
            const container = btn.closest("form").querySelector(".o_xls_preview_container");
            if (!container) return;

            // получаем record через data-record-id
            const recordId = btn.closest("form").dataset.id;
            if (!recordId) return;

            try {
                // запрашиваем xls_file через RPC
                const result = await odoo.rpc.query({
                    model: 'xml.import',
                    method: 'read',
                    args: [[parseInt(recordId)], ['xls_file']],
                });

                const xlsBase64 = result[0].xls_file;
                if (!xlsBase64) {
                    container.innerHTML = "<em>No XLS generated</em>";
                    return;
                }

                // преобразуем base64 в binary
                const binary = atob(xlsBase64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

                // читаем через XLSX.js
                const workbook = XLSX.read(bytes, { type: "array" });
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                container.innerHTML = XLSX.utils.sheet_to_html(firstSheet);
            } catch (e) {
                console.error("XLS preview error:", e);
                container.innerHTML = "<em>Error rendering XLS preview</em>";
            }
        };
    });
}

// инициализация после загрузки страницы
document.addEventListener('DOMContentLoaded', initXlsPreview);
