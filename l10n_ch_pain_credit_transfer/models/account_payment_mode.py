# Copyright (c) 2018 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, api, _, fields
from odoo.exceptions import UserError
from lxml import etree


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    # default option for account.payment.order
    default_debit_advice_control = fields.Selection(
        [('NOA', 'No Advice'),
         ('SIA', 'Single Advice'),
         ('CND', 'Collective Advice No Details'),
         ('CWD', 'Collective Advice With Details'),
         ], string='Default Debit Advice Control', required=False,
        help="Default Debit Advice Control for Payment Orders\n"
             "Can be used to control the debit advice. The following options are available:\n"
             "• NOA No Advice\n"
             "• SIA Single Advice\n"
             "• CND Collective Advice No Details\n"
             "• CWD Collective Advice With Details\n"
             "If used, then 'Code' must not be present")
    payment_method_code = fields.Char(related='payment_method_id.code',
                                      string='PM Code', readonly=True, store=False)
    default_batch_booking = fields.Boolean(
        string='Default Batch Booking',
        help="Default Batch Booking for Payment Orders\n"
             "If true, the bank statement will display only one debit "
             "line for all the wire transfers of the SEPA XML file ; if "
             "false, the bank statement will display one debit line per wire "
             "transfer of the SEPA XML file.")
