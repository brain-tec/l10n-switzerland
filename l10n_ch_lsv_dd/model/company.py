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
from openerp import models, fields


class ResCompany(models.Model):
    ''' Overrides it to add the email addresses where to send the LSV/DD files
        every time they are collected by the cron.job.
    '''

    _inherit = 'res.company'

    lsv_email_address = fields.Char(
        'LSV Email Address',
        help='Email address where to send the LSV files.'
    )

    dd_email_address = fields.Char(
        'DD Email Address',
        help='Email address where to send the DD files.'
    )
