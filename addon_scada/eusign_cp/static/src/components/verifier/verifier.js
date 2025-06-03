/** @odoo-module */

import {Component, onMounted, useRef, useState} from "@odoo/owl"
import {Downloader} from "../downloader/downloader";

export class Verifier extends Component {
    static template = "eusign_cp.owl_verifier"
    static components = {Downloader}

    setAlert(message, className, closeButton = false) {
        this.utils.alert(message, className, closeButton);
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
    async handleFilesForVerification(files) {
        if (files.length === 0) {
            return
        }
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
                break
            }
            if (file.name.endsWith('.pdf')) {
                try {
                    const data = await this.utils.loadFileAsArrayBuffer(file),
                        uint8Array = new Uint8Array(data);
                    this.euSign.PDFGetSignsCount(uint8Array)
                    isSign = true
                    break
                } catch (e) {

                }
            }
            if (file.name.endsWith('.xml')) {
                try {
                    const data = await this.utils.loadFileAsArrayBuffer(file),
                        uint8Array = new Uint8Array(data);
                    this.euSign.XAdESGetSignsCount(uint8Array)
                    isSign = true
                    break
                } catch (e) {

                }
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
                if (file.name.endsWith('.xml')) {
                    try {
                        const data = await this.utils.loadFileAsArrayBuffer(file),
                            uint8Array = new Uint8Array(data);
                        this.euSign.XAdESGetSignsCount(uint8Array)
                        content = 'Файл з підписом : ' + file.name
                        this.fileWihtSign = file
                        // continue
                    } catch (e) {
                        content = 'Файл без підпису : ' + file.name
                        this.fileWihtOutSign = file
                        // continue
                    }
                } else if (file.name.endsWith('.pdf')) {
                    try {
                        const data = await this.utils.loadFileAsArrayBuffer(file),
                            uint8Array = new Uint8Array(data);
                        this.euSign.PDFGetSignsCount(uint8Array)
                        content = 'Файл з підписом : ' + file.name
                        this.fileWihtSign = file
                        // continue
                    } catch (e) {
                        content = 'Файл без підпису : ' + file.name
                        this.fileWihtOutSign = file
                        // continue
                    }
                } else {
                    content = 'Файл без підпису : ' + file.name
                    this.fileWihtOutSign = file
                }
            }
            li.textContent = content;
            fileList.appendChild(li);
        }
        // this.VerificationButton.el.disabled = ''
        this.state.filesForVerifyReaded = true
    }
    handleFiles(ev) {
        this.handleFilesForVerification(ev.target.files)
    }
    getAsicSignTypeString(signType, signLevel) {
        switch (signType) {
            case EU_ASIC_SIGN_TYPE_XADES:
                return this.getXadesSignTypeString(signLevel);
            case EU_ASIC_SIGN_TYPE_CADES:
                return this.getSignTypeString(signLevel);
            default:
                return 'Невизначено';
        }
    }
    getXadesSignTypeString(signType) {
        switch (signType) {
            case EU_XADES_SIGN_LEVEL_B_B:
                return 'Базовий (XAdES-B-B)';
            case EU_XADES_SIGN_LEVEL_B_T:
                return 'З позначкою часу від ЕП (XAdES-B-T)';
            case EU_XADES_SIGN_LEVEL_B_LT:
                return 'З повними даними для перевірки (XAdES-B-LT)';
            case EU_XADES_SIGN_LEVEL_B_LTA:
                return 'З повними даними для архівного зберігання (XAdES-B-LTA)';
            default:
                return 'Невизначено';
        }
    }
    getPDFSignTypeString(signType) {
        switch (signType) {
            case EU_PADES_SIGN_LEVEL_B_B:
                return 'Базовий (PAdES-B-B)';
            case EU_PADES_SIGN_LEVEL_B_T:
                return 'З позначкою часу від ЕП (PAdES-B-T)';
            case EU_PADES_SIGN_LEVEL_B_LT:
                return 'З повними даними для перевірки (PAdES-B-LT)';
            case EU_PADES_SIGN_LEVEL_B_LTA:
                return 'З повними даними для архівного зберігання (PAdES-B-LTA)';
            default:
                return 'Невизначено';
        }
    }
    getSignTypeString(signType) {
        switch (signType) {
            case EU_SIGN_TYPE_CADES_BES:
                return 'Базовий (CADES-BES)';
            case EU_SIGN_TYPE_CADES_T:
                return 'З позначкою часу від ЕЦП (CADES-T)';
            case EU_SIGN_TYPE_CADES_C:
                return 'З посиланням на повні дані для перевірки (CADES-C)';
            case EU_SIGN_TYPE_CADES_X_LONG:
                return 'З повними даними для перевірки (CADES-X-LONG)';
            case EU_SIGN_TYPE_CADES_X_LONG | EU_SIGN_TYPE_CADES_X_LONG_TRUSTED:
                return 'З повними даними ЦСК для перевірки (CADES-X-LONG-TRUSTED)';
            default:
                return 'Невизначено';
        }
    }
    verifyFile(ev) {
        if (this.VerificationButton.el.innerHTML == 'Дякую!') {
            this.VerificationButton.el.innerHTML = 'Перевірити'
            this.fileWihtOutSign = null
            this.fileWihtSign = null
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = ''; // Очистить предыдущий список
            this.state.filesForVerifyReaded = false
            this.fileElem.el.value = ''
            this.state.verified_files = []

            return
        }
        if (this.fileWihtSign == null && this.fileWihtOutSign == null) {
            this.setAlert('Виберіть файли для перевірки', 'alert-danger')
            return
        }

        const pThis = this;
        const files = [],
            isInternalSign = !(this.fileWihtOutSign != null),
            isGetSignerInfo = true,
            isAsicSign = this.fileWihtSign.name.endsWith('.asics') || this.fileWihtSign.name.endsWith('.asice'),
            isXAdESSign = this.fileWihtSign.name.endsWith('.xml'),
            isPDFSign = this.fileWihtSign.name.endsWith('.pdf')
        if (!isInternalSign) {
            files.push(this.fileWihtOutSign)
        }
        files.push(this.fileWihtSign);
        if ((files[0].size > (Module.MAX_DATA_SIZE + EU_MAX_P7S_CONTAINER_SIZE)) ||
            (!isInternalSign && (files[1].size > Module.MAX_DATA_SIZE))) {
            this.setAlert("Розмір файлу для перевірки підпису занадто великий. Оберіть файл меншого розміру", 'alert-warning');
            return;
        }
        const _onSuccess = async function (files) {
            try {
                let info = "";
                let signType, file_info = {}, file_with_sign_info = [], files_sign = []
                // pThis.state.verified_files = []
                if (files.length === 1) {
                    file_with_sign_info.serial = files[0].name
                    file_with_sign_info.certificate = files[0].data
                    file_with_sign_info.keyUsage = 'Файл з підписом'
                    files_sign.push(file_with_sign_info)
                }
                if (isAsicSign) {
                    info = pThis.euSign.ASiCVerifyData(0, files[0].data);
                    signType = pThis.getAsicSignTypeString(pThis.euSign.ASiCGetSignType(files[0].data), pThis.euSign.ASiCGetSignLevel(0, files[0].data))
                } else if (isXAdESSign) {
                    pThis.euSign.XAdESGetSignReferences(0, files[0].data).forEach((ref, index) => {
                        // let reference = pThis.euSign.XAdESGetReference(files[isInternalSign ? 0 : 1].data, ref)
                        info = pThis.euSign.XAdESVerifyData(ref, 0, files[0].data);
                    })
                    signType = pThis.getXadesSignTypeString(pThis.euSign.XAdESGetSignLevel(0, files[0].data))
                } else if (isPDFSign) {
                    info = pThis.euSign.PDFVerifyData(0, files[0].data)
                    signType = pThis.getPDFSignTypeString(pThis.euSign.PDFGetSignType(0, files[0].data))
                } else {
                    if (isInternalSign) {
                        info = pThis.euSign.VerifyDataInternal(files[0].data);
                    } else {
                        info = pThis.euSign.VerifyData(files[0].data, files[1].data);
                    }
                    signType = pThis.getSignTypeString(pThis.euSign.GetSignType(0, files[isInternalSign ? 0 : 1].data))
                }

                let message = "Підпис успішно перевірено";

                if (isGetSignerInfo) {
                    const ownerInfo = info.GetOwnerInfo();
                    const timeInfo = info.GetTimeInfo();

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
                    } else {
                        message += "не підтверджено надавачем послуг";
                    }

                    message += '\nТип підпису: ' + signType;
                }

                if (isAsicSign) {
                    for (const ref of pThis.euSign.ASiCGetSignReferences(0, files[0].data)) {
                        // const index = pThis.euSign.ASiCGetSignReferences(0, files[0].data).indexOf(ref);
                        const zip = new JSZip(),
                            file = pThis.euSign.ASiCGetReference(files[0].data, ref)
                        zip.file(ref, file)
                        const content = await zip.generateAsync({type: "blob"})
                        file_info.serial = files[0].name.substring(0, files[0].name.length - 6) + '.zip'
                        file_info.certificate = content
                        file_info.keyUsage = 'Файл без підпису (архів)'
                        files_sign.push(file_info)
                        // pThis.saveFile(files[0].name.substring(0,
                        //     files[0].name.length - 6) + '.zip', content);
                    }
                } else if (isXAdESSign) {
                    if (isInternalSign) {
                        pThis.euSign.XAdESGetSignReferences(0, files[0].data).forEach((ref, index) => {
                            file_info.serial = files[0].name.substring(0, files[0].name.length - 4) + '.verified' + '.xml'
                            file_info.certificate = pThis.euSign.XAdESGetReference(files[0].data, ref)
                            file_info.keyUsage = 'Файл без підпису'
                            files_sign.push(file_info)
                            // pThis.saveFile(files[0].name.substring(0,
                            //     files[0].name.length - 4) + '.verified' + '.xml', pThis.euSign.XAdESGetReference(files[0].data, ref));
                        })
                    }
                } else if (isPDFSign) {
                    // pThis.saveFile(files[0].name.substring(0,
                    //     files[0].name.length - 4) + '.verified' + '.pdf', info.GetData());
                } else {
                    if (isInternalSign) {
                        file_info.serial = files[0].name.substring(0, files[0].name.length - 4)
                        file_info.certificate = info.GetData()
                        file_info.keyUsage = 'Файл без підпису'
                        files_sign.push(file_info)
                        // pThis.saveFile(files[0].name.substring(0,
                        //     files[0].name.length - 4), info.GetData());
                    }
                }

                pThis.setAlert(message, 'alert-success')
                pThis.VerificationButton.el.innerHTML = 'Дякую!'
                pThis.state.verified_files = files_sign
            } catch (e) {
                // alert(e);
                pThis.setAlert(e.message, 'alert-danger')
                // setStatus('');
            }
        };

        const _onFail = function (files) {
            pThis.setAlert("Виникла помилка при зчитуванні файлів для перевірки підпису", 'alert-danger')
        };

        this.utils.LoadFilesToArray(files, _onSuccess, _onFail);
    }
    setup() {
        this.fileWihtSign = null
        this.fileWihtOutSign = null

        this.euSign = EUSignCP();
        this.utils = Utils(this.euSign);

        this.fileElem = useRef("fileElem")
        this.VerificationButton = useRef("VerificationButton")
        this.state = useState({
            filesForVerifyReaded: false,
            verified_files: [],
        })
        onMounted(() => {
            this.applyDragDropEvents()
        })
    }
}