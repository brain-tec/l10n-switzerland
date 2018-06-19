##############################################################################
#
#    Part of Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2018 brain-tec AG (http://www.braintec-group.com)
#    @author Simon Schmid <simon.schmid@braintec-group.com>
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

from base64 import decodestring

from openerp import models, fields
from .export_sdd import PAIN_SEPA_DD_CH


class LSVExportWizard(models.TransientModel):
    _inherit = 'lsv.export.wizard'

    filetype = fields.Selection([
        ('lsv', 'LSV Text File'),
        ('xml', 'pain.008 XML File')
    ], default='xml', string="Filetype", required=True)

    def _generate_lsv_file_content(self, pmt_order):
        """
        override lsv_export_wizard to add support for pain.008
        files
        TODO: add field and view to select fileformat
        :param pmt_order:
        :return:
        """
        if pmt_order.line_ids and self.filetype == 'xml' and pmt_order.mode.type.code == PAIN_SEPA_DD_CH:
            wizard = self.env['banking.export.sdd.wizard'].with_context(active_ids=pmt_order.ids).create({})
            properties = {'seq_nb': len(pmt_order.line_ids)}
            wizard.generate_xml_ch_dd_file()
            return decodestring(wizard.file), properties
        return super(LSVExportWizard, self)._generate_lsv_file_content(pmt_order)

    def _create_lsv_export(self, p_o_ids, total_amount,
                           properties, file_content):

        r = super(LSVExportWizard, self)._create_lsv_export(p_o_ids, total_amount, properties, file_content)
        if self.filetype == 'xml':
            r.filename = r.filename.replace('.lsv', '.xml')
        return r
