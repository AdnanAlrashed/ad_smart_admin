from odoo import http
from odoo.http import request

class CustomController(http.Controller):

    @http.route('/ad_smart_admin/get_fields_visibility', type='json', auth='user')
    def get_fields_visibility(self):
        fields_visibility = request.env['priority'].get_data_fields(request.jsonrequest)
        return fields_visibility