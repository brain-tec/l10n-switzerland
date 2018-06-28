<?xml version='1.0' encoding='UTF-8'?>
<%block name="root">\
<Document xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
</%block>\
\
<%!
    def filter_text(text):
        # Mapping between Latin-1 to ascii characters, used also for LSV.
        LSV_LATIN1_TO_ASCII_MAPPING = {
            32: ' ', 33: '.', 34: '.', 35: '.', 36: '.', 37: '.', 38: '+', 39: "'",
            40: '(', 41: ')', 42: '.', 43: '+', 44: ',', 45: '-', 46: '.', 47: '/',
            48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6', 55: '7',
            56: '8', 57: '9', 58: ':', 59: '.', 60: '.', 61: '.', 62: '.', 63: '?',
            64: '.', 65: 'A', 66: 'B', 67: 'C', 68: 'D', 69: 'E', 70: 'F', 71: 'G',
            72: 'H', 73: 'I', 74: 'J', 75: 'K', 76: 'L', 77: 'M', 78: 'N', 79: 'O',
            80: 'P', 81: 'Q', 82: 'R', 83: 'S', 84: 'T', 85: 'U', 86: 'V', 87: 'W',
            88: 'X', 89: 'Y', 90: 'Z', 91: '.', 92: '.', 93: '.', 94: '.', 95: '.',
            96: '.', 97: 'a', 98: 'b', 99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g',
            104: 'h', 105: 'i', 106: 'j', 107: 'k', 108: 'l', 109: 'm', 110: 'n',
            111: 'o', 112: 'p', 113: 'q', 114: 'r', 115: 's', 116: 't', 117: 'u',
            118: 'v', 119: 'w', 120: 'x', 121: 'y', 122: 'z', 123: '.', 124: '.',
            125: '.', 126: '.', 127: '.', 128: ' ', 129: ' ', 130: ' ', 131: ' ',
            132: ' ', 133: ' ', 134: ' ', 135: ' ', 136: ' ', 137: ' ', 138: ' ',
            139: ' ', 140: ' ', 141: ' ', 142: ' ', 143: ' ', 144: ' ', 145: ' ',
            146: ' ', 147: ' ', 148: ' ', 149: ' ', 150: ' ', 151: ' ', 152: ' ',
            153: ' ', 154: ' ', 155: ' ', 156: ' ', 157: ' ', 158: ' ', 159: ' ',
            160: '.', 161: '.', 162: '.', 163: '.', 164: '.', 165: '.', 166: '.',
            167: '.', 168: '.', 169: '.', 170: '.', 171: '.', 172: '.', 173: '.',
            174: '.', 175: '.', 176: '.', 177: '.', 178: '.', 179: '.', 180: '.',
            181: '.', 182: '.', 183: '.', 184: '.', 185: '.', 186: '.', 187: '.',
            188: '.', 189: '.', 190: '.', 191: '.', 192: 'A', 193: 'A', 194: 'A',
            195: 'A', 196: 'EA', 197: 'A', 198: 'EA', 199: 'C', 200: 'E', 201: 'E',
            202: 'E', 203: 'E', 204: 'I', 205: 'I', 206: 'I', 207: 'I', 208: '.',
            209: 'N', 210: 'O', 211: 'O', 212: 'O', 213: 'O', 214: 'EO', 215: '.',
            216: '.', 217: 'U', 218: 'U', 219: 'U', 220: 'EU', 221: 'Y', 222: '.',
            223: 'ss', 224: 'a', 225: 'a', 226: 'a', 227: 'a', 228: 'ea', 229: 'a',
            230: 'ea', 231: 'c', 232: 'e', 233: 'e', 234: 'e', 235: 'e', 236: 'i',
            237: 'i', 238: 'i', 239: 'i', 240: '.', 241: 'n', 242: 'o', 243: 'o',
            244: 'o', 245: 'o', 246: 'eo', 247: '.', 248: '.', 249: 'u', 250: 'u',
            251: 'u', 252: 'eu', 253: 'y', 254: '.', 255: 'y',
        }
        text = ''.join([LSV_LATIN1_TO_ASCII_MAPPING.get(ord(ch), ch) for ch in text])
        return text
