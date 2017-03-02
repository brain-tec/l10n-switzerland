# b-*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 brain-tec AG (http://www.braintec-group.com)
# All Right Reserved
#
# See LICENSE file for full licensing details.
##############################################################################
from . import models

from openerp import SUPERUSER_ID
from logging import getLogger
_logger = getLogger(__name__)


def pre_init(cr):
    _logger.info('l10n_ch_states -> pre_init(%s)' % (cr))

    cr.execute("""SELECT id, res_id, name
                      FROM ir_model_data
                      WHERE model = 'res.country.state' and module = 'bt_swissdec' and name != 'EX';""")
    res = cr.fetchall()
    for model_field in res:
        print 'model_field: ', model_field
        cr.execute("""SELECT code
                              FROM res_country_state
                              WHERE id = %(id)s;""" % ({'id': model_field[1]}))
        res_code = cr.fetchone()
        print 'res_code: ', res_code
        print 'res_code[0]: ', res_code[0]
        cr.execute("""update ir_model_data
                      set module = 'l10n_ch_states',
                          name = '%(name_new)s'
                      where id = %(id)s;""" % ({'name_new': 'state_' + res_code[0],
                                                'id': model_field[0]}))
