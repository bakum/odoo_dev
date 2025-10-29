import requests
from werkzeug.exceptions import abort

from odoo.http import Controller, route, request, Response
from urllib.parse import urlparse
import base64
import re

knownHosts = [
    "czo.gov.ua",
    "zc.bank.gov.ua",
    "acskidd.gov.ua",
    "ca.informjust.ua",
    "csk.uz.gov.ua",
    "masterkey.ua",
    "ocsp.masterkey.ua",
    "tsp.masterkey.ua",
    "csk.uss.gov.ua",
    "csk.ukrsibbank.com",
    "acsk.privatbank.ua",
    "ca.mil.gov.ua",
    "acsk.dpsu.gov.ua",
    "acsk.er.gov.ua",
    "ca.mvs.gov.ua",
    "canbu.bank.gov.ua",
    "uakey.com.ua",
    "altersign.com.ua",
    "ca.altersign.com.ua",
    "ocsp.altersign.com.ua",
    "acsk.treasury.gov.ua",
    "ocsp.treasury.gov.ua",
    "ca.gp.gov.ua",
    "acsk.oree.com.ua",
    "ca.treasury.gov.ua",
    "ca.depositsign.com",
    "cesaris.itsway.kiev.ua",
    "ca.credit-agricole.ua",
    "ca.e-life.com.ua",
    "ocsp.e-life.com.ua",
    "tsp.e-life.com.ua",
    "cmp.e-life.com.ua",
    "ca.bankalliance.ua",
    "ca.vchasno.ua",
    "qca.ukrgasbank.com",
    "ca.tax.gov.ua",
    "ca.diia.gov.ua",
    "ca.sensebank.com.ua",
    "ca.tascombank.com.ua",
    "ca.tascombank.ua",
    "va1-knedp.ssu.gov.ua",
    "root-test.czo.gov.ua",
    "ca-test.czo.gov.ua",
    "ca.ngu.gov.ua",
    "ca.monobank.ua"
]
UriMaxLength = 255
UriRegEx = r'^(https?:\/\/)?([a-zA-Z0-9.\-]+)(:[0-9]{1,5})?(\/(.*))?$'
HttpRequestParameterAddress = "address"
HttpContentTypeBase64 = "X-user/base64-data"


class EUSignerProxyHundler(Controller):

    def get_ca_addresses(self):
        url = "https://ca.diia.gov.ua/download/Soft/CAs.json"
        response = requests.get(url)
        response.raise_for_status()  # выбросит исключение при ошибке запроса
        data = response.json()
        return [entry["address"] for entry in data if "address" in entry]

    def isKnownHost(self, uriValue):
        ca_knownHosts = self.get_ca_addresses()
        try:
            if len(uriValue) > UriMaxLength or not re.match(UriRegEx, uriValue):
                return False
            if uriValue.find("://") == -1:
                uriValue = "http://" + uriValue
            uri = urlparse(uriValue)
            if uri.scheme != "http" and uri.scheme != "https":
                return False
            host = urlparse(uriValue).hostname
            if host == None or host == "":
                host = uriValue
            if host in ca_knownHosts:
                return True
        except:
            return False
        return False

    def getContentType(self, uriValue):
        try:
            if uriValue.find("://") == -1:
                uriValue = "http://" + uriValue

            path = urlparse(uriValue).path
            if path == None or path == "":
                return ""

            if path[len(path) - 1] == '/':
                path = path[:-1]

            if path == "/services/cmp" or path == '/public/x509/cmp' or path == 'cmp' or path == '/api/PKI/CMP':
                return ""
            elif path == "/services/ocsp" or path == "/services/ocsp/" or path == "/public/ocsp" or path == "/ocsp" or path == "/ocsp-rsa" or path == "/ocsp-ecdsa" or path == "/OCSPsrv/ocsp" or path == "/queries/ocsp/":
                return "application/ocsp-request"
            elif path == "/services/tsp" or path == "/services/tsp/" or path == "/services/tsp/dstu" or path == "/services/tsp/dstu/" or path == "/services/tsp/rsa" or path == "/services/tsp/rsa/" or path == "/services/tsp/ecdsa" or path == "/services/tsp/ecdsa/" or path == "/public/tsa" or path == "/public/tsp" or path == "/tsp" or path == "/tsp-rsa" or path == "/ecdsa" or path == "/TspHTTPServer/tsp":
                return "application/timestamp-query"
            else:
                return ""
        except:
            return ""

    def HandleRequest(self, httpMethod, httpHeaders, httpURLParams, httpRequestData):
        returnResponse = {'status': 200, 'data': ''}

        address = httpURLParams.get(HttpRequestParameterAddress, '')
        if address == "":
            returnResponse['status'] = 400
            return returnResponse
        if self.isKnownHost(address) == False:
            returnResponse['status'] = 403
            return returnResponse

        url = address
        if url.find("://") == -1:
            url = "http://" + url

        headers = {"Accept": "*/*", "Pragma": "no-cache"}

        try:
            if httpMethod == 'POST':
                if httpHeaders.get('Content-Type') != HttpContentTypeBase64:
                    returnResponse['status'] = 400
                    return returnResponse

                headers['Content-Type'] = self.getContentType(address)
                requestData = base64.b64decode(httpRequestData)
                response = requests.post(url, data=requestData, headers=headers)
            else:
                response = requests.get(url, headers=headers)

            returnResponse['status'] = response.status_code
            if response.status_code == 200:
                returnResponse['data'] = base64.b64encode(response.content).decode('utf-8')
        except requests.RequestException:
            returnResponse['status'] = 500

        return returnResponse

    @route("/sign_auth/proxyHandler", auth="public", cors="*", csrf=False, methods=["GET", "POST"])
    def proxy(self, **kwargs):
        proxyResponse = self.HandleRequest(request.httprequest.method, request.httprequest.headers, request.httprequest.args, request.httprequest.data)
        if proxyResponse['status'] != 200:
            abort(proxyResponse['status'])

        returnResponse = Response(proxyResponse['data'], content_type=HttpContentTypeBase64)

        return returnResponse
