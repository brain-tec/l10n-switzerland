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

from openerp import models
from .export_sdd import PAIN_SEPA_DD_CH


class DDExportWizard(models.TransientModel):
    _inherit = 'post.dd.export.wizard'

    def _generate_dd_filecontent(self, pmt_order):
        if pmt_order.line_ids and pmt_order.mode.type.code == PAIN_SEPA_DD_CH:
            wizard = self.env['banking.export.sdd.wizard'].with_context(active_ids=pmt_order.ids).create({})
            properties = {}
            wizard.generate_xml_ch_dd_file()
            return decodestring(wizard.file), properties
        return super(DDExportWizard, self)._generate_dd_file_content(pmt_order)
