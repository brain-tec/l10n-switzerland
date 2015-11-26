##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    @author: Cyril Sester <cyril.sester@outlook.com>
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

import base64
from datetime import datetime, timedelta
from date_utils import is_weekday, is_past_weekday
from openerp import models, api, _, exceptions, fields, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AccountInvoice(models.Model):

    ''' Inherit invoice to add invoice freeing functionality. It's about
        moving related payment line in a new cancelled payment order. This
        way, the invoice (properly, invoice's move lines) can be used again
        in another payment order.
    '''
    _inherit = 'account.invoice'

    lsv_sent = fields.Boolean('LSV Payment File Sent?', default=False)
    lsv_sent_date = fields.Datetime('LSV Payment File Sending Date')

    dd_sent = fields.Boolean('DD Payment File Sent?', default=False)
    dd_sent_date = fields.Datetime('DD Payment File Sending Date')

    @api.multi
    def cancel_payment_lines(self):
        ''' This function simply finds related payment lines and move them
            in a new payment order.
        '''
        mov_line_obj = self.env['account.move.line']
        pay_line_obj = self.env['payment.line']
        pay_order_obj = self.env['payment.order']
        active_ids = self.env.context.get('active_ids')
        move_ids = self.browse(active_ids).mapped('move_id.id')
        move_line_ids = mov_line_obj.search([('move_id', 'in', move_ids)]).ids
        pay_lines = pay_line_obj.search([('move_line_id',
                                          'in', move_line_ids)])
        if not pay_lines:
            raise exceptions.Warning(_('No payment line found !'))

        old_pay_order = pay_lines[0].order_id
        vals = {
            'date_created': old_pay_order.date_created,
            'date_prefered': old_pay_order.date_prefered,
            'payment_order_type': old_pay_order.payment_order_type,
            'mode': old_pay_order.mode.id,
        }

        pay_order = pay_order_obj.create(vals)
        pay_order.signal_workflow('cancel')
        pay_lines.write({'order_id': pay_order.id})
        return pay_order

    @api.multi
    def _get_payment_mode_for_dd(self):
        ''' Gets the payment mode which is set to be used for DD payments,
            as set in the company associated to the invoice received.
        '''
        for invoice in self:
            return invoice.company_id.dd_payment_mode

    @api.multi
    def _get_payment_mode_for_lsv(self):
        ''' Gets the payment mode which is set to be used for LSV payments,
            as set in the company associated to the invoice received.
        '''
        for invoice in self:
            return invoice.company_id.lsv_payment_mode

    @api.multi
    def _get_company(self):
        ''' Gets the company associated to the invoice received.
        '''
        for invoice in self:
            return invoice.company_id

    @api.multi
    def _check_allowed_payment_types(self, payment_type):
        if payment_type not in ('dd', 'lsv'):
            error_message = _("Type '{0}' is not allowed. Allowed types are "
                              "'dd' and 'lsv'.").format(payment_type)
            raise exceptions.ValidationError(error_message)

    @api.model
    def _send_payment_file_by_email(self, email_address, file_content,
                                    payment_order, payment_type):
        ''' Sends an email to the indicated email address, and attach a text
            file with the contents received as parameter.
        '''
        mail_mail_obj = self.env['mail.mail']
        ir_model_data_obj = self.env['ir.model.data']
        ir_attachment_obj = self.env['ir.attachment']
        email_template_obj = self.env['email.template']

        self._check_allowed_payment_types(payment_type)

        try:
            # Generates the email for the current payment order taking
            # as the layout an email.template.
            email_template_xmlid = 'email_template_{0}'.format(payment_type)
            email_template_id = \
                ir_model_data_obj.get_object_reference('l10n_ch_lsv_dd',
                                                       email_template_xmlid)[1]
            email_template = email_template_obj.browse(email_template_id)
            values = email_template_obj.generate_email(email_template.id,
                                                       payment_order.id)
            mail = mail_mail_obj.create(values)

            # Creates the attachment.
            attachment_data = {
                'name': '{0} Payment File'.format(payment_type.upper()),
                'datas_fname': '{0} Payment File'.format(payment_type.upper()),
                'datas': base64.encodestring(file_content),
                'res_model': 'mail.mail',
                'res_id': mail.id,
            }
            attachment = ir_attachment_obj.create(attachment_data)

            # Associates the attachment with the email.
            mail.write({'attachment_ids': [(6, 0, [attachment.id])]})

        except Exception as e:
            raise e

    @api.multi
    def _prepare_payment_file_creation(self, payment_type):
        ''' Prepares for the creation of a payment file of either type
            LSV or DD. It creates a payment.order, and as many
            account.banking.mandate as different res.partners we have.
            Then, fills each account.banking.mandate with as many
            payment.lines as invoices that partner has from the list
            of invoices that we have received (in 'self').

            Returns the payment.order that was created, and which
            links all the structures created: a payment.line indicates
            the payment.order and also its account.banking.mandate.
        '''
        now = datetime.now()
        now_date_str = now.strftime(DEFAULT_SERVER_DATE_FORMAT)
        banking_mandate_obj = self.env['account.banking.mandate']
        payment_order_obj = self.env['payment.order']
        payment_line_obj = self.env['payment.line']

        self._check_allowed_payment_types(payment_type)

        # Creates the payment order for this payment method.
        if payment_type == 'lsv':
            payment_mode_id = self._get_payment_mode_for_lsv().id
        else:  # if payment_type == 'dd':
            payment_mode_id = self._get_payment_mode_for_dd().id
        payment_order_id = \
            payment_order_obj.create({'user_id': SUPERUSER_ID,
                                      'date_prefered': 'due',
                                      'mode': payment_mode_id,
                                      })

        # In order to reduce the quantity of account.banking.mandate
        # created, we create just one per res.partner.
        partner_ids = set()
        for invoice in self:
            partner_ids.add(invoice.partner_id)

        for partner in partner_ids:

            # Creates the account.banking.mandate for the bank account
            # of the current partner.
            if payment_type == 'lsv':
                partner_bank_id = partner.lsv_bank_account_id.id
            else:  # if payment_type == 'dd':
                partner_bank_id = partner.dd_bank_account_id.id
            banking_mandate_id = \
                banking_mandate_obj.create({'partner_bank_id': partner_bank_id,
                                            'signature_date': now_date_str,
                                            })

            # Gets the invoices which correspond to this res.partner, and for
            # each of them creates a payment.line with the amount paid on it.
            invoice_ids = self.search([('id', 'in', self.ids),
                                       ('partner_id', '=', partner.id),
                                       ])
            for invoice in invoice_ids:
                communication_text = 'For Invoice {0}.'.format(invoice.number)
                company = self._get_company()
                company_currency = company.currency_id
                payment_line_vals = {
                    'order_id': payment_order_id.id,
                    'partner_id': partner.id,
                    'bank_id': partner_bank_id,
                    'communication': communication_text,
                    'state': 'normal',
                    'mandate_id': banking_mandate_id.id,
                    'amount_currency': invoice.amount_total,
                    'currency': invoice.currency_id.id,
                    'company_currency': company_currency.id,
                    'company_id': company.id,
                    'move_line_id': False,
                }
                payment_line_obj.create(payment_line_vals)

            # Validates the banking mandate.
            banking_mandate_id.validate()

        return payment_order_id

    @api.multi
    def _send_dd(self, dd_email_address):
        ''' All the invoices received must be from the same res.company.
        '''
        now_str = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        dd_export_wizard_obj = self.env['post.dd.export.wizard']

        payment_order = self._prepare_payment_file_creation('dd')

        # Generates the DD file for the generated payment order.
        company = self._get_company()
        dd_export_wizard = dd_export_wizard_obj.\
            with_context({'active_id': payment_order.id}).\
            create({'currency': company.dd_currency})
        file_content, properties = \
            dd_export_wizard._generate_dd_file_content(payment_order)

        # Sends the DD file by email as an attachment.
        self._send_payment_file_by_email(dd_email_address, file_content,
                                         payment_order, 'dd')

        # Marks the invoice as having been 'exported' to DD.
        for invoice in self:
            invoice.dd_sent = True
            invoice.dd_sent_date = now_str

        return True

    @api.multi
    def _send_lsv(self, lsv_email_address):
        ''' Creates and sends a text file containing the LSV data for
            all the invoices which are received. In order to do it,
            an account.banking.mandate is created per invoice, and all
            those mandates are linked to a payment.order which is used
            to generate the LSV file which will be sent.
        '''
        now_str = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        lsv_export_wizard_obj = self.env['lsv.export.wizard']

        payment_order = self._prepare_payment_file_creation('lsv')

        # Generates the DD file for the generated payment order.
        company = self._get_company()
        lsv_export_wizard = lsv_export_wizard_obj.\
            with_context({'active_id': payment_order.id}).\
            create({'treatment_type': 'P',
                    'currency': company.dd_currency})
        file_content, properties = \
            lsv_export_wizard._generate_lsv_file_content(payment_order)

        # Sends the DD file by email as an attachment.
        self._send_payment_file_by_email(lsv_email_address, file_content,
                                         payment_order, 'lsv')

        # Marks the invoice as having been 'exported' to LSV.
        for invoice in self:
            invoice.lsv_sent = True
            invoice.lsv_sent_date = now_str

        return True

    @api.model
    def _test_send_lsv_dd(self, company):
        ''' Checks if we can send the LSV or DD files now.
            We can send it only once a day, and only on weekdays.
            It attempts to send the files between the timeframe indicated
            in the res.company view, to allow for some delay in the scheduler.
        '''
        # Gets the date of today as the user sees it (i.e. taking into
        # account its time-zone).
        now = fields.Datetime.context_timestamp(company, datetime.now())

        # Gets the cron.job which controls the automated sending.
        ir_model_data_obj = self.env['ir.model.data']
        ir_cron_obj = self.env['ir.cron']
        ir_cron_id = \
            ir_model_data_obj.get_object_reference('l10n_ch_lsv_dd',
                                                   'cronjob_send_lsv_dd')[1]
        ir_cron = ir_cron_obj.browse(ir_cron_id)

        # Gets the date of the last LSV/DD sending, taking into account
        # the time-zone of the user.
        if company.last_lsv_dd_send_date:
            last_lsv_dd_send_date = \
                fields.Datetime.context_timestamp(
                    ir_cron,
                    fields.Datetime.from_string(company.last_lsv_dd_send_date))
        else:
            last_lsv_dd_send_date = False

        # Checks the conditions.
        within_the_send_timeframe = int(company.lsv_dd_send_hour_start) \
            <= now.hour < (int(company.lsv_dd_send_hour_start) + 1)
        test_send_lsv_dd = within_the_send_timeframe and \
            is_weekday(now) and \
            ((not last_lsv_dd_send_date) or \
             is_past_weekday(last_lsv_dd_send_date, now))

        return test_send_lsv_dd

    @api.model
    def send_lsv_dd(self):
        ''' Iterates over all the paid invoices the LSV and DD payment files
            of which has not been sent yet to the addresses indicated in the
            res.company view. Generates a single LSV and/or DD file for all
            the invoices, and sends them to the indicated email addresses
            (but only if those addresses are set).
        '''
        for company in self.env['res.company'].search([]):
            if not self._test_send_lsv_dd(company):
                continue

            # Gets the paid invoices from this company.
            paid_invoices = self.search(
                [('company_id', '=', company.id),
                 ('state', '=', 'paid'),
                 ])

            # Whether to send the LSV payment files.
            if company.lsv_email_address:
                lsv_company_account = company.lsv_bank_account_id

                # Searches for those paid invoices for which their
                # LSD payment file were not yet sent.
                pending_invoices = self.search(
                    [('id', 'in', paid_invoices.ids),
                     ('lsv_sent', '=', False),
                     ('partner_bank_id', '=', lsv_company_account.id),
                     ])
                if pending_invoices:
                    pending_invoices._send_lsv(company.lsv_email_address)

            # Whether to send the DD payment files.
            if company.dd_email_address:
                dd_company_account = company.dd_bank_account_id

                # Searches for those paid invoices for which their
                # DD payment file were not yet sent.
                pending_invoices = self.search(
                    [('id', 'in', paid_invoices.ids),
                     ('dd_sent', '=', False),
                     ('partner_bank_id', '=', dd_company_account.id),
                     ])
                if pending_invoices:
                    pending_invoices._send_dd(company.dd_email_address)

            # Stores the datetime in which the last sending of the payment
            # files took place, and prepares the next execution date
            # of the scheduler.
            company.last_lsv_dd_send_date = fields.Datetime.now()

        return True
