from odoo.http import Controller, route, request


class EUSignerController(Controller):
    @route("/signer", auth="public", methods=["GET"])
    def signer(self, **kwargs):
        return request.render("eusign_cp.signer", {})