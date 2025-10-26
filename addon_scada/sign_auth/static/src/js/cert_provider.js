/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CertProviderSelect = publicWidget.Widget.extend({
    selector: '#cert_provider_select',
    start: function () {       
        this._populateProviders();
        document.getElementById('PKeyFileInput').addEventListener('change', function () {
        const file = this.files[0];
        if (file) {
            document.getElementById('PKeyFileName').value = file.name;
            document.getElementById('PKeyPassword').disabled = false;
        }
        
});

    },
    _populateProviders: function () {
        // const providers = [
        //     { id: 'acsk_ukraine', name: 'АЦСК України' },
        //     { id: 'privatbank', name: 'ПриватБанк' },
        //     { id: 'iit', name: 'ІІТ' },
        //     { id: 'dss', name: 'ДСС' },
        //     { id: 'key_cert', name: 'KeyCert' },
        // ];
        const $select = this.$el;
        if (!$select.length) return;

        $select.empty(); // Очищаем текущие опции
        fetch('/sign_auth/static/data/CAs.json')
            .then(response => {
            if (!response.ok) throw new Error('Failed to load CAs.json');
                return response.json();
            })
            .then(data => {
                data.forEach((ca, index) => {
                    const label = ca.issuerCNs?.[0];
                    $select.append($('<option>', {
                        value: ca.address || `ca_${index}`,
                        text: label,
                        'data-ocsp': ca.ocspAccessPointAddress,
                        'data-cmp': ca.cmpAddress,
                        'data-tsp': ca.tspAddress,
                    }));
                });
            })
            .catch(err => {
                console.error('Failed to load CAs.json:', err);
            });
    }
});