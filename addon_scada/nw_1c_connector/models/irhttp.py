from odoo import models, http


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_api_key(cls):
        api_key = http.request.httprequest.headers.get("Authorization")
        if not api_key:
            raise http.BadRequest("Authorization header with API key missing")

        user_id = http.request.env["res.users.apikeys"]._check_credentials(
            scope="api", key=api_key
        )
        if not user_id:
            raise http.BadRequest("API key invalid")
        # http.request.uid = user_id
        # http.request.uid = 1
        http.request.update_env(user=user_id)

    @classmethod
    def _auth_method_bearer_api_key(cls):
        bearer_api_key = http.request.httprequest.headers.get("Authorization")
        if not bearer_api_key:
            raise http.BadRequest("Authorization header with API key missing")

        arr = bearer_api_key.split(' ')
        if len(arr) <= 1:
            raise http.BadRequest("Authorization must be Bearer type")

        if arr[0] != 'Bearer':
            raise http.BadRequest("Authorization must be Bearer type")

        api_key = arr[1]
        if not api_key:
            raise http.BadRequest("Authorization header with API key missing")

        user_id = http.request.env["res.users.apikeys"]._check_credentials(
            scope="api", key=api_key
        )
        if not user_id:
            raise http.BadRequest("API key invalid")

        http.request.update_env(user=user_id)
