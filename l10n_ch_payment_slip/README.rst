.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

======================================
Swiss inpayment slip (ISR/PVR/BVR/ESR)
======================================


This addon allows you to print the ISR report Using Qweb report.

ISR is called:
- PVR in italian
- BVR in french
- ESR in german

The ISR is grenerated as an image and is availabe in a fields
of the `l10n_ch.payment_slip` Model.

This module also adds transaction_ref field on entries in order to manage
reconciliation in multi payment context (unique reference needed on
account.move.line). Many ISR can now be printed from one invoice for each
payment terms.


Configuration
=============

You can adjust the print out of ISR, which depend on each printer,
In the General Settings - Invoicing. The settings are specific for every
company.

This is especialy useful when using pre-printed paper.
Options also allow you to print the ISR in background when using
white paper and printing customer address in the page header.

By default address format on ISR is
`%(street)s
%(street2)s
%(zip)s %(city)s`
This can be change by setting System parameter
`isr.address.format`


Usage
=====

The ISR is created each time an invoice is validated.
To modify it you have to cancel it and reconfirm the invoice.

You can also activate "Save as attachement" for ISR prints your invoice.
To do so, edit the ir.actions.report `Payment Slip` with the template
name `l10n_ch_payment_slip.one_slip_per_page_from_invoice`.

To import v11, the feature has been moved in module `l10n_ch_import_isr_v11`

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/11.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/l10n-switzerland/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Vincent Renaville <vincent.renaville@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Romain Deheele <romain.deheele@camptocamp.com>
* Thomas Winteler <info@win-soft.com>
* Joël Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Alex Comba <alex.comba@agilebg.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* Paul Catinean <paulcatinean@gmail.com>
* Paulius Sladkevičius <paulius@hbee.eu>
* David Coninckx <dco@open-net.ch>
* Akim Juillerat <akim.juillerat@camptocamp.com>
* Simone Orsi <simone.orsi@camptocamp.com>

Financial contributors
----------------------

Hasa SA, Open Net SA, Prisme Solutions Informatique SA, Quod SA

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.

