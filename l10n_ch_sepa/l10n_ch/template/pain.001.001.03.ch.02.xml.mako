<%inherit file="pain.001.001.03.xml.mako"/>

<%block name="root">
<Document xmlns="http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd pain.001.001.03.ch.02.xsd">
</%block>

<%block name="CdtrAgt">
<%doc>\
        For type 1, Creditor Agent shouldn't be delivered
</%doc>\
   <%
   line=sepa_context['line']
   %>
   % if not line.bank_id.state == 'bvr':
    ${parent.CdtrAgt()}
   % endif
</%block>

<%block name="PmtTpInf">
<%doc>\
        Local Instrument
            Code
             or
            Proprietary

        Proprietary is required for types 1, 2.1, 2.2
        1: CH01
        2.1: CH02
        2.2: CH03

        Code is requiered for type 7
        7: CCP

</%doc>\
   <%
   line=sepa_context['line']
   %>
   % if line.bank_id.state == 'bvr':
          <PmtTpInf>
              <LclInstrm>
                <Prtry>CH01</Prtry>
              </LclInstrm>
          </PmtTpInf>
   % endif
</%block>

<%block name="RmtInf">
   <%
   line=sepa_context['line']
   %>
<%doc>\
Strd:
Art 1 (ESR): Muss verwendet werden.
Art 2.1, 2.2 (ES 1-stufig, ES 2-stufig): Darf nicht verwendet werden.
Art 3: Darf verwendet werden. In Zusammenhang
mit QR-IBAN (gültig ab 01.01.2019) muss dieses
Element verwendet werden.
Art 4, 5, 6, 7, 8: Darf maximal 140 Zeichen
einschliesslich XML-Tags beinhalten.
</%doc>\
   % if line.bank_id.state == 'bvr' and line.communication:
<%doc>\
STRD - Structured:
    ISO Definition:
    Information supplied to enable the matching/reconciliation of an entry with the items that the payment is
    intended to settle, such as commercial invoices in an accounts' receivable system, in a structured form.

    CH Definition: Only one occurrence is allowed, maximum 140 characters inclusive XML tags. If used, then
    "Unstructured" must not be present.

    CH PT Definition: Type 1: must be used.
    Type 2.1, 2.2: must not be used.
    Type 3: May be used. In association with QR-IBAN (valid from 01.01.2019) this element must be used.
    Type 4, 5, 6, 7, 8: May only contain maximum 140 characters including XML tags.


STRD - Structured:
</%doc>\
          <RmtInf>
            <Strd>
              <CdtrRefInf>
                <Ref>${line.communication}</Ref>
              </CdtrRefInf>
            </Strd>
          </RmtInf>
   % elif  line.bank_id.state != 'bvr' and line.communication:
<%doc>\

USTRD - UnStructured:
    ISO Definition: Information supplied to enable the matching/reconciliation of an entry with the items that the payment is
    intended to settle, such as commercial invoices in an accounts' receivable system, in an unstructured
    form.

    CH Definition: Only one occurrence is allowed, maximum 140 characters. If used, then "Structured" must not be
    present.

    CH PT Definition: Type 1: must not be used.
</%doc>\
          <RmtInf>
            <Ustrd>${line.communication}</Ustrd>
          </RmtInf>
   % endif
</%block>

<%def name="acc_id(bank_acc)">
              <Id>
                % if bank_acc.state == 'iban':
                  <IBAN>${bank_acc.acc_number.replace(' ', '')}</IBAN>
                % else:
                  <Othr>
                    <Id>${bank_acc.get_account_number()}</Id>
                  </Othr>
                % endif
              </Id>
</%def>
