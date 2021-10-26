# -*- coding: utf-8 -*-
from odoo import http

# class LoansTaxes(http.Controller):
#     @http.route('/loans_taxes/loans_taxes/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/loans_taxes/loans_taxes/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('loans_taxes.listing', {
#             'root': '/loans_taxes/loans_taxes',
#             'objects': http.request.env['loans_taxes.loans_taxes'].search([]),
#         })

#     @http.route('/loans_taxes/loans_taxes/objects/<model("loans_taxes.loans_taxes"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('loans_taxes.object', {
#             'object': obj
#         })