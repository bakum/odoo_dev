/** @odoo-module **/

import { Component, useRef, onMounted, useState, useEffect } from '@odoo/owl';
import { jsonrpc } from "@web/core/network/rpc_service";


export class CertLoginApp extends Component {
    static template = 'sign_auth.CertLoginApp';
    static props = {
        url_xml_http_proxy_service: {type: String, required: true},
        url_get_certificates: {type: String, required: true},
        url_cas: {type: String, required: true},
    }

    onKeyDown(ev) {
        if (ev.key === 'Enter') {
            this.readPrivateKeyButtonClick();
        }   
    }

    async onSubmit(ev) {
        ev.preventDefault();
        const payload = {
            keyInfo: this.state.keyInfo['ownerInfo'],
        };
        const result = await jsonrpc('/sign/login', payload);
        this.onChangeMenuItem();
        if (result.status === 'ok') {
            window.location.href = result.redirect;
        } else {
            // можно показать ошибку или перейти на login
            // const res = await result.json();
            this.setAlert(result.message || 'Authorization error', 'alert-danger', true);           
        }

        // const csrf = odoo.csrf_token; // встроенный токен CSRF
        // const keyInfo = this.state.keyInfo;
        // const response = await fetch('/sign/login', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //         'X-CSRFToken': csrf,
        //     },
        //     body: JSON.stringify({ keyInfo }),
        // });

        // if (response.redirected) {
        //     window.location.href = response.url; // сервер сам вернёт redirect
        // } else {
        //     const result = await response.json();
        //     this.setAlert(result.message || 'Ошибка авторизации', 'alert-danger', true);
        // }

    }


    setAlert(message, className, closeButton = false) {
        this.utils.alert(message, className, closeButton);
    }

    setup() {
        this.state = useState({
            privateKeyReaded: false,
            keyInfo: null,
        }); 
        this.euSign = EUSignCP();
        this.utils = Utils(this.euSign);

        this.CACertificatesSessionStorageName = "CACertificates"
        this.CAServerIndexSessionStorageName = "CAServerIndex"
        this.CertsLocalStorageName = "Certificates"
        this.CRLsLocalStorageName = "CRLs"
        this.PrivateKeyNameSessionStorageName = "PrivateKeyName"
        this.PrivateKeySessionStorageName = "PrivateKey"
        this.PrivateKeyPasswordSessionStorageName = "PrivateKeyPassword"
        this.PrivateKeyCertificatesSessionStorageName = "PrivateKeyCertificates"
        this.PrivateKeyCertificatesChainSessionStorageName = "PrivateKeyCertificatesChain"
        this.privateKeyCerts = null

        this.CAsServersSelect = useRef("CAsServersSelect")
        this.SelectedCertsList = useRef("SelectedCertsList")
        this.SelectedCRLsList = useRef("SelectedCRLsList")
        this.PKeyFileName = useRef("PKeyFileName")
        this.PKeyPassword = useRef("PKeyPassword")
        this.PKeyReadButton = useRef("PKeyReadButton")
        this.PKeyFileInput = useRef("PKeyFileInput")
        this.AuthButton = useRef("AuthButton")

        useEffect((isKeyReaded) => {
            this.AuthButton.el.disabled = !isKeyReaded
        }, () => [this.state.privateKeyReaded])

        onMounted(async () => {
            this.initialize()
        })
    }

    onchangeCASettings(event) {
        this.setCASettings(event.target.selectedIndex);
    }

    selectPrivateKeyFile(el) {
        this.PKeyFileName.el.value = el.target.files[0]?.name || '';
        this.PKeyPassword.el.disabled = !el.target.files[0];
    }

