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
from openerp import models, api


class PaymentSlip(models.Model):
    _inherit = 'l10n_ch.payment_slip'

    @api.model
    def _can_generate(self, move_line):
        ''' This method is overwritten to extend the list of types of
            bank accounts which generate a BVR. In the default
            implementation it is only generated for BVR and BV,
            but we want also for type IBAN.
        '''
        invoice = move_line.invoice
        if not invoice:
            return False
        return (invoice.partner_bank_id and
                invoice.partner_bank_id.state in ('bvr', 'bv', 'iban'))
