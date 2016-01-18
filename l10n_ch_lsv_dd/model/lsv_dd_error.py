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

from openerp import models, api, fields, sql_db


class LsvDdError(models.Model):
    ''' This is used to keep a visual record of the pending errors that
        happened while automatising the generation and sending of the
        LSV/DD payment files. Otherwise, the user would need to have
        a look at the log.
    '''
    _name = 'lsv.dd.error'
#     _log_access = False
# 
#     create_uid = fields.Integer(
#         'Create UID',
#         help='We make this table not to have any relation, so that it can be '
#              'used as a log table. In this case, this field stores the UID '
#              'which logged the error.'
#     )

    date_error = fields.Datetime(
        'Date', help='Date in which the error happened.'
    )

    error_message = fields.Text(
        'Error Message', help='The content of the error message.'
    )

    payment_file_type = fields.Selection(
        [('lsv', 'LSV'), ('dd', 'DD')],
        string='Type of Payment File',
        help='The type of payment file which caused the error: LSV or DD.'
    )

    @api.model
    def add_error(self, error_message, payment_file_type):
        ''' Adds an error message to the entry.
        '''
        # Creates a new cursor so that the exception does not roll-back the
        # writing of the error message.
        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        original_uid = self.env.uid
        original_context = self.env.context

        with api.Environment.manage():
            self.env = api.Environment(new_cr, original_uid, original_context)
            try:
                self.create({'date_error': fields.Datetime.now(),
                             'error_message': error_message,
                             'payment_file_type': payment_file_type,
#                              'create_uid': original_uid,
                             })
            finally:
                self.env.cr.commit()
                self.env.cr.close()

        return True
