# Copyright 2020 Commitsun.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import io
import csv
import base64
import pandas as pd
from contextlib import closing
import pyparsing as pp

from odoo import fields, models, api
from odoo.tools import float_round


class PmsWizardReconcile(models.TransientModel):

    _name = "pms.wizard.reconcile"
    _description = "Reconcile Payments"

    name = fields.Char("File name")
    file = fields.Binary("File")
    type = fields.Selection([("csv", "CSV")], default="csv", string="File type.")

    journal_ids = fields.Many2many("account.journal", string="Journals")

    filter_by_date = fields.Boolean("Filter by date")
    filter_from = fields.Date("Filter from")
    filter_to = fields.Date("Filter to")

    filter_by_property = fields.Boolean("Filter by property")
    pms_property_id = fields.Many2one("pms.property", "Property")

    filter_by_origin_agency = fields.Boolean("Filter by origin agency")
    origin_agency_id = fields.Many2one("pms.agency", "Origin agency")

    move_types = fields.Selection(
        string="Move types",
        selection=[("payment", "Payment"), ("invoice", "Invoice"), ('all', 'All')],
        default="payment",
    )

    move_line_ids = fields.Many2many(
        "account.move.line",
        string="Move lines",
    )

    origin_statement_line_id = fields.Many2one(
        comodel_name="account.bank.statement.line",
        string="Origin statement line",
        default=lambda self: self._default_origin_statement_line_id(),
        required=True,
    )

    folio_ids = fields.Many2many(
        string="folios not found",
        comodel_name="pms.folio"
    )

    target_total = fields.Float(
        string="Target total",
        compute="_compute_target_total"
    )

    residual = fields.Float(
        string="Residual",
        compute="_compute_residual"
    )

    csv_not_found = fields.Char(
        string="transactions not found",
        readonly=True,
    )

    def _default_origin_statement_line_id(self):
        return self.env.context.get("active_id", False)

    @api.depends("move_line_ids")
    def _compute_target_total(self):
        for record in self:
            record.target_total = sum(record.move_line_ids.mapped("balance"))

    @api.depends("target_total")
    def _compute_residual(self):
        for record in self:
            record.residual = float_round(
                record.target_total - record.origin_statement_line_id.amount,
                2
            )

    def search_move_line_ids(self):
        self.ensure_one()
        domain = [
            ("account_id.reconcile", "=", True),
            ("reconciled", "=", False),
            ("move_id.state", "=", "posted"),
        ]
        if self.move_types != 'all':
            journal_types = ["sale"] if self.move_types == "invoice" else ["bank"]
            domain.append(("journal_id.type", "in", journal_types))
        if self.filter_by_date and self.filter_from and self.filter_to:
            domain.append(("date", ">=", self.filter_from))
            domain.append(("date", "<=", self.filter_to))
        if self.filter_by_property and self.property_id:
            domain.append(("pms_property_id", "=", self.property_id.id))
        if self.filter_by_origin_agency and self.origin_agency_id:
            domain.append(("origin_agency_id", "=", self.origin_agency_id.id))
        if self.file and self.journal_ids:
            domain.append(("id", "in", self._get_move_line_ids(self.file)))
            domain.append(("journal_id", "in", self.journal_ids.ids))
            self.move_line_ids = self.env["account.move.line"].search(domain)
        else:
            self.move_line_ids = False

    @api.model
    def _get_move_line_ids(self, file):
        lines = self.get_and_parse_csv(file)
        return lines.ids

    def _read_csv(self, file):
        if self.file:
            return base64.b64decode(file)

    @api.model
    def get_and_parse_csv(self, file):
        with closing(io.BytesIO(self._read_csv(file))) as binary_file:
            csv.register_dialect('mydialect', delimiter=',', quoting=csv.QUOTE_MINIMAL, doublequote=True, skipinitialspace=True)
            reader = pd.read_csv(binary_file, dialect='mydialect', engine="python", header=0)
            keys = [i.replace('"', '') for i in reader.columns[0].split(",")]
            csv_payments = []
            for line in reader.values:
                values = [i.replace('"', '') for i in pp.pyparsing_common.comma_separated_list.parseString(line[0]).asList()]
                new_item = dict(zip(keys, values))
                csv_payments.append(new_item)
            lines = self.env["account.move.line"]
            for pay in csv_payments:
                line = False
                line = self.env["account.move.line"].search([
                    ("ref", "ilike", pay["Número de referencia"]),
                    ("balance", "=", float(pay["Importe"])),
                ])
                if line:
                    lines += line
                else:
                    mens = pay["Número de referencia"]
                    folio = self.env["pms.folio"].search([("external_reference", "=", pay["Número de referencia"])])
                    if folio:
                        self.folio_ids = [(4, folio.id)]
                    else:
                        mens += "(not found)"
                        self.csv_not_found = mens if not self.csv_not_found else self.csv_not_found + ", " + mens
        return lines

    def matching_button(self):
        self.ensure_one()
        domain = [('account_internal_type', 'in', ('receivable', 'payable', 'other')), ('reconciled', '=', False)]
        statement_move_line = self.origin_statement_line_id.move_id.line_ids.filtered_domain(
            domain
        )
        statement_move_line.account_id = self.move_line_ids.account_id
        lines_to_reconcile = statement_move_line + self.move_line_ids
        lines_to_reconcile.reconcile()
        action = self.env.ref('account.action_bank_statement_tree').sudo().read()[0]
        action['views'] = [(self.env.ref('account.view_bank_statement_form').id, 'form')]
        action['res_id'] = self.origin_statement_line_id.statement_id.id
        return action
