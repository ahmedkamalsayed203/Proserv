# -*- coding: utf-8 -*-
import base64
import json
import math
import re

from datetime import date, datetime, timedelta
from werkzeug import urls

from odoo import fields, http, tools, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq


class WebHrPortal(http.Controller):
    """ HR Portal User Requests"""

    MANDATORY_FIELDS = ['type_id', 'rfrom', 'rto']
    OPTIONAL_FIELDS = ['description']

    def timeoff_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.MANDATORY_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        # erro message for past days
        date_from = data.get('rfrom')
        date_from = (datetime.strptime(date_from, DF)).date()
        date_to = data.get('rto')
        date_to = (datetime.strptime(date_to, DF)).date()
        if date_from < date.today():
            error['rfrom'] = 'Date is not valid'
            error_message.append('Date is not valid')
        if date_to < date_from:
            error['rto'] = 'Date is not valid'
            error_message.append('Date is not valid')

        unknown = [k for k in data if k not in (
            self.MANDATORY_FIELDS + self.OPTIONAL_FIELDS)]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

    @route(['/my/hr_timeoff'], type='http', auth='user', website=True)
    def timeoff_request(self, redirect=None, **post):
        values = {}
        _user = request.env.user
        partner = _user.partner_id
        hrleave = request.env['hr.leave']
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.timeoff_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {
                    'name': values['description'],
                    'holiday_status_id': int(values['type_id']),
                    'request_date_from': values['rfrom'],
                    'request_date_to': values['rto'],
                }
                hrleave.with_user(_user).create(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        rtypes = request.env['hr.leave.type'].sudo().search([])
        rfrom = fields.Date.today()
        values.update({
            'page_name': 'timeoff',
            'partner': partner,
            'rtypes': rtypes,
            'rfrom': rfrom,
            'rto': '',
            'description': '',
            'redirect': redirect,
        })

        response = request.render("loans_taxes.portal_hr_timeoff", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def loan_form_validate(self, data):
        error = dict()
        error_message = []

        mandatory_fields = ['amount']
        optional_fields = []

        # Validation
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        # erro message for past days
        loan_amount = data.get('amount')
        loan_amount = float(loan_amount)
        if loan_amount < 0:
            error['amount'] = 'Amount should not be negative'
            error_message.append('Amount should not be negative')

        unknown = [k for k in data if k not in (
            mandatory_fields + optional_fields)]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

    @route(['/my/hr_loan'], type='http', auth='user', website=True)
    def loan_request(self, redirect=None, **post):
        values = {}
        usr = request.env.user
        partner = usr.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.loan_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            employee = request.env['hr.employee'].sudo().search(
                [('user_id', '=', usr.id)], limit=1)
            loan_obj = request.env['loans.creation']
            if not error:
                values = {
                    'name': employee.id,
                    'request_date': str(date.today()),
                    'loans_amount': float(values['amount']),
                }
                loan_obj.with_user(usr).create(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        values.update({
            'page_name': 'loans',
            'amount': 0,
            'partner': partner,
            'redirect': redirect,
        })

        response = request.render("loans_taxes.portal_hr_loan", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @route(['/my/hr_my_timeoff'], type='http', auth='user', website=True,
           method='GET')
    def my_timeoff(self, redirect=None, **post):
        values = {}
        usr = request.env.user
        partner = usr.partner_id
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', usr.id)], limit=1)
        leave_ids = request.env['hr.leave'].with_user(usr).search(
            [('employee_id', '=', employee.id)], limit=12,
            order='request_date_from asc')
        leaves = [{
            'status': x.state if x.state in ['validate', 'refuse'] else False,
            'name': x.holiday_status_id.display_name,
            'duration': x.number_of_days,
            'description': x.name,
        } for x in leave_ids]
        values.update({
            'page_name': 'mytimeoff',
            'leaves': leaves,
            'partner': partner,
            'redirect': redirect,
        })
        response = request.render("loans_taxes.portal_my_timeoff", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @route(['/my/hr_my_loans'], type='http', auth='user', website=True,
           method='GET')
    def my_loan(self, redirect=None, **post):
        values = {}
        usr = request.env.user
        partner = usr.partner_id
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', usr.id)], limit=1)
        loans = request.env['loans.creation'].search(
            [('name', '=', employee.id)], limit=6)
        loans = [{
            'amount': x.loans_amount,
            'status': x.state if x.state in ['approved', 'cancel'] else False,
            'starting_date': x.start_dateOf_loans,
        } for x in loans]
        values.update({
            'page_name': 'myloans',
            'laons': loans,
            'partner': partner,
            'redirect': redirect,
        })
        response = request.render('loans_taxes.portal_my_loans', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
