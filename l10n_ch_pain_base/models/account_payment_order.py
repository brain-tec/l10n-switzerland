# copyright 2016 Akretion (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _
from odoo.exceptions import UserError
from lxml import etree



class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def compute_sepa_final_hook(self, sepa):
        self.ensure_one()
        sepa = super().compute_sepa_final_hook(sepa)
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        # ISR orders cannot be SEPA orders
        if pain_flavor and '.ch.' in pain_flavor:
            sepa = False
        return sepa

    @api.multi
    def generate_pain_nsmap(self):
        self.ensure_one()
        nsmap = super().generate_pain_nsmap()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ['pain.001.001.03.ch.02', 'pain.008.001.02.ch.01']:
            nsmap[None] = 'http://www.six-interbank-clearing.com/de/'\
                          '%s.xsd' % pain_flavor

        return nsmap

    @api.multi
    def generate_pain_attrib(self):
        self.ensure_one()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor in ['pain.001.001.03.ch.02', 'pain.008.001.02.ch.01']:
            attrib = {
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                "http://www.six-interbank-clearing.com/de/"
                "%s.xsd  %s.xsd" % (pain_flavor, pain_flavor)
                }
            return attrib
        else:
            return super().generate_pain_attrib()

    @api.model
    def generate_start_payment_info_block(
            self, parent_node, payment_info_ident,
            priority, local_instrument, category_purpose, sequence_type,
            requested_date, eval_ctx, gen_args):
        if gen_args.get('pain_flavor') == 'pain.001.001.03.ch.02':
            gen_args['local_instrument_type'] = 'proprietary'
            gen_args['structured_remittance_issuer'] = False
        return super().generate_start_payment_info_block(
            parent_node, payment_info_ident, priority, local_instrument,
            category_purpose, sequence_type, requested_date, eval_ctx,
            gen_args,
        )

    @api.model
    def generate_party_agent(
            self, parent_node, party_type, order, partner_bank, gen_args,
            bank_line=None):
        if (
                gen_args.get('pain_flavor') == 'pain.001.001.03.ch.02' and
                bank_line):
            if (  # for the own bank account we set the BIC
                (party_type == 'Dbtr' and partner_bank.bank_bic) or
                # In case we have a foreign account and it is not EUR
                # (not SEPA) we also have to set the BIC
                (party_type == 'Cdtr' and partner_bank.bank_bic and
                 not bank_line.partner_bank_id.acc_number[0:2] == 'CH' and
                 not bank_line.currency_id.name == 'EUR')
               ):
                party_agent = etree.SubElement(parent_node,
                                               '%sAgt' % party_type)
                party_agent_institution = etree.SubElement(
                        party_agent, 'FinInstnId')
                party_agent_bic = etree.SubElement(
                        party_agent_institution, gen_args.get('bic_xml_tag'))
                party_agent_bic.text = partner_bank.bank_bic
                return True
            if bank_line.local_instrument == 'CH01':
                # Don't set the creditor agent on ISR/CH01 payments
                return True
        # if party_type == 'Dbtr' and partner_bank.bank_bic:
        #     party_agent = etree.SubElement(parent_node, '%sAgt' % party_type)
        #     party_agent_institution = etree.SubElement(
        #         party_agent, 'FinInstnId')
        #     party_agent_bic = etree.SubElement(
        #         party_agent_institution, gen_args.get('bic_xml_tag'))
        #     party_agent_bic.text = partner_bank.bank_bic
        #     return True
        return super().generate_party_agent(
            parent_node, party_type, order, partner_bank, gen_args,
            bank_line=bank_line,
        )

    @api.model
    def generate_party_acc_number(self, parent_node, party_type, order,
                                  partner_bank, gen_args, bank_line=None):
        if (gen_args.get('pain_flavor') == 'pain.001.001.03.ch.02' and
                bank_line and
                bank_line.local_instrument == 'CH01'):
            if not partner_bank.ccp:
                raise UserError(_(
                    "The field 'CCP/CP-Konto' is not set on the bank "
                    "account '%s'.") % partner_bank.acc_number)
            party_account = etree.SubElement(
                parent_node, '%sAcct' % party_type)
            party_account_id = etree.SubElement(party_account, 'Id')
            party_account_other = etree.SubElement(
                party_account_id, 'Othr')
            party_account_other_id = etree.SubElement(
                party_account_other, 'Id')
            party_account_other_id.text = partner_bank.ccp
            return True
        else:
            return super().generate_party_acc_number(
                parent_node, party_type, order, partner_bank, gen_args,
                bank_line=bank_line)
