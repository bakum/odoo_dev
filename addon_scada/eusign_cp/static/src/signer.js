/** @odoo-module **/

// import {loadCSS, loadJS} from "@web/core/assets"
import {browser} from "@web/core/browser/browser"
import {Component, onMounted, useRef, useState, onWillUnmount} from "@odoo/owl";

export class OwlSigner extends Component {
    static template = "eusign_cp.owl_signer"

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

    handleFilesForVerification(files) {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = ''; // Очистить предыдущий список
        this.fileWihtSign = null
        this.fileWihtOutSign = null
        this.state.filesForVerifyReaded = false
        if (files.length > 2) {
            this.setAlert('Виберіть не більше 2-х файлів', 'alert-danger')
            return
        }
        let isSign = false
        for (const file of files) {
            if (file.name.endsWith('.p7s') || file.name.endsWith('.asics') || file.name.endsWith('.asice')) {
                isSign = true
            }
        }
        if (!isSign) {
            this.setAlert('Виберіть файл з підписом', 'alert-danger')
            return
        }
        for (const file of files) {
            const li = document.createElement('li');
            let content
            if (file.name.endsWith('.p7s') || file.name.endsWith('.asics') || file.name.endsWith('.asice')) {
                content = 'Файл з підписом : ' + file.name
                this.fileWihtSign = file
            } else {
                content = 'Файл без підпису : ' + file.name
                this.fileWihtOutSign = file
            }
            li.textContent = content;
            fileList.appendChild(li);
        }
        // this.VerificationButton.el.disabled = ''
        this.state.filesForVerifyReaded = true
    }

    onChangeFileToSign(ev) {
        console.log(ev.target)
        this.state.file_loaded = ev.target.files.length > 0 && this.euSign.IsPrivateKeyReaded()
    }

    handleFiles(ev) {
        this.handleFilesForVerification(ev.target.files)
    }

