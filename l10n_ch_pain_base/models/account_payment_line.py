# -*- coding: utf-8 -*-
# © 2016 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class AccountPaymentLine(models.Model):
    _inherit = 'payment.line'

    local_instrument = fields.Selection(
        [('CH01', 'CH01 (BVR)')])
    communication_type = fields.Selection([('bvr', 'BVR')])

    def invoice_reference_type2communication_type(self):
        res = super(AccountPaymentLine, self).\
            invoice_reference_type2communication_type()
        res['bvr'] = 'bvr'
        return res
