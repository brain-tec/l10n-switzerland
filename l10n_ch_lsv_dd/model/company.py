# b-*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 brain-tec AG (http://www.braintec-group.com)
#    All Right Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _

HOURS_SELECTION = []
for hour in xrange(24):
    HOURS_SELECTION.append((str(hour), str(hour)))


class ResCompany(models.Model):
    ''' Overrides it to add the email addresses where to send the LSV/DD files
        every time they are collected by the cron.job.
    '''

    _inherit = 'res.company'

#     @api.multi
#     def write(self, values):
#         ''' Overrides the write() so that a a check is done over
#             certain values which must be set. In particular, the parameters
#             which control the automatic sending of the
#             LSV/DD payment files.
#         '''
#         values_to_check

    last_lsv_dd_send_date = fields.Datetime(
        'Last LSV/DD Sending Date',
        help='The date in which the LSV and/or DD payment files were sent.'
    )

    lsv_dd_send_hour_start = fields.Selection(
        HOURS_SELECTION,
        string='LSV/DD Sending Hour (Start)',
        help='From this hour on, allow to send the LSV/DD payment files.',
        default='2'
    )

    lsv_email_address = fields.Char(
        'LSV Email Address',
        help='Email address where to send the LSV files.'
    )

    lsv_payment_mode = fields.Many2one(
        'payment.mode',
        string='Payment Mode for LSV',
        help='The payment mode to use when creating the payment orders '
             'which will be used to generate the LSV files.'
    )

    lsv_currency = fields.Selection(
        [('CHF', 'CHF'), ('EUR', 'EUR')],
        string="Currency for LSV",
        default='CHF'
    )

    lsv_bank_account_id = fields.Many2one('res.partner.bank', 'Bank for LSV',
                                          help='The bank account to use '
                                               'for LSV payment files.')

    dd_email_address = fields.Char(
        'DD Email Address',
        help='Email address where to send the DD files.'
    )

    dd_payment_mode = fields.Many2one(
        'payment.mode',
        string='Payment Mode for DD',
        help='The payment mode to use when creating the payment orders '
             'which will be used to generate the DD files.'
    )

    dd_currency = fields.Selection(
        [('CHF', 'CHF'), ('EUR', 'EUR')],
        string="Currency for DD",
        default='CHF'
    )

    dd_bank_account_id = fields.Many2one('res.partner.bank', 'Bank for DD',
                                         help='The bank account to use for DD '
                                              'payment files.')
