##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    Copyright (C) 2017-2018 brain-tec AG (http://www.braintec-group.com)
#    @author: Cyril Sester <cyril.sester@outlook.com>
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

from lxml import etree

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.tools.float_utils import float_round

ACCEPTED_PAIN_FLAVOURS = (
    'pain.008.001.02.ch.01',
    'pain.008.001.03.ch.01',
    'pain.008.001.02.ch.03',
    'pain.008.001.03.ch.03'
)
PAIN_SEPA_DD_CH = 'pain.008.001.02.ch.03'


def xml_remove_tag(root, tag):
    el = root.find(".//%s" % tag)
    if el is not None:
        el.getparent().remove(el)
    else:
        raise ValueError('element %s not found' % tag)
    return el


class BankingExportSddWizard(models.TransientModel):
    _inherit = 'banking.export.sdd.wizard'
    _description = 'Export SEPA Direct Debit File'

    bank_line_ids = fields.One2many(related="payment_order_ids.line_ids")
    company_partner_bank_id = fields.Many2one(
        related='payment_order_ids.mode.bank_id', string='Company Bank Account',
        readonly=True)

    @api.multi
    def generate_payment_file(self):
        """ Overridden to consider LSV and DD.
            Returns (payment file as string, filename)
        """
        self.ensure_one()

        payment_method_code = self.payment_method_id.code
        pain_flavor = self.payment_order_ids[0].mode.type.code
        pain_flavor = self.payment_order_ids[0].mode.type.code
        # We are going to re-use the wizard, thus we pass the
        # active_ids through the context.
        new_context = self._context.copy()
        new_context.update({'active_ids': self.ids})

        # We use as the currency that of the bank account, or
        # that of the journal, or that of the company.
        currency = self.company_partner_bank_id.currency_id or \
                   self.journal_id.currency_id or \
                   self.journal_id.company_id.currency_id or \
                   False

        if payment_method_code == 'lsv':
            lsv_treatment_type = \
                self.payment_method_id.lsv_treatment_type or 'T'
            lsv_export_wizard = self.env['lsv.export.wizard']. \
                create({'treatment_type': lsv_treatment_type,
                        'currency': currency.name,
                        })
            lsv_export_wizard.with_context(new_context).generate_lsv_file()
            file_contents = base64.decodestring(lsv_export_wizard.file)
            res = file_contents, lsv_export_wizard.filename

        elif payment_method_code == 'postfinance.dd' and not pain_flavor:
            dd_export_wizard = self.env['post.dd.export.wizard']. \
                create({'currency': currency.name})
            dd_export_wizard.with_context(new_context).generate_dd_file()
            file_contents = base64.decodestring(dd_export_wizard.file)
            res = file_contents, dd_export_wizard.filename

        elif payment_method_code == 'sepa.ch.dd' and \
                pain_flavor == 'pain.008.001.02.ch.03':
            file_content, file_name = self.generate_xml_ch_dd_file()
            res = file_content, file_name

        else:
            res = super(BankingExportSddWizard, self).generate_payment_file()

        return res

    @api.multi
    def generate_pain_nsmap(self):
        """ Overridden to add the new pain.008.001.03.ch.01 pain version
        to the list.
        """
        self.ensure_one()
        nsmap = {
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            # None: 'http://www.six-interbank-clearing.com/de/'\
            #              '%s.xsd' % pain_flavor,
        }
        # nsmap = super(BankingExportSddWizard, self).generate_pain_nsmap()
        pain_flavor = self.payment_order_ids[0].mode.type.code
        if pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            nsmap[None] = 'http://www.six-interbank-clearing.com/de/%s.xsd' % \
                          pain_flavor
        return nsmap

    @api.multi
    def generate_pain_attrib(self):
        """ Overridden to add the new pain.008.001.03.ch.01 pain version
            to the list.
        """
        self.ensure_one()
        pain_flavor = self.payment_order_ids[0].mode.type.code
        if pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            attrib = {
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                    "http://www.six-interbank-clearing.com/de/%s.xsd  %s.xsd" %
                    (pain_flavor, pain_flavor)
            }
        else:
            attrib = super(BankingExportSddWizard, self).generate_pain_attrib()
        return attrib

    @api.model
    def _must_have_initiating_party(self, gen_args):
        """ Overridden because of pain.008.001.03.ch.01, where we have
            to provide the Initiating Party Identifier.
        """
        if gen_args.get('pain_flavor') == PAIN_SEPA_DD_CH:
            return True
        else:
            return super(BankingExportSddWizard, self). \
                _must_have_initiating_party(gen_args)

    @api.model
    def generate_group_header_block(self, parent_node, gen_args):
        """ Overridden because of pain.008.001.03.ch.01.
        """
        group_header, nb_of_transactions_a, control_sum_a = \
            super(BankingExportSddWizard, self).generate_group_header_block(
                parent_node, gen_args)

        if gen_args.get('pain_flavor') == PAIN_SEPA_DD_CH:
            # It removes the tag <Issr> and its subtree.
            subtrees = group_header.xpath('//Issr')
            for subtree in subtrees:
                subtree.getparent().remove(subtree)

        return group_header, nb_of_transactions_a, control_sum_a

    @api.model
    def generate_initiating_party_block(self, parent_node, gen_args):
        if gen_args.get('pain_flavor') != PAIN_SEPA_DD_CH:
            return super(BankingExportSddWizard, self).generate_initiating_party_block(parent_node, gen_args)

        my_company_name = self._prepare_field(
            'Company Name',
            'self.payment_order_ids[0].mode.bank_id.partner_id.name',
            {'self': self}, gen_args.get('name_maxsize'), gen_args=gen_args)
        initiating_party_1_8 = etree.SubElement(parent_node, 'InitgPty')
        initiating_party_name = etree.SubElement(initiating_party_1_8, 'Nm')
        initiating_party_name.text = my_company_name

        bank = self.payment_order_ids[0].mode.bank_id
        initiating_party_identifier = \
            bank.post_dd_identifier or bank.lsv_identifier
        iniparty_id = etree.SubElement(initiating_party_1_8, 'Id')
        iniparty_org_id = etree.SubElement(iniparty_id, 'OrgId')
        iniparty_org_other = etree.SubElement(iniparty_org_id, 'Othr')
        iniparty_org_other_id = etree.SubElement(iniparty_org_other, 'Id')

        # identifier for either CHTA or CHDD
        iniparty_org_other_id.text = initiating_party_identifier

        return True

    @api.model
    def generate_start_payment_info_block(
            self, parent_node, payment_info_ident,
            priority, local_instrument, sequence_type, requested_date,
            eval_ctx, gen_args):
        """ This is overridden because pain.008.001.03.ch.01 uses a different
            XML structure. The code is basically the same that can be found
            on the module account_banking_pain_base's method
            generate_start_payment_info_block().
        """

        if gen_args.get('pain_flavor') == PAIN_SEPA_DD_CH:
            payment_info = etree.SubElement(parent_node, 'PmtInf')

            # <PmtInf>/  <PmtInfId>
            payment_info_identification = \
                etree.SubElement(payment_info, 'PmtInfId')
            payment_info_identification.text = self._prepare_field(
                'Payment Information Identification',
                payment_info_ident, eval_ctx, 35, gen_args=gen_args)

            # <PmtInf>/  <PmtMtd>
            payment_method = etree.SubElement(payment_info, 'PmtMtd')
            payment_method.text = gen_args['payment_method']

            # These two parameters are set to False only to avoid changing the
            # return of the method we are overriding.
            nb_of_transactions = False
            control_sum = False

            # <PmtInf>/  <PmtTpInf>
            payment_type_info = etree.SubElement(payment_info, 'PmtTpInf')
            if priority and gen_args['payment_method'] != 'DD':
                instruction_priority = \
                    etree.SubElement(payment_type_info, 'InstrPrty')
                instruction_priority.text = priority

            # <PmtInf>/<PmtTpInf>/  <SvcLvl>
            service_level = etree.SubElement(payment_type_info, 'SvcLvl')

            # <PmtInf>/<PmtTpInf>/<SvcLvl>/  <Prtry>
            prtry_value = None
            # if self.company_partner_bank_id.state in ('postal', 'iban'):
            service_level_value = etree.SubElement(service_level, 'Prtry')
            if self.company_partner_bank_id.state == 'postal' or \
                    self.company_partner_bank_id.bank.bic == 'POFICHBEXXX':
                prtry_value = 'CHDD'
            else:
                prtry_value = 'CHTA'
            gen_args['service_level'] = prtry_value
            service_level_value.text = prtry_value

            # <PmtInf>/<PmtTpInf>/  <LclInstrm>
            local_instrument_root = etree.SubElement(payment_type_info,
                                                     'LclInstrm')
            # if self.company_partner_bank_id.state in ('postal', 'iban'):
            local_instr_value = \
                etree.SubElement(local_instrument_root, 'Prtry')
            if not self.company_partner_bank_id.partner_id.is_company \
                    or prtry_value == 'CHTA':
                local_instrument = 'LSV+'
            else:
                local_instrument = 'DDCOR1'
            local_instr_value.text = local_instrument

            # <PmtInf>/<PmtTpInf>/  <ReqdColltnDt>
            requested_date_node = etree.SubElement(payment_info,
                                                   'ReqdColltnDt')
            requested_date_node.text = requested_date

        else:
            payment_info, nb_of_transactions, control_sum = \
                super(BankingExportSddWizard, self). \
                    generate_start_payment_info_block(
                    parent_node, payment_info_ident,
                    priority, local_instrument, sequence_type,
                    requested_date, eval_ctx, gen_args)

        return payment_info, nb_of_transactions, control_sum

    @api.model
    def generate_party_acc_number(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None):
        """ Overridden for pain.008.001.03.ch.01.
        """
        if gen_args.get('pain_flavor') == PAIN_SEPA_DD_CH:
            # <CdtrAcct>
            party_account = etree.SubElement(parent_node,
                                             '%sAcct' % party_type)
            party_account_id = etree.SubElement(party_account, 'Id')
            # use iban if provided. Postfinance may provide a non iban conform
            # account number (9 digits. Thus we have to check and use the correct identification
            # format.
            acc = partner_bank.acc_number.replace('-', '').replace(' ', '')
            needs_iban = party_type == 'Cdtr'
            if partner_bank.is_iban_valid(partner_bank.acc_number):
                party_account_iban = etree.SubElement(party_account_id, 'IBAN')
                party_account_iban.text = acc
            elif not needs_iban and len(acc) == 9:
                othr = etree.SubElement(party_account_id, 'Othr')
                othr_id = etree.SubElement(othr, 'Id')
                othr_id.text = acc
            else:
                raise Warning("The proivded bank account number %s is invalid." % partner_bank.acc_number)
            res = True

        else:
            res = super(BankingExportSddWizard, self).generate_party_acc_number(
                parent_node, party_type, order, partner_bank, gen_args,
                bank_line)

        return res

    @api.model
    def generate_party_agent(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None, *args):
        """ Overridden for pain.008.001.03.ch.01.
        """
        # in order to stay compatible with v8 account_banking
        # we have to check the arguments, because they are different
        # in the super method.
        if isinstance(gen_args, dict) and gen_args.get('pain_flavor') == PAIN_SEPA_DD_CH:
            party_agent = etree.SubElement(parent_node, '%sAgt' % party_type)
            party_agent_institution = \
                etree.SubElement(party_agent, 'FinInstnId')

            # <CdtrAgt>/<FinInstnId>/  <ClrSysMmbId>
            party_agent_clearing = \
                etree.SubElement(party_agent_institution, 'ClrSysMmbId')
            party_agent_clearing_identification = \
                etree.SubElement(party_agent_clearing, 'MmbId')
            party_agent_clearing_identification.text = \
                partner_bank.bank.clearing.zfill(5)

            if gen_args.get('service_level') == 'CHTA':
                # <CdtrAgt>/<FinInstnId>/  <Othr>
                party_agent_other = \
                    etree.SubElement(party_agent_institution, 'Othr')
                party_agent_other_identification = \
                    etree.SubElement(party_agent_other, 'Id')
                party_agent_other_identification.text = partner_bank.esr_party_number \
                                                        or 'NOTPROVIDED'
            res = True

        else:
            res = super(BankingExportSddWizard, self).generate_party_agent(
                parent_node, party_type, order, partner_bank, gen_args,
                bank_line, *args)

        return res

    @api.model
    def generate_party_block(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None, *args, **kwargs):
        """ This is overridden because pain.008.001.03.ch.01 uses a
            different XML structure. The code is basically the same that
            can be found on the module account_banking_pain_base's method
            generate_party_block().
        """
        # in order to stay compatible with v8 account_banking
        # we have to check the arguments, because they are different
        # in the super method.
        if isinstance(gen_args, dict) and gen_args.get('pain_flavor') == PAIN_SEPA_DD_CH:

            # <Cdtr>
            party = etree.SubElement(parent_node, party_type)

            if party_type == 'Cdtr':
                party_type_label = 'Creditor'
            elif party_type == 'Dbtr':
                party_type_label = 'Debtor'

            name = 'partner_bank.partner_id.name'
            eval_ctx = {'partner_bank': partner_bank}
            party_name = self._prepare_field('%s Name' % party_type_label,
                                             name, eval_ctx,
                                             gen_args.get('name_maxsize'),
                                             gen_args=gen_args)

            # <Cdtr>/  <Nm>
            party_nm = etree.SubElement(party, 'Nm')
            party_nm.text = party_name
            partner = partner_bank.partner_id

            if partner.country_id:
                # <Cdtr>/<Nm>/  <PstlAdr>
                postal_address = etree.SubElement(party, 'PstlAdr')

                # <Cdtr>/<Nm>/  <Ctry>
                country = etree.SubElement(postal_address, 'Ctry')
                country.text = self._prepare_field('Country',
                                                   'partner.country_id.code',
                                                   {'partner': partner}, 2,
                                                   gen_args=gen_args)

                # <Cdtr>/<Nm>/  <AdrLine> x2
                if partner.street:
                    adrline1 = etree.SubElement(postal_address, 'AdrLine')
                    adrline1.text = \
                        self._prepare_field('Adress Line1',
                                            'partner.street',
                                            {'partner': partner},
                                            70, gen_args=gen_args)
                if partner.city and partner.zip:
                    adrline2 = etree.SubElement(postal_address, 'AdrLine')
                    adrline2.text = \
                        self._prepare_field('Address Line2',
                                            "partner.zip + ' ' + partner.city",
                                            {'partner': partner}, 70,
                                            gen_args=gen_args)

            # <CdtrAcct>
            self.generate_party_acc_number(parent_node, party_type, order,
                                           partner_bank, gen_args,
                                           bank_line=bank_line)

            if order == 'B':
                self.generate_party_agent(
                    parent_node, party_type, order, partner_bank, gen_args,
                    bank_line=bank_line)

            res = True

        else:
            res = super(BankingExportSddWizard, self).generate_party_block(parent_node, party_type, order, partner_bank,
                                                                           gen_args,
                                                                           bank_line, *args, **kwargs)

        return res

    @api.model
    def generate_remittance_info_block(self, parent_node, line, gen_args):
        super(BankingExportSddWizard, self).generate_remittance_info_block(parent_node, line, gen_args)
        if gen_args.get('pain_flavor') == PAIN_SEPA_DD_CH \
                and gen_args.get('service_level') == 'CHTA':
            remittance_info_2_91 = parent_node.find("./RmtInf")

            xml_remove_tag(remittance_info_2_91, "Ustrd")

            remittance_info_structured_2_100 = etree.SubElement(
                remittance_info_2_91, 'Strd')
            creditor_ref_information_2_120 = etree.SubElement(
                remittance_info_structured_2_100, 'CdtrRefInf')
            creditor_ref_info_type_2_121 = etree.SubElement(
                creditor_ref_information_2_120, 'Tp')

            creditor_ref_info_type_or_2_122 = etree.SubElement(
                creditor_ref_info_type_2_121, 'CdOrPrtry')
            creditor_ref_info_type_code_2_123 = etree.SubElement(
                creditor_ref_info_type_or_2_122, 'Prtry')
            creditor_reference_2_126 = etree.SubElement(
                creditor_ref_information_2_120, 'Ref')
            creditor_ref_info_type_code_2_123.text = 'ESR'
            creditor_reference_2_126.text = \
                self._prepare_field(
                    'Creditor Structured Reference',
                    'line.communication', {'line': line}, 35,
                    gen_args=gen_args)
            return True

    @api.multi
    def generate_dd_transaction_information(self, parent_node, partner_bank,
                                            lines, gen_args):
        """ Takes portions of the code that is inside
            account_banking_sepa_direct_debit's generate_payment_file().
            Implements the //<DrctDbtTxInf> part of the XML
            for pain.008.001.03.ch.01.
        """
        for line in lines:
            dd_transaction_info = etree.SubElement(
                parent_node, 'DrctDbtTxInf')
            payment_identification = etree.SubElement(
                dd_transaction_info, 'PmtId')
            instruction_identification = etree.SubElement(
                payment_identification, 'InstrId')
            instruction_identification.text = self._prepare_field(
                'Intruction Identification', 'line.name',
                {'line': line}, 35, gen_args=gen_args)
            end2end_identification = etree.SubElement(
                payment_identification, 'EndToEndId')
            end2end_identification.text = self._prepare_field(
                'End to End Identification', 'line.name',
                {'line': line}, 35, gen_args=gen_args)
            currency_name = self._prepare_field(
                'Currency Code', 'line.currency.name',
                {'line': line}, 3, gen_args=gen_args)
            instructed_amount = etree.SubElement(
                dd_transaction_info, 'InstdAmt', Ccy=currency_name)
            instructed_amount.text = '%.2f' % line.amount_currency

            # .../  <DbtrAgt>
            ori_debtor_agent = etree.SubElement(
                dd_transaction_info, 'DbtrAgt')
            ori_debtor_agent_institution = etree.SubElement(
                ori_debtor_agent, 'FinInstnId')
            ori_debtor_agent_institution_clearing = etree.SubElement(
                ori_debtor_agent_institution, 'ClrSysMmbId')
            ori_debtor_agent_institution_clearing_identification = \
                etree.SubElement(ori_debtor_agent_institution_clearing,
                                 'MmbId')
            ori_debtor_agent_institution_clearing_identification.text = \
                partner_bank.bank.clearing.zfill(5)

            # .../  <Dbtr>
            self.generate_party_block(
                dd_transaction_info, 'Dbtr', 'C',
                line.bank_id, gen_args, line)

            # .../  <DbtrAcct>
            dbtr_acct = etree.Element("DbtrAcct")
            dbtr_acct_id = etree.SubElement(dbtr_acct, "Id")
            dbtr_acct_iban = etree.SubElement(dbtr_acct_id, "IBAN")
            dbtr_acct_iban.text = partner_bank.acc_number.replace(' ', '')

            # .../  <RmtInf>
            self.generate_remittance_info_block(dd_transaction_info,
                                                line, gen_args)

        return True

    @api.multi
    def generate_xml_ch_dd_file(self):
        """ Generates the XML Direct Debit file for pain.008.001.03.ch.01.
        """
        self.ensure_one()

        pay_method = self.payment_order_ids[0].mode
        xsd_file = pay_method.get_xsd_file_path()
        gen_args = {
            'bic_xml_tag': 'BIC',
            'name_maxsize': 70,
            'convert_to_ascii': True,  # pay_method.convert_to_ascii,
            'payment_method': 'DD',
            'file_prefix': 'sdd_',
            'pain_flavor': PAIN_SEPA_DD_CH,
            'pain_xsd_file': xsd_file,
        }

        # Creates the container tag, with the schema and so on.
        nsmap = self.generate_pain_nsmap()
        attrib = self.generate_pain_attrib()
        xml_root = etree.Element('Document', nsmap=nsmap, attrib=attrib)

        # Creates the root tag <CstmrDrctDbtInitn> having the content.
        root = etree.SubElement(xml_root, 'CstmrDrctDbtInitn')

        # Creates the header tag <GrpHdr>
        group_header, nb_of_transactions_a, control_sum_a = \
            self.generate_group_header_block(root, gen_args)

        # The following code is very much inspired from
        # that of account_banking_sepa_credit_transfer.

        lines_per_group = {}
        for line in self.bank_line_ids:
            key = (line.date, line.priority, line.local_instrument)
            lines_per_group.setdefault(key, []).append(line)

        for (req_date, prio, local_inst), lines in lines_per_group.items():
            # Creates the tags <PmtInf>/  [<PmtInfId>, <PmtMtd>,
            # <PmtTpInf>, <ReqdColltnDt>]
            req_date = req_date or fields.Date.today()
            payment_info, nb_of_transactions_b, control_sum_b = \
                self.generate_start_payment_info_block(
                    root,
                    "self.payment_order_ids[0].reference + '-' "
                    "+ requested_date.replace('-', '')  + '-' + priority + "
                    "'-' + local_instrument",
                    prio, local_inst, False, req_date, {
                        'self': self,
                        'priority': prio,
                        'requested_date': req_date,
                        'local_instrument': local_inst or 'NOinstr',
                    }, gen_args)

            # Creates the tags <PmtInf>/  [<Cdtr>, <CdtrAcct>, <CdtrAgt>]
            self.generate_party_block(payment_info, 'Cdtr', 'B',
                                      self.company_partner_bank_id, gen_args)

            # <PmtInf>/  <CdtrSchmeId>
            creditor_scheme_identification = \
                etree.SubElement(payment_info, 'CdtrSchmeId')

            prty = False
            ident = False
            if gen_args.get('service_level') == 'CHDD':
                prty = 'CHDD'
                ident = 'self.payment_order_ids[0].mode.bank_id.post_dd_identifier'
            else: #CHTA
                prty = 'CHLS'
                ident = 'self.payment_order_ids[0].mode.bank_id.lsv_identifier'
            self.generate_creditor_scheme_identification(
                creditor_scheme_identification,
                ident,
                'SEPA Creditor Identifier', {'self': self}, 'CHDD', gen_args)

            # <PmtInf>/  <DrctDbtTxInf>
            self.generate_dd_transaction_information(
                payment_info, self.company_partner_bank_id, lines, gen_args)

        # It sets the number of transactions, <NbOfTxs>
        nb_of_transactions_a.text = unicode(len(self.bank_line_ids))

        # It sets the check sum, <CtrlSum>
        ctrl_sum = float_round(sum(bank_line.amount_currency
                                   for bank_line in self.bank_line_ids), 2)
        control_sum_a.text = str(ctrl_sum)

        open("sepa_ch_test.xml", 'w').write(etree.tostring(xml_root, pretty_print=1))
        return self.finalize_sepa_file_creation(xml_root, sum(self.payment_order_ids.mapped('total')),
                                                nb_of_transactions_a, gen_args)

    @api.multi
    def create_sepa(self):
        """Creates the SEPA Direct Debit file. That's the important code !"""
        pain_flavor = self.payment_order_ids[0].mode.type.code
        if not pain_flavor in ACCEPTED_PAIN_FLAVOURS:
            return super(BankingExportSddWizard, self).create_sepa()
        return self.generate_xml_ch_dd_file()
