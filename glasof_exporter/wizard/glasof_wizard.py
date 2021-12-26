# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from io import BytesIO
import xlsxwriter
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GlassofExporterWizard(models.TransientModel):
    FILENAME = 'invoices_glasof.xls'
    _name = 'glasof.exporter.wizard'

    date_start = fields.Date("Start Date")
    date_end = fields.Date("End Date")
    export_journals = fields.Boolean("Export Account Movements?", default=True)
    export_invoices = fields.Boolean("Export Invoices?", default=True)
    property_id = fields.Many2one(
        string="Property",
        help="The property",
        comodel_name="pms.property"
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company",
        required=True,
        comodel_name="res.company",
    )
    seat_num = fields.Integer("Seat Number Start", default=1)
    xls_journals_filename = fields.Char()
    xls_journals_binary = fields.Binary()
    xls_invoices_filename = fields.Char()
    xls_invoices_binary = fields.Binary()

    @api.onchange("property_id")
    def onchangey_property_id(self):
        if self.property_id:
            self.company_id = self.property_id.company_id

    @api.onchange("company_id")
    def onchange_property_id(self):
        if self.property_id and self.company_id and self.property_id.company_id != self.company_id:
            raise UserError(_("El hotel seleccionado no es de esta compañía, eliminar o modifica el hotel para seleccionar esta compañía"))

    @api.model
    def _export_payments(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {
            'strings_to_numbers': True,
            'default_date_format': 'dd/mm/yyyy'
        })

        company_id = self.env.user.company_id
        workbook.set_properties({
            'title': 'Exported data from ' + company_id.name,
            'subject': 'PMS Data from Odoo of ' + company_id.name,
            'author': 'Odoo ALDA PMS',
            'manager': 'Jose Luis Algara',
            'company': company_id.name,
            'category': 'Hoja de Calculo',
            'keywords': 'pms, odoo, alda, data, ' + company_id.name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
        workbook.use_zip64()

        xls_cell_format_seat = workbook.add_format({'num_format': '#'})
        xls_cell_format_date = workbook.add_format({
            'num_format': 'dd/mm/yyyy'
        })
        xls_cell_format_saccount = workbook.add_format({
            'num_format': '000000'
        })
        xls_cell_format_money = workbook.add_format({
            'num_format': '#,##0.00'
        })
        xls_cell_format_header = workbook.add_format({
            'bg_color': '#CCCCCC'
        })

        worksheet = workbook.add_worksheet('Simples-1')

        worksheet.write('A1', _('Num Factura'), xls_cell_format_header)
        worksheet.write('B1', _('Cliente Reserva'), xls_cell_format_header)
        worksheet.write('C1', _('Fecha de Factura'), xls_cell_format_header)
        worksheet.write('D1', _('Cliente Factura'), xls_cell_format_header)
        worksheet.write('E1', _('NIF'), xls_cell_format_header)
        worksheet.write('F1', _('Ref-Pago'), xls_cell_format_header)
        worksheet.write('G1', _('Fecha de Pago'), xls_cell_format_header)
        worksheet.write('H1', _('Modo de pago'), xls_cell_format_header)
        worksheet.write('I1', _('Importe'), xls_cell_format_header)
        worksheet.write('J1', _('Tipo'), xls_cell_format_header)
        worksheet.write('K1', _('Origen'), xls_cell_format_header)

        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 50)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 11)
        worksheet.set_column('J:J', 11)
        worksheet.set_column('K:K', 11)

        folios = self.env["pms.folio"].search([
            ('company_id', '=', self.company_id.id),
            '|',
            ('payment_ids', '!=', False),
            ('statement_line_ids', '!=', False),
        ])
        if self.property_id:
            folios.filtered(lambda x: x.pms_property_id.id == self.property_id.id)

        sale_line_ids = folios.mapped("sale_line_ids.id")

        invoice_ids = self.env["folio.sale.line"].search([
            ("invoice_lines", "!=", False),
            ('id', 'in', sale_line_ids)
        ]).mapped("invoice_lines.move_id.id")

        account_inv_obj = self.env['account.move']
        account_invs = account_inv_obj.search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('move_type', '!=', 'entry'),
            ('id', 'in', invoice_ids)
        ])

        nrow = 1
        invoices_read = []
        for inv in account_invs:
            if inv.id in invoices_read:
                continue
            folio_ids = inv.line_ids.mapped("folio_line_ids.folio_id.id")
            folios = self.env["pms.folio"].browse(folio_ids)
            for folio_inv in folios.move_ids:
                invoices_read.append(folio_inv.id)
                country_code = ''
                vat_partner = inv.partner_id.vat if inv.partner_id.vat else ''
                country_partner = inv.partner_id.country_id
                if country_partner:
                    country_code = country_partner.code
                    if inv.partner_id.vat:
                        vat_partner = inv.partner_id.vat[2:] if inv.partner_id.vat[2:] == country_code else inv.partner_id.vat
                if not vat_partner and inv.partner_id.id_numbers:
                    vat_partner = inv.partner_id.id_numbers[0].name
                worksheet.write(nrow, 0, inv.name)
                worksheet.write(nrow, 1, inv.partner_id.name)
                worksheet.write(nrow, 2, inv.date, xls_cell_format_date)
                worksheet.write(nrow, 3, ",".join([fol.partner_name for fol in folios]))
                worksheet.write(nrow, 4, vat_partner)
                pays_read = []
                partial_pay = {}
                for pay in folios.payment_ids:
                    if pay.id in pays_read:
                        continue
                    if pay.amount == folio_inv.amount_total:
                        pays_read.append(pay.id)
                        amount = pay.amount
                    elif pay.amount < folio_inv.amount_total:
                        pays_read.append(pay.id)
                        amount = pay.amount
                    else:
                        amount = folio_inv.amount_total
                        if partial_pay.get(pay.id):
                            partial_pay[pay.id] += folio_inv.amount_total
                        else:
                            partial_pay[pay.id] = folio_inv.amount_total
                    worksheet.write(nrow, 5, pay.name)
                    worksheet.write(nrow, 6, pay.date, xls_cell_format_date)
                    worksheet.write(nrow, 7, pay.journal_id.name)
                    worksheet.write(nrow, 8, amount,
                                    xls_cell_format_money)
                    pay_type = "Devolución" if pay.payment_type == "outbound" else "Cobro"
                    worksheet.write(nrow, 9, pay_type)
                pays_read = []
                partial_pay = {}
                for pay in folios.statement_line_ids:
                    if pay.id in pays_read:
                        continue
                    if pay.amount == folio_inv.amount_total:
                        pays_read.append(pay.id)
                        amount = pay.amount
                    elif pay.amount < folio_inv.amount_total:
                        pays_read.append(pay.id)
                        amount = pay.amount
                    else:
                        amount = folio_inv.amount_total
                        if partial_pay.get(pay.id):
                            partial_pay[pay.id] += folio_inv.amount_total
                        else:
                            partial_pay[pay.id] = folio_inv.amount_total
                    worksheet.write(nrow, 5, pay.name)
                    worksheet.write(nrow, 6, pay.date, xls_cell_format_date)
                    worksheet.write(nrow, 7, pay.journal_id.name)
                    worksheet.write(nrow, 8, amount,
                                    xls_cell_format_money)
                    pay_type = "Devolución" if pay.amount < 0 else "Cobro"
                    worksheet.write(nrow, 9, pay_type)
                worksheet.write(nrow, 10, ",".join([fol.name for fol in folios]))
            nrow += 1

        workbook.close()
        file_data.seek(0)
        tnow = str(fields.Datetime.now()).replace(' ', '_')
        return {
            'xls_journals_filename': 'pagos_facturas_%s.xlsx' % tnow,
            'xls_journals_binary': base64.encodestring(file_data.read()),
        }

    @api.model
    def _export_invoices(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, {
            'strings_to_numbers': True,
            'default_date_format': 'dd/mm/yyyy'
        })

        company_id = self.env.user.company_id
        workbook.set_properties({
            'title': 'Exported data from ' + company_id.name,
            'subject': 'PMS Data from Odoo of ' + company_id.name,
            'author': 'Odoo ALDA PMS',
            'manager': 'Jose Luis Algara',
            'company': company_id.name,
            'category': 'Hoja de Calculo',
            'keywords': 'pms, odoo, alda, data, ' + company_id.name,
            'comments': 'Created with Python in Odoo and XlsxWriter'})
        workbook.use_zip64()

        xls_cell_format_seat = workbook.add_format({'num_format': '#'})
        xls_cell_format_date = workbook.add_format({
            'num_format': 'dd/mm/yyyy'
        })
        xls_cell_format_saccount = workbook.add_format({
            'num_format': '000000'
        })
        xls_cell_format_money = workbook.add_format({
            'num_format': '#,##0.00'
        })
        xls_cell_format_odec = workbook.add_format({
            'num_format': '#,#0.0'
        })
        xls_cell_format_header = workbook.add_format({
            'bg_color': '#CCCCCC'
        })

        worksheet = workbook.add_worksheet('ventas')

        account_inv_obj = self.env['account.move']
        account_invs = account_inv_obj.search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('move_type', '!=', 'entry'),
            ('company_id', '=', self.company_id.id),
        ])
        if self.property_id:
            account_invs.filtered(lambda x: x.pms_property_id.id == self.property_id.id)
        nrow = 1
        for inv in account_invs:
            if inv.partner_id.parent_id:
                firstname = inv.partner_id.parent_id.firstname or ''
                lastname = inv.partner_id.parent_id.lastname or ''
            else:
                firstname = inv.partner_id.firstname or ''
                lastname = inv.partner_id.lastname or ''

            country_code = ''
            vat_partner = inv.partner_id.vat if inv.partner_id.vat else ''
            country_partner = inv.partner_id.country_id
            if country_partner:
                country_code = country_partner.code
                if inv.partner_id.vat:
                    vat_partner = inv.partner_id.vat[2:] if inv.partner_id.vat[2:] == country_partner.code else inv.partner_id.vat

            if not vat_partner and inv.partner_id.id_numbers:
                vat_partner = inv.partner_id.id_numbers[0].name

            worksheet.write(nrow, 0, inv.name)
            worksheet.write(nrow, 1, inv.invoice_date, xls_cell_format_date)
            worksheet.write(nrow, 2, '')
            worksheet.write(nrow, 3, country_code)
            worksheet.write(nrow, 4, vat_partner)
            worksheet.write(nrow, 5, lastname)
            worksheet.write(nrow, 6, '')
            worksheet.write(nrow, 7, firstname)
            worksheet.write(nrow, 8, 705.0, xls_cell_format_odec)
            worksheet.write(nrow, 9, inv.amount_untaxed, xls_cell_format_money)
            if any(inv.invoice_line_ids.tax_line_id):
                worksheet.write(nrow,
                                10,
                                inv.amount_tax,
                                xls_cell_format_money)
            else:
                worksheet.write(nrow, 10, '')
            worksheet.write(nrow, 11, inv.invoice_line_ids.tax_line_id and
                            inv.amount_tax or '',
                            xls_cell_format_money)
            worksheet.write(nrow, 12, '')
            worksheet.write(nrow, 13, '')
            worksheet.write(nrow, 14, '')
            worksheet.write(nrow, 15, '')
            worksheet.write(nrow, 16, '')
            worksheet.write(nrow, 17, '')
            worksheet.write(nrow, 18, '')
            worksheet.write(nrow, 19, '')
            worksheet.write(nrow, 20, '')
            worksheet.write(nrow, 21, 'S')
            worksheet.write(nrow, 22, '')
            if inv.move_type == 'out_refund':
                worksheet.write(nrow, 23, inv.invoice_origin)
            else:
                worksheet.write(nrow, 23, '')
            worksheet.write(nrow, 24, '')
            worksheet.write(nrow, 25, '')
            worksheet.write(nrow, 27, '')
            worksheet.write(nrow, 28, '')
            worksheet.write(nrow, 29, '')
            worksheet.write(nrow, 30, '')
            worksheet.write(nrow, 31, '')
            worksheet.write(nrow, 32, '')
            worksheet.write(nrow, 33, '')
            worksheet.write(nrow, 34, '')
            worksheet.write(nrow, 35, '')
            worksheet.write(nrow, 36, '')
            worksheet.write(nrow, 37, '')
            worksheet.write(nrow, 38, '')
            worksheet.write(nrow, 39, '')
            worksheet.write(nrow, 40, '')
            worksheet.write(nrow, 41, '')
            worksheet.write(nrow, 42, '')
            worksheet.write(nrow, 43, '430')
            nrow += 1

        workbook.add_worksheet('compras')
        workbook.close()
        file_data.seek(0)
        tnow = str(fields.Datetime.now()).replace(' ', '_')
        return {
            'xls_invoices_filename': 'facturas_glasof_%s.xlsx' % tnow,
            'xls_invoices_binary': base64.encodestring(file_data.read()),
        }

    def export(self):
        towrite = {}
        if self.export_journals:
            towrite.update(self._export_payments())
        if self.export_invoices:
            towrite.update(self._export_invoices())
        if any(towrite):
            self.write(towrite)
        return {
            "name": _("Glasof export"),
            "res_id": self.id,
            "res_model": "glasof.exporter.wizard",
            "type": "ir.actions.act_window",
            "view_id": self.env.ref("glasof_exporter.view_glasof_exporter_wizard").id,
            "view_mode": "form",
        }