%>
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>${order.reference | filter_text}</MsgId>
      <CreDtTm>${thetime.strftime("%Y-%m-%dT%H:%M:%S")}</CreDtTm>
      <NbOfTxs>${len (order.line_ids)}</NbOfTxs>
      <%
      control_sum = sum([line.amount_currency for line in order.line_ids])
      %>
      <CtrlSum>${control_sum}</CtrlSum>\
      <%block name="InitgPty">
        <InitgPty>
          <Nm>${order.user_id.company_id.name | filter_text}</Nm>\
          ${address(order.user_id.company_id.partner_id) | filter_text}\
        </InitgPty>\
      </%block>
    </GrpHdr>\
<%doc>\
  for each payment in the payment order
  line is saved in sepa_context in order to be available
  in sub blocks and inheritages. Because, for now, only unamed
  blocks and def in mako can use a local for loop variable.
</%doc>
<%block name="PmtInf">\
<%
today = thetime.strftime("%Y-%m-%d")
%>
<PmtInf>
    <PmtInfId>${order.reference}</PmtInfId>
    <PmtMtd>${order.mode.payment_method if order.mode else ''}</PmtMtd>
    <BtchBookg>${'true' if order.mode and order.mode.batchbooking else 'false'}</BtchBookg>
    <ReqdExctnDt>${ order.date_scheduled and order.date_scheduled > today or today}</ReqdExctnDt>
    <Dbtr>
      <Nm>${order.user_id.company_id.name | filter_text }</Nm>\
      <!-- SIX ISO20022 Recommendation: Do not use. -->
        <!--${self.address(order.user_id.company_id.partner_id) | filter_text}\-->
    </Dbtr>
    <DbtrAcct>\
      ${self.acc_id(order.mode.bank_id)}\
    </DbtrAcct>
    <DbtrAgt>
      <FinInstnId>
        <BIC>${order.mode.bank_id.bank.bic or order.mode.bank_id.bank_bic}</BIC>
      </FinInstnId>
    </DbtrAgt>
% for line in order.line_ids:
        <% sepa_context['line'] = line %>\
        <CdtTrfTxInf>
          <PmtId>
              <!-- ZKB mandatory field -->
              <InstrId>${line.name}</InstrId>
              <EndToEndId>${line.name}</EndToEndId>
          </PmtId>
          <%block name="PmtTpInf"/>
          <Amt>
            <InstdAmt Ccy="${line.currency.name}">${line.amount_currency}</InstdAmt>
          </Amt>
          <ChrgBr>SLEV</ChrgBr>

          <%block name="CdtrAgt">
            <%
            line=sepa_context['line']
            invoice = line.move_line_id.invoice
            %>
            <CdtrAgt>
              <FinInstnId>
                <BIC>${line.bank_id.bank.bic or line.bank_id.bank_bic}</BIC>
              </FinInstnId>
            </CdtrAgt>
          </%block>
          <Cdtr>
            <Nm>${line.partner_id.name | filter_text}</Nm>\
            ${self.address(line.partner_id) | filter_text}\
          </Cdtr>
          <CdtrAcct>\
            ${self.acc_id(line.bank_id)}\
          </CdtrAcct>\
          <%block name="RmtInf"/>
        </CdtTrfTxInf>

% endfor

</PmtInf>\
</%block>

\
  </CstmrCdtTrfInitn>
</Document>
\
<%def name="address(partner)">\
              <PstlAdr>
                %if partner.street:
                  <StrtNm>${partner.street.strip() | filter_text}</StrtNm>
                %endif
                %if partner.zip:
                  <PstCd>${partner.zip | filter_text}</PstCd>
                %endif
                %if partner.city:
                  <TwnNm>${partner.city | filter_text}</TwnNm>
                %endif
                <Ctry>${partner.country_id.code or partner.company_id.country_id.code}</Ctry>
              </PstlAdr>
</%def>\
\
<%def name="acc_id(bank_acc)">
              <Id>
                % if bank_acc.state == 'iban':
                  <IBAN>${bank_acc.iban.replace(' ', '')}</IBAN>
                % else:
                  <Othr>
                    <Id>${bank_acc.acc_number}</Id>
                  </Othr>
                % endif
              </Id>
</%def>
