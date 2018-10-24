# Copyright (c) 2018 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, api, fields
from lxml import etree


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    debit_advice_control = fields.Selection(
        [('NOA', 'No Advice'),
         ('SIA', 'Single Advice'),
         ('CND', 'Collective Advice No Details'),
         ('CWD', 'Collective Advice With Details'),
         ], string='Debit Advice Control', required=False,
        help="Can be used to control the debit advice. "
             "The following options are available:\n"
             "• NOA No Advice\n"
             "• SIA Single Advice\n"
             "• CND Collective Advice No Details\n"
             "• CWD Collective Advice With Details\n"
             "If used, then 'Code' must not be present")
    payment_method_code = fields.Char(
        related='payment_mode_id.payment_method_id.code',
        tring='PM Code', readonly=True, store=False)

    @api.model
    def create(self, vals):
        if vals.get('payment_mode_id'):
            payment_mode = \
                self.env['account.payment.mode'].browse(vals['payment_mode_id'])
            if not vals.get('debit_advice_control') and \
                    payment_mode.default_debit_advice_control:
                vals['debit_advice_control'] = \
                    payment_mode.default_debit_advice_control
            if not vals.get('batch_booking') and \
                    payment_mode.default_batch_booking:
                vals['batch_booking'] = payment_mode.default_batch_booking
        return super(AccountPaymentOrder, self).create(vals)

    @api.onchange('payment_mode_id')
    def payment_mode_id_change(self):
        res = super(AccountPaymentOrder, self).payment_mode_id_change()
        self.debit_advice_control = \
            self.payment_mode_id.default_debit_advice_control or None
        self.batch_booking = self.payment_mode_id.default_batch_booking
        return res

    @api.model
    def generate_party_acc_number(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None):
        res = super().generate_party_acc_number(
            parent_node, party_type, order, partner_bank, gen_args,
            bank_line=bank_line)
        assert order in ('B', 'C'), "Order can be 'B' or 'C'"
        if res and order == 'B' and self.debit_advice_control:
            party_account = parent_node.find('%sAcct' % party_type)
            party_tp = party_account.find('Tp')
            if party_tp:
                party_account.remove(party_tp)
            party_tp = etree.SubElement(party_account, 'Tp')
            party_proprietary = etree.SubElement(
                party_tp, 'Prtry')
            party_proprietary.text = self.debit_advice_control
        return res
    
