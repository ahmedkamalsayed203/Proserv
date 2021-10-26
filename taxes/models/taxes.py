from odoo import api, fields, models
import datetime

class Employee_Taxes(models.Model):
    _inherit = 'hr.contract'

    yearly_taxes = fields.Float('Yearly Taxes', compute="_compute_employee_taxes")
    monthly_taxes = fields.Float('Monthly Taxes', compute="_compute_employee_taxes")


    def _compute_employee_taxes(self):
        for rec in self:
            # deduction = self.env["hr.payslip"].search([('employee_id', '=', rec.employee_id.id)])
            # month = datetime.datetime.now().month
            emp_wage = rec.wage
            # if rec.medical_information:
            #     emp_wage -= rec.medical_information_amount
            # for compute in deduction:
            #     if compute.date_from.month == month:
            #         if compute.state == "done":
            #             for table in compute.line_ids:
            #                 if table.category_id.name == "Deduction":
            #                     emp_wage -= (table.quantity * table.amount)
            yearly_wage = emp_wage * 12
            yearly_wage -= (rec.medical_insurance + rec.family_exemption + rec.education_exemption)
            if yearly_wage <= 5000:
                rec.yearly_taxes = yearly_wage * 0.05
                rec.monthly_taxes = rec.yearly_taxes / 12
            elif yearly_wage <= 10000:
                rec.yearly_taxes = ((yearly_wage - 5000) * 0.1) + 250
                rec.monthly_taxes = rec.yearly_taxes / 12
            elif yearly_wage <= 15000:
                rec.yearly_taxes = ((yearly_wage - 10000) * 0.15) + 250 + 500
                rec.monthly_taxes = rec.yearly_taxes / 12
            elif yearly_wage > 15000:
                rec.yearly_taxes = ((yearly_wage - 15000) * 0.2) + 250 + 500 + 750
                rec.monthly_taxes = rec.yearly_taxes / 12