    readPrivateKeyButtonClick() {
        const passwordTextField = this.PKeyPassword.el;
        const certificatesFiles = this.privateKeyCerts;
        const self = this;

        const _onError = function (e) {
            // setStatus('');
            // alert(e);
            self.file_loaded = false
            self.setAlert(e, 'alert-danger')
        };

        const _onSuccess = function (keyName, key) {
            self.readPrivateKey(keyName, new Uint8Array(key),
                passwordTextField.value, null, false);
        };

        try {
            if (!this.state.privateKeyReaded) {
                // setStatus('зчитування ключа');

                const files = this.PKeyFileInput.el.files;

                if (files.length !== 1) {
                    _onError("Виникла помилка при зчитуванні особистого ключа. " +
                        "Опис помилки: файл з особистим ключем не обрано");
                    return;
                }

                if (passwordTextField.value == "") {
                    passwordTextField.focus();
                    _onError("Виникла помилка при зчитуванні особистого ключа. " +
                        "Опис помилки: не вказано пароль доступу до особистого ключа");
                    return;
                }

                if (this.state.loadPKCertsFromFile &&
                    (certificatesFiles == null ||
                        certificatesFiles.length <= 0)) {
                    _onError("Виникла помилка при зчитуванні особистого ключа. " +
                        "Опис помилки: не обрано жодного сертифіката відкритого ключа");
                    return;
                }

                var _onFileRead = function (readedFile) {
                    _onSuccess(readedFile.file.name, readedFile.data);
                };

                this.euSign.ReadFile(files[0], _onFileRead, _onError);
            } else {
                this.file_loaded = false
                this.state.certificates = []
                this.onChangeMenuItem()
            }
        } catch (e) {
            _onError(e.message);
        }
    }

