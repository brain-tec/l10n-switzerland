<%inherit file="pain.001.001.09.xml.mako"/>

<%!
import re

def swiss_text(text, limit=70):
    text = unicode(text or u'')
    text = re.sub(ur'[^\u0020-\u007e\u00a0-\u00ff\u0100-\u017f€ȘșȚț]', u' ', text)
    return text[:limit]
%>

<%block name="root">
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09 pain.001.001.09.ch.03.xsd">
</%block>

<%block name="CdtrAgt">
    <%
    line=sepa_context['line']
    %>
    % if not line.bank_id.state == 'bvr':
    ${parent.CdtrAgt()}
    % endif
</%block>

<%block name="InitgPty">
    <InitgPty>
        <Nm>${swiss_text(order.user_id.company_id.name)}</Nm>
    </InitgPty>
</%block>

<%block name="PmtTpInf">
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
    % if line.bank_id.state == 'bvr':
           <RmtInf>
             <Strd>
               <CdtrRefInf>
                 <Ref>${line.communication}</Ref>
               </CdtrRefInf>
             </Strd>
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

<%def name="address(partner)">\
              <PstlAdr>

<%
    partner_street = ""
    if partner.street:
        partner_street = re.sub(r'[ \t\r\n]+', r' ', partner.street.strip())
%>
                %if partner.street:
                  <StrtNm>${swiss_text(partner_street)}</StrtNm>
                %endif
                %if partner.zip:
                  <PstCd>${partner.zip}</PstCd>
                %endif
                %if partner.city:
                  <TwnNm>${partner.city}</TwnNm>
                %endif
                <Ctry>${partner.country_id.code or partner.company_id.country_id.code}</Ctry>
              </PstlAdr>
</%def>\

