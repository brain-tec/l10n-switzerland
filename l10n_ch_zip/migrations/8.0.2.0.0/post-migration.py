# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Mathias Neef
#    Copyright 2015 copadoMEDIA UG
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

"""
In previews versions the states in Switzerland are created within this module.
Now they are seperated in extra module l10n_ch_states. This modul now depends
on l10n_ch_states.
"""

import logging

logger = logging.getLogger('upgrade')


def migrate(cr, version):
    if not version:
        logger.info("No migration necsessary for l10n_ch_zip")
        return

    logger.info("Migrating l10n_ch_zip from version %s", version)

    cr.execute("SELECT name, res_id "
               "FROM ir_model_data "
               "WHERE module = 'l10n_ch_zip' "
               "AND model = 'res.country.state';")

    for name, res_id in cr.fetchall():

        old_state = res_id

        cr.execute("SELECT res_id "
                   "FROM ir_model_data "
                   "WHERE name = %s "
                   "AND module = 'l10n_ch_states';", (name,))

        new_state = cr.fetchone()

        logger.info(
            "Updating state_id from id %s to id %s",
            old_state, new_state
        )

        cr.execute("UPDATE res_partner "
                   "SET state_id = %s"
                   "WHERE state_id = %s", (new_state, old_state))

        cr.execute("UPDATE res_better_zip "
                   "SET state_id = %s "
                   "WHERE state_id = %s;", (new_state, old_state))

        #check if bt_swissdec is not in state 'uninstalled' -> bt_swissdec is installed
        cr.execute("SELECT id "
                   "FROM ir_module_module "
                   "WHERE name = 'bt_swissdec' "
                   "AND state != 'uninstalled';")
        bt_swissdec_installed = cr.fetchone()
        #do some updates if bt_swissdec is installed
        if bt_swissdec_installed:
            print 'TRUE bt_swissdec_installed'
            print 'update state_id from res_company_fak'
            cr.execute("UPDATE res_company_fak "
                   "SET state_id = %s "
                   "WHERE state_id = %s;", (new_state, old_state))
            print 'update state_id from res_company_bur'
            cr.execute("UPDATE res_company_bur "
                   "SET state_id = %s "
                   "WHERE state_id = %s;", (new_state, old_state))
            print 'update state_id from res_company_qst'
            cr.execute("UPDATE res_company_qst "
                   "SET state_id = %s "
                   "WHERE state_id = %s;", (new_state, old_state))
            print 'update spesen_stv_state_id from hr_employee_year'
            cr.execute("UPDATE hr_employee_year "
                   "SET spesen_stv_state_id = %s "
                   "WHERE spesen_stv_state_id = %s;", (new_state, old_state))
            print 'update privat_fz_state_id from hr_employee_year'
            cr.execute("UPDATE hr_employee_year "
                   "SET privat_fz_state_id = %s "
                   "WHERE privat_fz_state_id = %s;", (new_state, old_state))
            print 'update verkehrswert_stv_ok_state_id from hr_employee_year'
            cr.execute("UPDATE hr_employee_year "
                   "SET verkehrswert_stv_ok_state_id = %s "
                   "WHERE verkehrswert_stv_ok_state_id = %s;", (new_state, old_state))
            print 'update qst_state_id from hr_employee_calculationparameter_qst'
            cr.execute("UPDATE hr_employee_calculationparameter_qst "
                   "SET qst_state_id = %s "
                   "WHERE qst_state_id = %s;", (new_state, old_state))
            print 'update partner_working_state_id from hr_employee_calculationparameter_qst'
            cr.execute("UPDATE hr_employee_calculationparameter_qst "
                   "SET partner_working_state_id = %s "
                   "WHERE partner_working_state_id = %s;", (new_state, old_state))
            print 'update spesen_stv_state_id from res_company_year'
            cr.execute("UPDATE res_company_year "
                   "SET spesen_stv_state_id = %s "
                   "WHERE spesen_stv_state_id = %s;", (new_state, old_state))
            print 'update privat_fz_state_id from res_company_year'
            cr.execute("UPDATE res_company_year "
                   "SET privat_fz_state_id = %s "
                   "WHERE privat_fz_state_id = %s;", (new_state, old_state))
            print 'update verkehrswert_stv_ok_state_id from res_company_year'
            cr.execute("UPDATE res_company_year "
                   "SET verkehrswert_stv_ok_state_id = %s "
                   "WHERE verkehrswert_stv_ok_state_id = %s;", (new_state, old_state))

        cr.execute("DELETE FROM res_country_state "
                   "WHERE id = %s;", (old_state,))

    logger.info(
        "Delete old states from ir_model_data"
    )

    cr.execute("DELETE FROM ir_model_data "
               "WHERE module = 'l10n_ch_zip' "
               "AND model = 'res.country.state'")