    loadCAsSettings(onSuccess, onError) {
        const pThis = this;

        const _onSuccess = function (casResponse) {
            try {
                const servers = JSON.parse(casResponse.replace(/\\'/g, "'"));

                const select = pThis.CAsServersSelect.el;
                for (let i = 0; i < servers.length; i++) {
                    const option = document.createElement("option");
                    option.text = servers[i].issuerCNs[0];
                    select.add(option);
                }

                pThis.CAsServers = servers;

                onSuccess();
            } catch (e) {
                onError();
            }
        };

        this.euSign.LoadDataFromServer(this.props.url_cas, _onSuccess, onError, false);
    }

    setDefaultSettings() {
        try {
            this.euSign.SetXMLHTTPProxyService(this.props.url_xml_http_proxy_service);

            let settings = this.euSign.CreateFileStoreSettings();
            settings.SetPath("/certificates");
            settings.SetSaveLoadedCerts(true);
            this.euSign.SetFileStoreSettings(settings);

            settings = this.euSign.CreateProxySettings();
            this.euSign.SetProxySettings(settings);

            settings = this.euSign.CreateTSPSettings();
            this.euSign.SetTSPSettings(settings);

            settings = this.euSign.CreateOCSPSettings();
            this.euSign.SetOCSPSettings(settings);

            settings = this.euSign.CreateCMPSettings();
            this.euSign.SetCMPSettings(settings);

            settings = this.euSign.CreateLDAPSettings();
            this.euSign.SetLDAPSettings(settings);

            settings = this.euSign.CreateOCSPAccessInfoModeSettings();
            settings.SetEnabled(true);
            this.euSign.SetOCSPAccessInfoModeSettings(settings);

            const CAs = this.CAsServers;
            settings = this.euSign.CreateOCSPAccessInfoSettings();
            for (let i = 0; i < CAs.length; i++) {
                settings.SetAddress(CAs[i].ocspAccessPointAddress);
                settings.SetPort(CAs[i].ocspAccessPointPort);

                for (let j = 0; j < CAs[i].issuerCNs.length; j++) {
                    settings.SetIssuerCN(CAs[i].issuerCNs[j]);
                    this.euSign.SetOCSPAccessInfoSettings(settings);
                }
            }
        } catch (e) {
            this.setAlert("Виникла помилка при встановленні налашувань: " + e.message, 'alert-danger')
        }
    }

    setItemsToList(listId, items) {
        var output = [];
        for (var i = 0, item; item = items[i]; i++) {
            output.push('<li><strong>', item, '</strong></li>');
        }

        document.getElementById(listId).innerHTML =
            '<ul>' + output.join('') + '</ul>';
    }

    loadCertsAndCRLsFromLocalStorage() {
        try {
            var files = this.loadFilesFromLocalStorage(
                this.CertsLocalStorageName,
                (fileName, fileData) => {
                    if (fileName.indexOf(".cer") >= 0)
                        this.euSign.SaveCertificate(fileData);
                    else if (fileName.indexOf(".p7b") >= 0)
                        this.euSign.SaveCertificates(fileData);
                });
            if (files != null && files.length > 0)
                this.setItemsToList('SelectedCertsList', files);
            else {
                this.SelectedCertsList.el.innerHTML = "Сертифікати відсутні в локальному сховищі"
            }
        } catch (e) {
            this.SelectedCertsList.el.innerHTML = "Виникла помилка при завантаженні сертифікатів " +
                "з локального сховища"
        }

        try {
            var files = this.loadFilesFromLocalStorage(
                this.CRLsLocalStorageName,
                (fileName, fileData) => {
                    if (fileName.indexOf(".crl") >= 0) {
                        try {
                            this.euSign.SaveCRL(true, fileData);
                        } catch (e) {
                            this.euSign.SaveCRL(false, fileData);
                        }
                    }
                });
            if (files != null && files.length > 0)
                this.setItemsToList('SelectedCRLsList', files);
            else {
                this.SelectedCRLsList.el.innerHTML = "СВС відсутні в локальному сховищі"
            }
        } catch (e) {
            this.SelectedCRLsList.el.innerHTML = "Виникла помилка при завантаженні СВС з локального сховища"
        }

    }

    loadFilesFromLocalStorage(localStorageFolder, loadFunc) {
        if (!this.utils.IsStorageSupported())
            this.euSign.RaiseError(EU_ERROR_NOT_SUPPORTED);

        if (this.utils.IsFolderExists(localStorageFolder)) {
            const files = this.utils.GetFiles(localStorageFolder);
            for (var i = 0; i < files.length; i++) {
                var file = this.utils.ReadFile(
                    localStorageFolder, files[i]);
                loadFunc(files[i], file);
            }
            return files;
        } else {
            this.utils.CreateFolder(localStorageFolder);
            return null;
        }
    }

    loadCertsFromServer() {
        const pThis = this;
        const certificates = this.utils.GetSessionStorageItem(
            this.CACertificatesSessionStorageName, true, false);
        if (certificates != null) {
            try {
                this.euSign.SaveCertificates(certificates);

                return;
            } catch (e) {
                this.setAlert("Виникла помилка при імпорті " +
                    "завантажених з сервера сертифікатів " +
                    "до файлового сховища", 'alert-danger')
            }
        }

        var _onSuccess = function (certificates) {
            try {
                pThis.euSign.SaveCertificates(certificates);
                pThis.utils.SetSessionStorageItem(
                    pThis.CACertificatesSessionStorageName,
                    certificates, false);
            } catch (e) {

                pThis.setAlert("Виникла помилка при імпорті " +
                    "завантажених з сервера сертифікатів " +
                    "до файлового сховища", 'alert-danger')
            }
        };

        var _onFail = function (errorCode) {
            console.log("Виникла помилка при завантаженні сертифікатів з сервера. " +
                "(HTTP статус " + errorCode + ")");
        };

        this.utils.GetDataFromServerAsync(this.props.url_get_certificates, _onSuccess, _onFail, true);
    }

    setCASettings(caIndex) {
        try {
            var caServer = (caIndex < this.CAsServers.length) ?
                this.CAsServers[caIndex] : null;
            var offline = ((caServer == null) ||
                (caServer.address == "")) ?
                true : false;
            var useCMP = (!offline && (caServer.cmpAddress != ""));
            var loadPKCertsFromFile = (caServer == null) ||
                (!useCMP && !caServer.certsInKey);

            this.state.CAServer = caServer;
            this.state.offline = offline;
            this.state.useCMP = useCMP;
            this.state.loadPKCertsFromFile = loadPKCertsFromFile;

            let settings;

            this.clearPrivateKeyCertificatesList();

            settings = this.euSign.CreateTSPSettings();
            if (!offline) {
                settings.SetGetStamps(true);
                if (caServer.tspAddress != "") {
                    settings.SetAddress(caServer.tspAddress);
                    settings.SetPort(caServer.tspAddressPort);
                } else {
                    settings.SetAddress('acskidd.gov.ua');
                    settings.SetPort('80');
                }
            }
            this.euSign.SetTSPSettings(settings);

            settings = this.euSign.CreateOCSPSettings();
            if (!offline) {
                settings.SetUseOCSP(true);
                settings.SetBeforeStore(true);
                settings.SetAddress(caServer.ocspAccessPointAddress);
                settings.SetPort("80");
            }
            this.euSign.SetOCSPSettings(settings);

            settings = this.euSign.CreateCMPSettings();
            settings.SetUseCMP(useCMP);
            if (useCMP) {
                settings.SetAddress(caServer.cmpAddress);
                settings.SetPort("80");
            }
            this.euSign.SetCMPSettings(settings);

            settings = this.euSign.CreateLDAPSettings();
            this.euSign.SetLDAPSettings(settings);
        } catch (e) {
            this.setAlert("Виникла помилка при встановленні налашувань: " + e.message, 'alert-danger')
        }
    }

    clearPrivateKeyCertificatesList() {
        this.privateKeyCerts = null;
    }

    loadCAServer() {
        const index = this.utils.GetSessionStorageItem(
            this.CAServerIndexSessionStorageName, false, false);
        if (index != null) {
            this.CAsServersSelect.el.selectedIndex = parseInt(index)

            this.setCASettings(parseInt(index));
        }
    }

    getCAServer() {
        const index = this.CAsServersSelect.el.selectedIndex;

        if (index < this.CAsServers.length)
            return this.CAsServers[index];

        return null;
    }

    readPrivateKeyAsStoredFile() {
        const self = this
        const keyName = this.utils.GetSessionStorageItem(
            this.PrivateKeyNameSessionStorageName, false, false);
        const key = this.utils.GetSessionStorageItem(
            this.PrivateKeySessionStorageName, true, false);
        const password = this.utils.GetSessionStorageItem(
            this.PrivateKeyPasswordSessionStorageName, false, true);
        if (keyName == null || key == null || password == null)
            return;

        this.loadCAServer();

        this.PKeyFileName.el.value = keyName
        this.PKeyPassword.el.value = password
        const _readPK = async () => {
            self.readPrivateKey(keyName, key, password, null, true);
            if (self.euSign.IsPrivateKeyReaded()) {
                self.showOwnerInfo();
            }
        };
        setTimeout(_readPK, 10);

        return;
    }

    onChangeMenuItem() {

        this.removeStoredPrivateKey();
        this.euSign.ResetPrivateKey();
        this.privateKeyReaded(false);
        this.PKeyPassword.el.value = "";
        this.PKeyFileInput.el.value = null
        this.clearPrivateKeyCertificatesList();
        // this.sharedState.status_key = "";
        this.utils.RemoveSessionStorageItem(
            this.CACertificatesSessionStorageName);
        // this.fileElem.el.value = null
    }

    showOwnerInfo() {
        try {
            const ownerInfo = this.euSign.GetPrivateKeyOwnerInfo();
            this.state.keyInfo = {
                ownerInfo: Object.assign({}, ownerInfo)
            };
        } catch (e) {
            this.setAlert(e.message, 'alert-danger')
        }
    }

    storePrivateKey(keyName, key, password, certificates) {
        if (!this.utils.SetSessionStorageItem(
                this.PrivateKeyNameSessionStorageName, keyName, false) ||
            !this.utils.SetSessionStorageItem(
                this.PrivateKeySessionStorageName, key, false) ||
            !this.utils.SetSessionStorageItem(
                this.PrivateKeyPasswordSessionStorageName, password, true) ||
            !this.storeCAServer()) {
            return false;
        }

        if (Array.isArray(certificates)) {
            if (!this.utils.SetSessionStorageItems(
                this.PrivateKeyCertificatesSessionStorageName,
                certificates, false)) {
                return false;
            }
        } else {
            if (!this.utils.SetSessionStorageItem(
                this.PrivateKeyCertificatesChainSessionStorageName,
                certificates, false)) {
                return false;
            }
        }

        return true;
    }

    removeCAServer() {
        this.utils.RemoveSessionStorageItem(
            this.CAServerIndexSessionStorageName);
    }

    removeStoredPrivateKey() {
        this.utils.RemoveSessionStorageItem(
            this.PrivateKeyNameSessionStorageName);
        this.utils.RemoveSessionStorageItem(
            this.PrivateKeySessionStorageName);
        this.utils.RemoveSessionStorageItem(
            this.PrivateKeyPasswordSessionStorageName);
        this.utils.RemoveSessionStorageItem(
            this.PrivateKeyCertificatesChainSessionStorageName);
        this.utils.RemoveSessionStorageItem(
            this.PrivateKeyCertificatesSessionStorageName);

        this.removeCAServer();
    }

    storeCAServer() {
        const index = this.CAsServersSelect.el.selectedIndex;
        return this.utils.SetSessionStorageItem(
            this.CAServerIndexSessionStorageName, index.toString(), false);
    }

    getPrivateKeyCertificates(key, password, fromCache, onSuccess, onError) {
        let certificates;

        if (this.state.CAServer != null &&
            this.state.CAServer.certsInKey) {
            onSuccess([]);
            return;
        }

        if (fromCache) {
            if (this.state.useCMP) {
                certificates = this.utils.GetSessionStorageItem(
                    this.PrivateKeyCertificatesChainSessionStorageName, true, false);
            } else if (this.state.loadPKCertsFromFile) {
                certificates = this.utils.GetSessionStorageItems(
                    this.PrivateKeyCertificatesSessionStorageName, true, false)
            }

            onSuccess(certificates);
        } else if (this.state.useCMP) {
            this.getPrivateKeyCertificatesByCMP(
                key, password, onSuccess, onError);
        } else if (this.state.loadPKCertsFromFile) {
            const _onSuccess = function (files) {
                var certificates = [];
                for (var i = 0; i < files.length; i++) {
                    certificates.push(files[i].data);
                }

                onSuccess(certificates);
            };

            this.euSign.ReadFiles(
                this.privateKeyCerts,
                _onSuccess, onError);
        }
    }

    getPrivateKeyCertificatesByCMP(key, password, onSuccess, onError) {
        try {
            const cmpAddress = this.getCAServer().cmpAddress + ":80",
                keyInfo = this.euSign.GetKeyInfoBinary(key, password);
            onSuccess(this.euSign.GetCertificatesByKeyInfo(keyInfo, [cmpAddress]));
        } catch (e) {
            onError(e);
        }
    }

    readPrivateKey(keyName, key, password, certificates, fromCache) {
        const self = this;
        const _onError = (e) => {
            // setStatus('');

            if (fromCache) {
                self.removeStoredPrivateKey();
                self.privateKeyReaded(false);
            } else {
                // alert(e);
                self.setAlert(e, 'alert-danger')
            }

            // if (e.GetErrorCode != null &&
            //     e.GetErrorCode() == EU_ERROR_CERT_NOT_FOUND) {
            //
            //     euSignTest.mainMenuItemClicked(
            //         document.getElementById('MainPageMenuCertsAndCRLs'),
            //         'MainPageMenuCertsAndCRLsPage');
            // }
        };

        if (certificates == null) {
            const _onGetCertificates = (certs) => {
                if (certs == null) {
                    _onError(self.euSign.MakeError(EU_ERROR_CERT_NOT_FOUND));
                    return;
                }

                self.readPrivateKey(keyName, key, password, certs, fromCache);
            };

            this.getPrivateKeyCertificates(
                key, password, fromCache, _onGetCertificates, _onError);
            return;
        }

        try {
            if (Array.isArray(certificates)) {
                for (var i = 0; i < certificates.length; i++) {
                    this.euSign.SaveCertificate(certificates[i]);
                }
            } else {
                this.euSign.SaveCertificates(certificates);
            }

            this.euSign.ReadPrivateKeyBinary(key, password);

            if (!fromCache && this.utils.IsSessionStorageSupported()) {
                if (!this.storePrivateKey(
                    keyName, key, password, certificates)) {
                    this.removeStoredPrivateKey();
                }
            }

            this.privateKeyReaded(true);
            // this.file_loaded = this.FileToSign.el.files.length > 0
            this.pKeyInfo()

            if (!fromCache)
                this.showOwnerInfo();
            this.setAlert('Особистий ключ успішно завантажено!', 'alert-success')
        } catch (e) {
            _onError(e.message);
        }
    }

    pKeyInfo() {
        try {
            if (this.euSign.IsPrivateKeyReaded()) {
                let i = 0
                this.state.certificates = []
                while (true) {
                    const certInfo = this.euSign.EnumOwnCertificates(i),
                        info = {}
                    if (certInfo == null)
                        break
                    const cert = this.euSign.GetCertificate(
                            certInfo.GetIssuer(), certInfo.GetSerial()),
                        keyUsage = certInfo.GetKeyUsage()

                    info.serial = 'EU-' + certInfo.GetSerial() + '.cer'
                    info.certificate = cert
                    info.keyUsage = keyUsage
                    this.state.certificates.push(info)
                    i++
                }
            }
        } catch (e) {
            this.setAlert(e.message, 'alert-danger')
        }
    }

    privateKeyReaded(isReaded) {
        let enabled = '';
        let disabled = 'disabled';

        if (!isReaded) {
            enabled = 'disabled';
            disabled = '';
            this.state.keyInfo = null;
        }
        this.CAsServersSelect.el.disabled = disabled;
        this.PKeyFileName.el.disabled = disabled;
        this.PKeyPassword.el.disabled = disabled;
        this.PKeyFileInput.el.disabled = disabled;
        // this.PKeySelectFileButton.el.disabled = disabled;
        this.PKeyReadButton.el.innerHTML = isReaded ? 'Стерти' : 'Зчитати'
        this.PKeyFileName.el.value = !isReaded ? '' : this.PKeyFileName.el.value
        this.state.privateKeyReaded = isReaded
        
    }

    initialize() {
        const pThis = this;
        // this.state.loaded = false
        const _onSuccess = () => {
            try {
                pThis.euSign.Initialize();
                pThis.euSign.SetJavaStringCompliant(true);
                pThis.euSign.SetCharset("UTF-16LE");

                pThis.euSign.SetRuntimeParameter(
                    EU_MAKE_PKEY_PFX_CONTAINER_PARAMETER, true);

                if (pThis.euSign.DoesNeedSetSettings()) {
                    pThis.setDefaultSettings();

                    if (pThis.utils.IsStorageSupported()) {
                        pThis.loadCertsAndCRLsFromLocalStorage();
                    } else {
                        pThis.SelectedCertsList.el.innerHTML = "Локальне сховище не підтримується"

                        pThis.SelectedCRLsList.el.innerHTML = "Локальне сховище не підтримується"
                    }
                }

                pThis.loadCertsFromServer();
                pThis.setCASettings(0);

                if (pThis.utils.IsSessionStorageSupported()) {
                    const _readPrivateKeyAsStoredFile = () => {
                        pThis.readPrivateKeyAsStoredFile();
                    };
                    setTimeout(_readPrivateKeyAsStoredFile, 10);
                }
                // pThis.DSCAdESTypeChanged()

            } catch (e) {
                pThis.setAlert(e.message, 'alert-danger')
            }
        };

        const _onError = () => {
            pThis.setAlert('Виникла помилка ' +
                'при завантаженні криптографічної бібліотеки', 'alert-danger')
        };
        this.loadCAsSettings(_onSuccess, _onError);
    }
}

