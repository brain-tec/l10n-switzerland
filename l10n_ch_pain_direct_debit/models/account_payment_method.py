# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountPaymentMethod(models.Model):
    _inherit = 'payment.mode'

    # pain_version = fields.Selection(selection_add=[
    #     ('pain.008.001.02.ch.01',
    #      'pain.008.001.02.ch.01 (direct debit in Switzerland)'),
    #     ])

    @api.multi
    def get_xsd_file_path(self):
        self.ensure_one()
        painv = self.type.code
        if painv[:-2] == 'pain.008.001.02.ch.':
            path = 'l10n_ch_pain_direct_debit/data/%s.xsd' % painv
            return path
        return super(AccountPaymentMethod, self).get_xsd_file_path()