    setItemsToList(listId, items) {
        var output = [];
        for (var i = 0, item; item = items[i]; i++) {
            output.push('<li><strong>', item, '</strong></li>');
        }

        document.getElementById(listId).innerHTML =
            '<ul>' + output.join('') + '</ul>';
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
            if (this.PKeyReadButton.el.innerHTML == 'Зчитати') {
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

                // if (utils.IsFileImage(files[0])) {
                // 	euSignTest.readPrivateKeyAsImage(files[0], _onSuccess, _onError);
                // }
                // else {
                // 	var _onFileRead = function(readedFile) {
                // 		_onSuccess(readedFile.file.name, readedFile.data);
                // 	};
                //
                // 	euSign.ReadFile(files[0], _onFileRead, _onError);
                // }
                var _onFileRead = function (readedFile) {
                    _onSuccess(readedFile.file.name, readedFile.data);
                };

                this.euSign.ReadFile(files[0], _onFileRead, _onError);
            } else {
                this.file_loaded = false
                this.onChangeMenuItem()
            }
        } catch (e) {
            _onError(e.message);
        }
    }

    onChangeMenuItem() {

        this.removeStoredPrivateKey();
        this.euSign.ResetPrivateKey();
        this.privateKeyReaded(false);
        this.PKeyPassword.el.value = "";
        this.PKeyFileInput.el.value = null
        this.clearPrivateKeyCertificatesList();
        this.state.status_key = "";
        this.fileElem.el.value = null
    }

    clearPrivateKeyCertificatesList() {
        this.privateKeyCerts = null;
        // document.getElementById('ChoosePKCertsInput').value = null;
        // document.getElementById('SelectedPKCertsList').innerHTML =
        // 	"Сертифікати відкритого ключа не обрано" + '<br>';
    }

    selectPrivateKeyFile(event) {
        const enable = (event.target.files.length == 1);

        // setPointerEvents(document.getElementById('PKeyReadButton'), enable);
        this.PKeyPassword.el.disabled = enable ? '' : 'disabled'
        // document.getElementById('PKeyPassword').disabled =
        // 	enable ? '' : 'disabled';
        this.PKeyFileName.el.value = enable ? event.target.files[0].name : ''
        // document.getElementById('PKeyFileName').value =
        // 	enable ? event.target.files[0].name : '';
        this.PKeyPassword.el.value = ''
        // document.getElementById('PKeyPassword').value = '';

        // if (enable) {
        // 	var file = event.target.files[0];
        // 	setPointerEvents(document.getElementById('PKeySaveInfo'),
        // 		file.name.endsWith(".jks"));
        // }
        this.state.privateKeyReaded = enable
    }

    loadCertsAndCRLsFromLocalStorage() {
        try {
            var files = this.loadFilesFromLocalStorage(
                this.CertsLocalStorageName,
                 (fileName, fileData) =>{
                    if (fileName.indexOf(".cer") >= 0)
                        this.euSign.SaveCertificate(fileData);
                    else if (fileName.indexOf(".p7b") >= 0)
                        this.euSign.SaveCertificates(fileData);
                });
            if (files != null && files.length > 0)
                this.setItemsToList('SelectedCertsList', files);
            else {
                this.SelectedCertsList.el.innerHTML = "Сертифікати відсутні в локальному сховищі"
                // document.getElementById('SelectedCertsList').innerHTML =
                //     "Сертифікати відсутні в локальному сховищі";
            }
        } catch (e) {
            this.SelectedCertsList.el.innerHTML = "Виникла помилка при завантаженні сертифікатів " +
                "з локального сховища"
            // document.getElementById('SelectedCertsList').innerHTML =
            //     "Виникла помилка при завантаженні сертифікатів " +
            //     "з локального сховища";
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
                // document.getElementById('SelectedCRLsList').innerHTML =
                //     "СВС відсутні в локальному сховищі";
            }
        } catch (e) {
            this.SelectedCRLsList.el.innerHTML = "Виникла помилка при завантаженні СВС з локального сховища"
            // document.getElementById('SelectedCRLsList').innerHTML =
            //     "Виникла помилка при завантаженні СВС з локального сховища";
        }

    }

    getSignTypeString(signType) {
        switch (signType) {
            case EU_SIGN_TYPE_CADES_BES:
                return 'базовий';
            case EU_SIGN_TYPE_CADES_T:
                return 'з позначкою часу від ЕЦП';
            case EU_SIGN_TYPE_CADES_C:
                return 'з посиланням на повні дані для перевірки';
            case EU_SIGN_TYPE_CADES_X_LONG:
                return 'з повними даними для перевірки';
            case EU_SIGN_TYPE_CADES_X_LONG | EU_SIGN_TYPE_CADES_X_LONG_TRUSTED:
                return 'з повними даними ЦСК для перевірки';
            default:
                return 'невизначено';
        }
    }

    verifyFile(ev) {
        // console.log(this.fileWihtOutSign)
        // console.log(this.fileWihtSign)
        if (this.VerificationButton.el.innerHTML == 'Дякую!') {
            this.VerificationButton.el.innerHTML = 'Перевірити'
            this.fileWihtOutSign = null
            this.fileWihtSign = null
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = ''; // Очистить предыдущий список
            this.state.filesForVerifyReaded = false
            this.fileElem.el.value = ''

            return
        }
        if (this.fileWihtSign == null && this.fileWihtOutSign == null) {
            this.setAlert('Виберіть файли для перевірки', 'alert-danger')
            return
        }

        const pThis = this;
        const files = [],
            isInternalSign = !(this.fileWihtOutSign != null),
            isGetSignerInfo = true
        if (!isInternalSign) {
            files.push(this.fileWihtOutSign)
        }
        files.push(this.fileWihtSign);
        if ((files[0].size > (Module.MAX_DATA_SIZE + EU_MAX_P7S_CONTAINER_SIZE)) ||
            (!isInternalSign && (files[1].size > Module.MAX_DATA_SIZE))) {
            this.setAlert("Розмір файлу для перевірки підпису занадто великий. Оберіть файл меншого розміру", 'alert-warning');
            return;
        }
        const _onSuccess = function (files) {
            try {
                var info = "";
                if (isInternalSign) {
                    info = pThis.euSign.VerifyDataInternal(files[0].data);
                } else {
                    info = pThis.euSign.VerifyData(files[0].data, files[1].data);
                }
                var signType = pThis.getSignTypeString(
                    pThis.euSign.GetSignType(0, files[isInternalSign ? 0 : 1].data));

                var message = "Підпис успішно перевірено";

                if (isGetSignerInfo) {
                    var ownerInfo = info.GetOwnerInfo();
                    var timeInfo = info.GetTimeInfo();

                    message += "\n";
                    message += "Підписувач: " + ownerInfo.GetSubjCN() + "\n" +
                        "ЦСК: " + ownerInfo.GetIssuerCN() + "\n" +
                        "Серійний номер: " + ownerInfo.GetSerial() + "\n";
                    if (timeInfo.IsTimeAvail()) {
                        message += (timeInfo.IsTimeStamp() ?
                            "Мітка часу (від даних):" : "Час підпису: ") + timeInfo.GetTime();
                    } else {
                        message += "Час підпису відсутній";
                    }

                    if (timeInfo.IsSignTimeStampAvail()) {
                        message += "\nМітка часу (від підпису):" + timeInfo.GetSignTimeStamp();
                    }

                    message += '\nТип підпису: ' + signType;
                }

                if (isInternalSign) {
                    saveFile(files[0].name.substring(0,
                        files[0].name.length - 4), info.GetData());
                }

                // alert(message);
                // setStatus('');
                pThis.setAlert(message, 'alert-success')
                pThis.VerificationButton.el.innerHTML = 'Дякую!'
            } catch (e) {
                // alert(e);
                pThis.setAlert(e.message, 'alert-danger')
                // setStatus('');
            }
        };

        const _onFail = function (files) {
            // setStatus('');
            // alert("Виникла помилка при зчитуванні файлів для перевірки підпису");
            pThis.setAlert("Виникла помилка при зчитуванні файлів для перевірки підпису", 'alert-danger')
        };

        // setStatus('перевірка підпису файлів');
        this.utils.LoadFilesToArray(files, _onSuccess, _onFail);
    }

    signFile() {
        const file = this.FileToSign.el.files[0];
        const self = this;
        if (this.SignButton.el.innerHTML == 'Дякую!') {
            this.SignButton.el.innerHTML = 'Підписати'
            this.FileToSign.el.value = ''
            this.state.file_loaded = false
            return
        }

        if (!file) {
            this.setAlert('Файл для підпису не обрано. Оберіть файл', 'alert-danger')
            return;
        }

        if (file.size > Module.MAX_DATA_SIZE) {
            // alert("Розмір файлу для піпису занадто великий. Оберіть файл меншого розміру");
            this.setAlert("Розмір файлу для піпису занадто великий. Оберіть файл меншого розміру", 'alert-warning')
            return;
        }
        if (!this.euSign.IsPrivateKeyReaded()) {
            this.setAlert("Особистий ключ не зчитано!", 'alert-danger')
            return;
        }

        const fileReader = new FileReader();

        fileReader.onloadend = ((fileName) => {
            return (evt) => {
                if (evt.target.readyState != FileReader.DONE)
                    return;

                const isInternalSign = false;
                // document.getElementById("InternalSignCheckbox").checked;
                const isAddCert = false;
                // var isAddCert = document.getElementById(
                // 	"AddCertToInternalSignCheckbox").checked;
                const dsAlgType = parseInt(self.DSAlgTypeSelect.el.value);

                var data = new Uint8Array(evt.target.result);

                try {
                    let sign;

                    if (dsAlgType == 1) {
                        if (isInternalSign)
                            sign = self.euSign.SignDataInternal(isAddCert, data, false);
                        else
                            sign = self.euSign.SignData(data, false);
                    } else {
                        sign = self.euSign.SignDataRSA(data, isAddCert,
                            !isInternalSign, false);
                    }

                    self.saveFile(fileName + ".p7s", sign);

                    // setStatus('');
                    // alert("Файл успішно підписано");
                    self.SignButton.el.innerHTML = 'Дякую!'
                    self.setAlert("Файл успішно підписано", 'alert-success')
                } catch (e) {
                    // setStatus('');
                    // alert(e);
                    self.setAlert(e.message, 'alert-danger')
                }
            };
        })(file.name);

        // setStatus('підпис файлу');
        fileReader.readAsArrayBuffer(file);
    }

    saveFile(fileName, array) {
        const blob = new Blob([array], {type: "application/octet-stream"});
        saveAs(blob, fileName);
    }

    setDefaultSettings() {
        try {
            this.euSign.SetXMLHTTPProxyService(this.URL_XML_HTTP_PROXY_SERVICE);

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
            // alert("Виникла помилка при встановленні налашувань: " + e);
            this.setAlert("Виникла помилка при встановленні налашувань: " + e.message, 'alert-danger')
        }
    }

    loadCertsFromServer() {
        const pThis = this;
        const certificates = this.utils.GetSessionStorageItem(
            this.CACertificatesSessionStorageName, true, false);
        if (certificates != null) {
            try {
                this.euSign.SaveCertificates(certificates);
                // this.updateCertList();
                return;
            } catch (e) {
                // alert("Виникла помилка при імпорті " +
                //     "завантажених з сервера сертифікатів " +
                //     "до файлового сховища");
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
                // this.updateCertList();
            } catch (e) {
                // alert("Виникла помилка при імпорті " +
                //     "завантажених з сервера сертифікатів " +
                //     "до файлового сховища");
                pThis.setAlert("Виникла помилка при імпорті " +
                    "завантажених з сервера сертифікатів " +
                    "до файлового сховища", 'alert-danger')
            }
        };

        var _onFail = function (errorCode) {
            console.log("Виникла помилка при завантаженні сертифікатів з сервера. " +
                "(HTTP статус " + errorCode + ")");
        };

        this.utils.GetDataFromServerAsync(this.URL_GET_CERTIFICATES, _onSuccess, _onFail, true);
    }

    getCAServer() {
        const index = this.CAsServersSelect.el.selectedIndex;

        if (index < this.CAsServers.length)
            return this.CAsServers[index];

        return null;
    }

    loadCAServer() {
        const index = this.utils.GetSessionStorageItem(
            this.CAServerIndexSessionStorageName, false, false);
        if (index != null) {
            this.CAsServersSelect.el.selectedIndex = parseInt(index)
            // document.getElementById("CAsServersSelect").selectedIndex =
            // 	parseInt(index);
            this.setCASettings(parseInt(index));
        }
    }

    storeCAServer() {
        const index = this.CAsServersSelect.el.selectedIndex;
        return this.utils.SetSessionStorageItem(
            this.CAServerIndexSessionStorageName, index.toString(), false);
    }

    removeCAServer() {
        this.utils.RemoveSessionStorageItem(
            this.CAServerIndexSessionStorageName);
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

    privateKeyReaded(isReaded) {
        let enabled = '';
        let disabled = 'disabled';

        if (!isReaded) {
            enabled = 'disabled';
            disabled = '';
        }
        this.CAsServersSelect.el.disabled = disabled;
        this.PKeyFileName.el.disabled = disabled;
        this.PKeyPassword.el.disabled = disabled;
        this.PKeyFileInput.el.disabled = disabled;
        this.PKeySelectFileButton.el.disabled = disabled;
        this.PKeyReadButton.el.innerHTML = isReaded ? 'Стерти' : 'Зчитати'
        this.PKeyFileName.el.value = !isReaded ? '' : this.PKeyFileName.el.value
        this.state.privateKeyReaded = isReaded
    }

    DSCAdESTypeChanged() {
        const signType = this.CAdESTypes[
            this.DSCAdESTypeSelect.el.selectedIndex];
        try {
            this.euSign.SetRuntimeParameter(EU_SIGN_TYPE_PARAMETER, signType);
        } catch (e) {
            this.setAlert(e.message, 'alert-danger')
        }
    }

    toggleMenu(ev) {
        const allPanels = document.getElementsByClassName("nav-link");
        const id = ev.target.id;

        if (id === "home") {
            this.onChangeMenuItem();
            browser.location.href = '/';
            return;
        }

        Array.from(allPanels).forEach(panel => panel.classList.remove("active"));

        this.state.signmode = id === "sign";
        ev.target.classList.toggle("active");
        if (!this.state.signmode) {
            this.onChangeMenuItem();
        }
    }

    applyDragDropEvents() {
        const self = this
        let dropArea = document.getElementById('drop-area')
        ;['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false)
        })

        function preventDefaults(e) {
            e.preventDefault()
            e.stopPropagation()
        }

        ;['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false)
        })
        ;['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false)
        })

        function highlight(e) {
            dropArea.classList.add('highlight')
        }

        function unhighlight(e) {
            dropArea.classList.remove('highlight')
        }

        dropArea.addEventListener('drop', handleDrop, false)

        function handleDrop(e) {
            let dt = e.dataTransfer
            let files = dt.files
            self.handleFilesForVerification(files)
        }
    }

    applyAccordionEvents() {
        const containers = document.querySelectorAll(".accordion-container")
        containers.forEach(container => {
            const acc = container.getElementsByClassName("accordion");
            for (let i = 0; i < acc.length; i++) {
                acc[i].addEventListener("click", function () {
                    // Закрыть все панели внутри текущего контейнера
                    const allPanels = container.getElementsByClassName("panel");
                    for (let j = 0; j < allPanels.length; j++) {
                        if (allPanels[j] !== this.nextElementSibling) {
                            allPanels[j].style.maxHeight = null;
                            allPanels[j].previousElementSibling.classList.remove("current");
                        }
                    }

                    // Переключить текущую панель
                    this.classList.toggle("current");
                    const panel = this.nextElementSibling;
                    if (panel.style.maxHeight) {
                        panel.style.maxHeight = null;
                    } else {
                        panel.style.maxHeight = panel.scrollHeight + "px";
                    }
                });
            }
        });
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
            this.file_loaded = this.FileToSign.el.files.length > 0
            // euSignTest.updateCertList();

            if (!fromCache)
                this.showOwnerInfo();
            this.setAlert('Особистий ключ успішно завантажено!', 'alert-success')
        } catch (e) {
            _onError(e.message);
        }
    }

    showOwnerInfo() {
        try {
            // const stringToHTML = function (str) {
            //     const dom = document.createElement('div');
            //     dom.innerHTML = str;
            //     return dom;
            // };
            const ownerInfo = this.euSign.GetPrivateKeyOwnerInfo();
            // this.state.status_key = stringToHTML("Власник: " + ownerInfo.GetSubjCN() + "<br/>" +
            //     "ЦСК: " + ownerInfo.GetIssuerCN() + "<br/>" +
            //     "Серійний номер: " + ownerInfo.GetSerial())
            this.state.status_key = "Власник: " + ownerInfo.GetSubjCN() + "\n" +
                "ЦСК: " + ownerInfo.GetIssuerCN() + "\n" +
                "Серійний номер: " + ownerInfo.GetSerial()
            // alert("Власник: " + ownerInfo.GetSubjCN() + "\n" +
            // 		"ЦСК: " + ownerInfo.GetIssuerCN() + "\n" +
            // 		"Серійний номер: " + ownerInfo.GetSerial());
        } catch (e) {
            // alert(e);
            this.setAlert(e.message, 'alert-danger')
        }
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

        // setStatus('зчитування ключа');
        // setPointerEvents(document.getElementById('PKeyReadButton'), true);
        this.PKeyFileName.el.value = keyName
        // document.getElementById('PKeyFileName').value = keyName;
        // document.getElementById('PKeyPassword').value = password;
        this.PKeyPassword.el.value = password
        const _readPK =  async () => {
            await self.readPrivateKey(keyName, key, password, null, true);
            if (self.euSign.IsPrivateKeyReaded()) {
                self.showOwnerInfo();
            }
        };
        setTimeout(_readPK, 10);

        return;
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
                        // document.getElementById(
                        //     'SelectedCertsList').innerHTML =
                        //     "Локальне сховище не підтримується";
                        pThis.SelectedCRLsList.el.innerHTML = "Локальне сховище не підтримується"
                        // document.getElementById(
                        //     'SelectedCRLsList').innerHTML =
                        //     "Локальне сховище не підтримується";
                    }
                }

                pThis.loadCertsFromServer();
                pThis.setCASettings(0);

                // setPointerEvents(
                //     document.getElementById('PGenKeyButton'), true);
                // setPointerEvents(
                //     document.getElementById('VerifyDataButton'), true);
                //
                // euSignTest.setSelectPKCertificatesEvents();

                if (pThis.utils.IsSessionStorageSupported()) {
                    const _readPrivateKeyAsStoredFile =  () => {
                        pThis.readPrivateKeyAsStoredFile();
                    };
                    setTimeout(_readPrivateKeyAsStoredFile, 10);
                }
                pThis.DSCAdESTypeChanged()

                // euSignTest.updateCertList();

                // setStatus('');
                // pThis.state.loaded = true
            } catch (e) {
                // setStatus('не ініціалізовано');
                // alert(e);
                pThis.setAlert(e.message, 'alert-danger')
            }
        };

        const _onError = () => {
            // setStatus('Не ініціалізовано');
            // alert('Виникла помилка ' +
            //     'при завантаженні криптографічної бібліотеки');
            pThis.setAlert('Виникла помилка ' +
                'при завантаженні криптографічної бібліотеки', 'alert-danger')
            // console.error("Виникла помилка при завантаженні криптографічної бібліотеки")
        };
        this.loadCAsSettings(_onSuccess, _onError);
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

            // document.getElementById('ChoosePKFileText').innerHTML =
            // 	"Оберіть файл з особистим ключем " +
            // 	"та вкажіть пароль захисту";
            // if (loadPKCertsFromFile) {
            // 	document.getElementById('ChoosePKFileText').innerHTML +=
            // 		", а також оберіть сертифікат(и)";
            // }

            let settings;

            // document.getElementById('PKCertsSelectZone').hidden =
            // 	loadPKCertsFromFile ? '' : 'hidden';
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
            // alert("Виникла помилка при встановленні налашувань: " + e);
            this.setAlert("Виникла помилка при встановленні налашувань: " + e.message, 'alert-danger')
        }
    }

    onchangeCASettings(event) {
        this.setCASettings(event.target.selectedIndex);
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

                // select.onchange = function() {
                // 	pThis.setCASettings(select.selectedIndex);
                // };

                pThis.CAsServers = servers;

                onSuccess();
            } catch (e) {
                onError();
            }
        };

        this.euSign.LoadDataFromServer(this.URL_CAS, _onSuccess, onError, false);
    }

    onCloseAlert() {
        this.state.alert_occurred = false
        this.state.alert_object.message = ''
        this.state.alert_object.class = ''
    }

    setAlert(message, className, closeButton = false) {
        const self = this
        this.state.alert_occurred = true
        this.state.alert_object.message = message
        this.state.alert_object.class = className
        let background = this.alertStyles[className]
        Toastify({
            text: message,
            close: closeButton,
            style: {
                background: background,
            },
            stopOnFocus: true,
            duration: 5000
        }).showToast();
    }

    setup() {
        this.state = useState({
            loaded: false,
            file_loaded: false,
            privateKeyReaded: false,
            signmode: true,
            status_key: '',
            alert_occurred: false,
            alert_object: {
                message: '',
                class: '',
            },
            filesForVerifyReaded: false,
        })
        this.fileWihtSign = null
        this.fileWihtOutSign = null
        this.alertStyles = {
            'alert-danger': "linear-gradient(to right, #721c24, #721c24)",
            'alert-warning': "linear-gradient(to right, #721c24, #f8d7da)",
            'alert-success': "linear-gradient(to right, #00b09b, #00b09b)",
        }
        this.URL_GET_CERTIFICATES = "/eusign_cp/static/data/CACertificates.p7b"
        this.URL_CAS = "/eusign_cp/static/data/CAs.json"
        this.URL_XML_HTTP_PROXY_SERVICE = "/signer/proxyHandler";
        this.SubjectCertTypes = [
            {"type": EU_SUBJECT_TYPE_UNDIFFERENCED, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_UNDIFFERENCED},
            {"type": EU_SUBJECT_TYPE_CA, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_UNDIFFERENCED},
            {"type": EU_SUBJECT_TYPE_CA_SERVER, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_UNDIFFERENCED},
            {"type": EU_SUBJECT_TYPE_CA_SERVER, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_CMP},
            {"type": EU_SUBJECT_TYPE_CA_SERVER, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_OCSP},
            {"type": EU_SUBJECT_TYPE_CA_SERVER, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_TSP},
            {"type": EU_SUBJECT_TYPE_END_USER, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_UNDIFFERENCED},
            {"type": EU_SUBJECT_TYPE_RA_ADMINISTRATOR, "subtype": EU_SUBJECT_CA_SERVER_SUB_TYPE_UNDIFFERENCED}
        ]
        this.CertKeyTypes = [
            EU_CERT_KEY_TYPE_UNKNOWN,
            EU_CERT_KEY_TYPE_DSTU4145,
            EU_CERT_KEY_TYPE_RSA,
            EU_CERT_KEY_TYPE_ECDSA
        ];

        this.KeyUsages = [
            EU_KEY_USAGE_UNKNOWN,
            EU_KEY_USAGE_DIGITAL_SIGNATURE,
            EU_KEY_USAGE_KEY_AGREEMENT
        ];

        this.CAdESTypes = [
            EU_SIGN_TYPE_CADES_BES,
            EU_SIGN_TYPE_CADES_T,
            EU_SIGN_TYPE_CADES_C,
            EU_SIGN_TYPE_CADES_X_LONG,
            EU_SIGN_TYPE_CADES_X_LONG | EU_SIGN_TYPE_CADES_X_LONG_TRUSTED
        ];
        this.euSign = EUSignCP();
        this.utils = Utils(this.euSign);

        this.CACertificatesSessionStorageName = "CACertificates"
        this.CAServerIndexSessionStorageName = "CAServerIndex"
        this.CertsLocalStorageName = "Certificates"
        this.CRLsLocalStorageName = "CRLs"
        this.recepientsCertsIssuers = null
        this.recepientsCertsSerials = null
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
        this.PKeySelectFileButton = useRef("PKeySelectFileButton")
        this.DSCAdESTypeSelect = useRef("DSCAdESTypeSelect")
        this.FileToSign = useRef("FileToSign")
        this.DSAlgTypeSelect = useRef("DSAlgTypeSelect")
        this.alertMessage = useRef("alertMessage")
        this.VerificationButton = useRef("VerificationButton")
        this.fileElem = useRef("fileElem")
        this.SignButton = useRef("SignButton")

        onMounted(async () => {
            this.applyDragDropEvents()
            this.applyAccordionEvents()
            await this.initialize()
            setTimeout(() => {
                this.state.loaded = true
            }, 1000)
        })
        onWillUnmount(() => {
            this.onChangeMenuItem()
        })
    }
}