# Copyright 2019  Pablo Q. Barriuso
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from dateutil.relativedelta import relativedelta
import datetime
from itertools import groupby
import urllib.error
from odoo.tools.mail import email_escape_char
import odoorpc.odoo
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class MigratedHotel(models.Model):
    _name = 'migrated.hotel'

    name = fields.Char('Name', copy=False)
    odoo_host = fields.Char('Host', help='Full URL to the host.')
    odoo_db = fields.Char('Database Name', required=True, help='Odoo database name.')
    odoo_user = fields.Char('Username', required=True, help='Odoo administration user.')
    odoo_password = fields.Char('Password', required=True, help='Odoo password.')
    odoo_port = fields.Integer(string='TCP Port', required=True, default=443,
                               help='Specify the TCP port for the XML-RPC protocol.')
    odoo_protocol = fields.Selection([('jsonrpc+ssl', 'jsonrpc+ssl')],
                                     'Protocol', required=True, default='jsonrpc+ssl')
    odoo_version = fields.Char()

    migration_date_d = fields.Date('Migration Ddate', copy=False)
    migration_before_date_d = fields.Boolean('Migrate data before Ddate', default=True)
    migration_date_operator = fields.Char(default='<')

    log_ids = fields.One2many('migrated.log', 'migrated_hotel_id')

    pms_property_id = fields.Many2one(
        string="Property",
        help="The migration property",
        comodel_name="pms.property",
        copy=False,
    )

    count_total_partners = fields.Integer(string="Partners Total V11", readonly=True, copy=False)
    count_migrated_partners = fields.Integer(string="Partners V14 Migrated", readonly=True, copy=False)
    count_tarjet_partners = fields.Integer(string="Partners Tarjet (With documents)", readonly=True, copy=False)
    complete_partners = fields.Boolean("Partners Complete", compute="_compute_complete_partners", store=True, copy=False)

    count_total_folios = fields.Integer(string="Folios Total V11", readonly=True, copy=False)
    count_migrated_folios = fields.Integer(string="Folios V14 Migrated", readonly=True, copy=False)
    count_tarjet_folios = fields.Integer(string="Folios Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_folios = fields.Boolean("Folios Complete", compute="_compute_complete_folios", store=True, copy=False)

    count_total_reservations = fields.Integer(string="Reservations Total V11", readonly=True, copy=False)
    count_migrated_reservations = fields.Integer(string="Reservations V14 Migrated", readonly=True, copy=False)
    count_tarjet_reservations = fields.Integer(string="Reservations Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_reservations = fields.Boolean("Reservations Complete", compute="_compute_complete_reservations", store=True, copy=False)

    count_total_checkins = fields.Integer(string="Checkins Total V11", readonly=True, copy=False)
    count_migrated_checkins = fields.Integer(string="Checkins V14 Migrated", readonly=True, copy=False)
    count_tarjet_checkins = fields.Integer(string="Checkins Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_checkins = fields.Boolean("Checkins Complete", compute="_compute_complete_checkins", store=True, copy=False)

    count_total_payments = fields.Integer(string="Payments Total V11", readonly=True, copy=False)
    count_migrated_payments = fields.Integer(string="Payments V14 Migrated", readonly=True, copy=False)
    count_tarjet_payments = fields.Integer(string="Payments Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_payments = fields.Boolean("Payments Complete", compute="_compute_complete_payments", store=True, copy=False)

    count_total_invoices = fields.Integer(string="Invoices Total V11", readonly=True, copy=False)
    count_migrated_invoices = fields.Integer(string="Invoices V14 Migrated", readonly=True, copy=False)
    count_tarjet_invoices = fields.Integer(string="Invoices Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_invoices = fields.Boolean("Invoices Complete", compute="_compute_complete_invocies", store=True, copy=False)

    backend_id = fields.Many2one('channel.backend', copy=False)

    dummy_closure_reason_id = fields.Many2one(string='Default Clousure Reasen', comodel_name='room.closure.reason')
    dummy_product_id = fields.Many2one(string='Default Product', comodel_name='product.product')
    default_channel_agency_id = fields.Many2one(string='Default agencys Channel', comodel_name='pms.sale.channel')
    default_plan_avail_id = fields.Many2one('pms.availability.plan')
    folio_prefix = fields.Char("Add prefix on folios")

    migrated_pricelist_ids = fields.One2many(
        string="Pricelists Mapping",
        readonly=False,
        comodel_name="migrated.pricelist",
        inverse_name="migrated_hotel_id",
    )
    count_total_pricelists = fields.Integer(string="Total Pricelists V11", readonly=True, copy=False)
    count_migrated_pricelists = fields.Integer(string="Pricelists V14 Migrated", readonly=True, copy=False)
    count_tarjet_pricelists = fields.Integer(string="Pricelists Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_pricelists = fields.Boolean("Pricelists Complete", compute="_compute_complete_pricelists", store=True, copy=False)

    migrated_room_type_ids = fields.One2many(
        string="Room Types Mapping",
        readonly=False,
        comodel_name="migrated.room.type",
        inverse_name="migrated_hotel_id",
    )
    count_total_room_types = fields.Integer(string="Total Room Types V11", readonly=True, copy=False)
    count_migrated_room_types = fields.Integer(string="Room Types V14 Migrated", readonly=True, copy=False)
    count_tarjet_room_types = fields.Integer(string="Room Types Tarjet ('Migration D-Date')", readonly=True, copy=False)
    migrated_room_type_class_ids = fields.One2many(
        string="Room Type Clases Mapping",
        readonly=False,
        comodel_name="migrated.room.type.class",
        inverse_name="migrated_hotel_id",
    )
    auto_create_rooms = fields.Boolean(string="Create Rooms automatically", default=False, copy=False)
    migrated_room_ids = fields.One2many(
        string="Rooms Mapping",
        readonly=False,
        comodel_name="migrated.room",
        inverse_name="migrated_hotel_id",
    )
    count_total_rooms = fields.Integer(string="Total Rooms V11", readonly=True, copy=False)
    count_migrated_rooms = fields.Integer(string="Rooms V14 Migrated", readonly=True, copy=False)
    count_tarjet_rooms = fields.Integer(string="Rooms Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_rooms = fields.Boolean("Rooms Complete", compute="_compute_complete_rooms", store=True, copy=False)
    auto_create_products = fields.Boolean(string="Create Products automatically", default=False, copy=False)
    migrated_product_ids = fields.One2many(
        string="Products Mapping",
        readonly=False,
        comodel_name="migrated.product",
        inverse_name="migrated_hotel_id",
    )
    count_total_products = fields.Integer(string="Total Products V11", readonly=True, copy=False)
    count_migrated_products = fields.Integer(string="Products V14 Migrated", readonly=True, copy=False)
    count_tarjet_products = fields.Integer(string="Products Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_products = fields.Boolean("Products Complete", compute="_compute_complete_products", store=True, copy=False)
    migrated_board_service_ids = fields.One2many(
        string="Boards Mapping",
        readonly=False,
        comodel_name="migrated.board.service",
        inverse_name="migrated_hotel_id",
    )
    count_total_board_services = fields.Integer(string="Total Boards V11", readonly=True, copy=False)
    count_migrated_board_services = fields.Integer(string="Boards V14 Migrated", readonly=True, copy=False)
    count_tarjet_board_services = fields.Integer(string="Boards Tarjet ('Migration D-Date')", readonly=True, copy=False)
    complete_boards = fields.Boolean("Boards Complete", compute="_compute_complete_boards", store=True, copy=False)
    auto_create_board_service_room_types = fields.Boolean(string="Create Board Service in Room Types automatically", default=False, copy=False)
    migrated_board_service_room_type_ids = fields.One2many(
        string="Board Rooms Services Mapping",
        readonly=False,
        comodel_name="migrated.board.service.room.type",
        inverse_name="migrated_hotel_id",
    )

    migrated_journal_ids = fields.One2many(
        string="Pricelists Mapping",
        readonly=False,
        comodel_name="migrated.journal",
        inverse_name="migrated_hotel_id",
    )
    count_total_journals = fields.Integer(string="Total Journals V11", readonly=True, copy=False)
    count_migrated_journals = fields.Integer(string="Journals V14 Migrated", readonly=True, copy=False)
    complete_journals = fields.Boolean("Pricelists Complete", compute="_compute_complete_journals", store=True, copy=False)

    migrated_channel_type_ids = fields.One2many(
        string="Channels Services Mapping",
        readonly=False,
        comodel_name="migrated.channel.type",
        inverse_name="migrated_hotel_id",
    )
    complete_channels = fields.Boolean("Channels Complete", compute="_compute_complete_channels", store=True, copy=False)

    last_import_rooms = fields.Datetime("Updated Rooms", copy=False)
    last_import_pricelists = fields.Datetime("Updated Pricelists", copy=False)
    last_import_partners = fields.Datetime("Updated Partners", copy=False)
    last_import_folios = fields.Datetime("Updated Folios", copy=False)
    last_import_payments = fields.Datetime("Updated Payments", copy=False)
    last_import_invoices = fields.Datetime("Updated Invoices", copy=False)
    last_import_products = fields.Datetime("Updated Products", copy=False)
    last_import_board_services = fields.Datetime("Updated BoardServices", copy=False)

    @api.depends("count_total_partners", "count_migrated_partners")
    def _compute_complete_partners(self):
        for record in self:
            if record.count_total_partners == record.count_migrated_partners:
                record.complete_partners = True
            else:
                record.complete_partners = False

    @api.depends("count_total_folios", "count_migrated_folios")
    def _compute_complete_folios(self):
        for record in self:
            if record.count_total_folios == record.count_migrated_folios:
                record.complete_folios = True
            else:
                record.complete_folios = False

    @api.depends("count_total_reservations", "count_migrated_reservations")
    def _compute_complete_reservations(self):
        for record in self:
            if record.count_total_reservations == record.count_migrated_reservations:
                record.complete_reservations = True
            else:
                record.complete_reservations = False

    @api.depends("count_total_checkins", "count_migrated_checkins")
    def _compute_complete_checkins(self):
        for record in self:
            if record.count_total_checkins == record.count_migrated_checkins:
                record.complete_checkins = True
            else:
                record.complete_checkins = False

    @api.depends("count_total_payments", "count_migrated_payments")
    def _compute_complete_payments(self):
        for record in self:
            if record.count_total_payments == record.count_migrated_payments:
                record.complete_payments = True
            else:
                record.complete_payments = False

    @api.depends("count_total_invoices", "count_migrated_invoices")
    def _compute_complete_invoices(self):
        for record in self:
            if record.count_total_invoices == record.count_migrated_invoices:
                record.complete_invoices = True
            else:
                record.complete_invoices = False

    @api.depends("count_tarjet_pricelists", "count_migrated_pricelists", "migrated_pricelist_ids", "migrated_pricelist_ids.pms_pricelist_id")
    def _compute_complete_pricelists(self):
        for record in self:
            if record.count_total_pricelists == record.count_migrated_pricelists and \
                    all(x.pms_pricelist_id for x in record.migrated_pricelist_ids):
                record.complete_pricelists = True
            else:
                record.complete_pricelists = False

    @api.depends("count_migrated_rooms", "migrated_room_ids", "migrated_room_ids.pms_room_id")
    def _compute_complete_rooms(self):
        for record in self:
            if record.count_total_rooms == record.count_migrated_rooms and \
                    all(x.pms_room_id for x in record.migrated_room_ids):
                record.complete_rooms = True
            else:
                record.complete_rooms = False

    @api.depends("count_tarjet_products", "count_migrated_products", "migrated_product_ids", "migrated_product_ids.product_id")
    def _compute_complete_products(self):
        for record in self:
            if record.count_tarjet_products == record.count_migrated_products and \
                    all(x.product_id for x in record.migrated_product_ids):
                record.complete_products = True
            else:
                record.complete_products = False

    @api.depends("count_migrated_board_services", "migrated_board_service_room_type_ids", "migrated_board_service_room_type_ids.board_service_room_type_id")
    def _compute_complete_boards(self):
        for record in self:
            if record.count_total_board_services == record.count_migrated_board_services and \
                    all(x.board_service_room_type_id for x in record.migrated_board_service_room_type_ids):
                record.complete_boards = True
            else:
                record.complete_boards = False

    @api.depends("count_migrated_journals", "migrated_journal_ids", "migrated_journal_ids.account_journal_id")
    def _compute_complete_journals(self):
        for record in self:
            if record.count_total_journals == record.count_migrated_journals and \
                    any(x.account_journal_id for x in record.migrated_journal_ids):
                record.complete_journals = True
            else:
                record.complete_journals = False

    @api.depends("migrated_channel_type_ids", "migrated_channel_type_ids", "migrated_channel_type_ids.channel_type_id")
    def _compute_complete_channels(self):
        for record in self:
            if len(record.migrated_channel_type_ids) == 9 and \
                    all(x.channel_type_id for x in record.migrated_channel_type_ids):
                record.complete_channels = True
            else:
                record.complete_channels = False

    @api.onchange('migration_before_date_d')
    def onchange_migration_before_date_d(self):
        if self.migration_before_date_d:
            self.migration_date_operator = '<'
        else:
            self.migration_date_operator = '>='

    @api.onchange('migration_date_operator', 'migration_date_d')
    def onchange_count_remote_date(self):
        if self.odoo_db and self.odoo_host and self.odoo_port and self.odoo_protocol and self.odoo_user and \
                self.odoo_version and self.odoo_password and self. migration_date_d and self.migration_date_operator:
            try:
                noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
                noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
            except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
                raise ValidationError(err)
            self.count_total_pricelists = noderpc.env['product.pricelist'].search_count([])
            self.count_total_room_types = noderpc.env['hotel.room.type'].search_count([])
            self.count_total_rooms = noderpc.env['hotel.room'].search_count([])
            self.count_total_board_services = noderpc.env['hotel.board.service.room.type'].search_count([])
            self.count_total_journals = noderpc.env['account.journal'].search_count([])
            self.count_total_products = noderpc.env['product.product'].search_count([])
            self.count_total_partners = noderpc.env['res.partner'].search_count([])
            self.count_total_folios = noderpc.env['hotel.folio'].search_count([])
            self.count_total_reservations = noderpc.env['hotel.reservation'].search_count([])
            self.count_total_checkins = noderpc.env['hotel.checkin.partner'].search_count([])
            self.count_total_payments = noderpc.env['account.payment'].search_count([])
            self.count_total_invoices = noderpc.env['account.invoice'].search_count([])

            self.count_migrated_pricelists = len(self.migrated_pricelist_ids)
            self.count_migrated_room_types = len(self.migrated_room_type_ids)
            self.count_migrated_rooms = len(self.migrated_room_ids)
            self.count_migrated_board_services = len(self.migrated_board_service_room_type_ids)
            self.count_migrated_journals = len(self.migrated_journal_ids)
            self.count_migrated_products = len(self.migrated_product_ids)
            self.count_migrated_folios = self.env["pms.folio"].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])
            self.count_migrated_reservations = self.env["pms.reservation"].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])
            self.count_migrated_checkins = self.env["pms.checkin.partner"].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])
            # self.count_migrated_payments = self.env[""].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])
            # self.count_migrated_invoices = self.env[""].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])

            self.count_tarjet_pricelists = noderpc.env['product.pricelist'].search_count([])
            self.count_tarjet_room_types = noderpc.env['hotel.room.type'].search_count([])
            self.count_tarjet_rooms = noderpc.env['hotel.room'].search_count([])
            self.count_tarjet_board_services = noderpc.env['hotel.board.service.room.type'].search_count([])
            self.count_tarjet_products = noderpc.env['product.product'].search_count([]) - self.count_tarjet_room_types
            self.count_tarjet_partners = noderpc.env['res.partner'].search_count([
                '|', ('vat', '!=', False), ('document_number', '!=', False),
            ])
            self.count_tarjet_folios = noderpc.env['hotel.folio'].search_count([
                ("write_date", self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                '|',
                ("room_lines", "!=", False),
                ("service_ids", "!=", False),
            ])
            self.count_tarjet_reservations = noderpc.env['hotel.reservation'].search_count([
                ("write_date", self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT))
            ])
            self.count_tarjet_checkins = noderpc.env['hotel.checkin.partner'].search_count([
                ("write_date", self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT))
            ])
            self.count_tarjet_payments = noderpc.env['account.payment'].search_count([
                ("write_date", self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT))
            ])
            self.count_tarjet_invoices = noderpc.env['account.invoice'].search_count([
                ("write_date", self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT))
            ])

    @api.model
    def create(self, vals):
        try:
            noderpc = odoorpc.ODOO(vals['odoo_host'], vals['odoo_protocol'], vals['odoo_port'])
            noderpc.login(vals['odoo_db'], vals['odoo_user'], vals['odoo_password'])

            vals.update({'odoo_version': noderpc.version})

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        else:
            hotel_id = super().create(vals)
            noderpc.logout()
            return hotel_id

    # PARTNERS ---------------------------------------------------------------------------------------------------------------------------

    def check_vat(self, vat, country_id):
        res_partner = self.env['res.partner']
        # quick and partial off-line checksum validation
        check_func = res_partner.simple_vat_check
        # check with country code as prefix of the TIN
        vat_country, vat_number = res_partner._split_vat(vat)
        if not check_func(vat_country, vat_number):
            # if fails, check with country code from country
            country_code = self.env['res.country'].browse(country_id).code
            if country_code:
                if not check_func(country_code.lower(), vat):
                    return False
            else:
                return False
        return True

    def _prepare_partner_remote_data(self, rpc_res_partner, country_map_ids,
                                     country_state_map_ids, category_map_ids,
                                     document_data):
        # prepare country_id related field
        remote_id = rpc_res_partner['country_id'] and rpc_res_partner['country_id'][0]
        country_id = remote_id and country_map_ids.get(remote_id) or None
        # prepare state_id related field
        remote_id = rpc_res_partner['state_id'] and rpc_res_partner['state_id'][0]
        state_id = remote_id and country_state_map_ids.get(remote_id) or None
        # prepare category_ids related field
        remote_ids = rpc_res_partner['category_id'] and rpc_res_partner['category_id']
        category_ids = remote_ids and [category_map_ids.get(str(r)) for r in remote_ids] or None
        # prepare parent_id related field
        parent_id = rpc_res_partner['parent_id']
        vat = rpc_res_partner['vat']
        if parent_id:
            parent_id = self.env['migrated.partner'].search([
                ('remote_id', '=', parent_id[0]),
                ('migrated_hotel_id', '=', self.id),
            ]).id
            vat = False

        comment = rpc_res_partner['comment'] or False
        # REVIEW: sin el prefijo del pais el check_vat lo da como NO valido, homogeneizar VATS????
        # if vat and not self.check_vat(vat, country_id):
        #     check_vat_msg = 'Invalid VAT number ' + vat + ' for this partner ' + rpc_res_partner['name']
        #     migrated_log = self.env['migrated.log'].create({
        #         'name': check_vat_msg,
        #         'date_time': fields.Datetime.now(),
        #         'migrated_hotel_id': self.id,
        #         'model': 'partner',
        #         'remote_id': rpc_res_partner['id'],
        #     })
        #     _logger.warning('res.partner with ID remote: [%s] LOG #%s: (%s)',
        #                     rpc_res_partner['id'], migrated_log.id, check_vat_msg)
        #     comment = check_vat_msg + "\n" + comment
        #     vat = False

        # TODO: prepare child_ids related field
        return {
            'remote_id': rpc_res_partner['id'],
            'lastname': rpc_res_partner['lastname'],
            'firstname': rpc_res_partner['firstname'],
            'phone': rpc_res_partner['phone'],
            'mobile': rpc_res_partner['mobile'],
            'email': rpc_res_partner['email'],
            'website': rpc_res_partner['website'],
            'lang': rpc_res_partner['lang'],
            'is_company': rpc_res_partner['is_company'],
            'type': rpc_res_partner['type'],
            'street': rpc_res_partner['street'],
            'street2': rpc_res_partner['street2'],
            'is_agency': rpc_res_partner['is_tour_operator'],
            # 'zip_id': rpc_res_partner['zip_id'] and rpc_res_partner['zip_id'][0],
            'zip': rpc_res_partner['is_tour_operator'],
            'city': rpc_res_partner['city'],
            'state_id': state_id,
            'country_id': country_id,
            'nationality_id': country_id,
            'comment': comment,
            'id_numbers': [(0, 0, document_data)] if document_data else False,
            'gender': rpc_res_partner['gender'],
            'birthdate_date': rpc_res_partner['birthdate_date'],
            'category_id': category_ids and [[6, False, category_ids]] or None,
            'parent_id': parent_id if parent_id else False,
            'vat': vat,
            'sale_channel_id': self.default_channel_agency_id.id if rpc_res_partner['is_tour_operator'] else False,
        }

    def action_migrate_partners(self):
        self.ensure_one()

        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        # prepare res.country ids
        _logger.info("Mapping local with remote 'res.country' ids...")
        PartnersMigrated = self.env["migrated.partner"]
        remote_ids = noderpc.env['res.country'].search([])
        remote_xml_ids = noderpc.env['res.country'].browse(
            remote_ids).get_external_id()
        country_map_ids = {}
        for key, value in remote_xml_ids.items():
            # Known Issue: res.country base.an, base.nt, base.tp, base.yu, base.zr are not
            # migrated from Odoo version 10 to version 11
            res_country_id = self.env['ir.model.data'].xmlid_to_res_id(value)
            country_map_ids.update({int(key): res_country_id})

        # prepare res.country.state ids
        _logger.info("Mapping local with remote 'res.country.state' ids...")
        remote_ids = noderpc.env['res.country.state'].search([])
        remote_xml_ids = noderpc.env['res.country.state'].browse(
            remote_ids).get_external_id()
        country_state_map_ids = {}
        for key, value in remote_xml_ids.items():
            res_country_state_id = self.env['ir.model.data'].xmlid_to_res_id(value)
            country_state_map_ids.update({int(key): res_country_state_id})

        # prepare res.partner.category ids
        _logger.info("Mapping local with remote 'res.partner.category' ids...")
        remote_ids = noderpc.env['res.partner.category'].search([])
        remote_records = noderpc.env['res.partner.category'].browse(remote_ids)
        category_map_ids = {}
        for record in remote_records:
            if record.parent_id:
                res_partner_category = self.env['res.partner.category'].search([
                    ('name', '=', record.name),
                    ('parent_id.name', '=', record.parent_id.name),
                ])

            else:
                res_partner_category = self.env['res.partner.category'].search([
                    ('name', '=', record.name),
                ])
            if not res_partner_category:
                if record.parent_id:
                    parent_category_id = self.env['res.partner.category'].search([('name', '=', record.name)])
                    if not parent_category_id:
                        parent = self.env['res.partner.category'].create({'name': record.parent_id.name})
                    res_partner_category = self.env['res.partner.category'].create({
                        'name': record.name,
                        'parent_id': parent.id,
                    })
                else:
                    res_partner_category = self.env['res.partner.category'].create({'name': record.name})
            res_partner_category_id = res_partner_category[0].id
            category_map_ids.update({record.id: res_partner_category_id})

        # prepare partners of interest
        _logger.info("Preparing 'res.partners' of interest...")
        partner_remote_fields = [
            'id',
            'document_number',
            'document_type',
            'is_company',
            'is_tour_operator',
            'document_expedition_date',
            'vat',
            'country_id',
            'state_id',
            'category_id',
            'parent_id',
            'lastname',
            'firstname',
            'phone',
            'mobile',
            'email',
            'website',
            'lang',
            'type',
            'street',
            'street2',
            'zip',
            'city',
            'comment',
            'gender',
            'birthdate_date',
        ]

        partners_migrated_remote_ids = []
        partners_migrated = PartnersMigrated.search([("migrated_hotel_id", "=", self.id)])
        if partners_migrated:
            partners_migrated_remote_ids = partners_migrated.mapped("remote_id")
        # First, import remote partners without contacts (parent_id is not set)
        _logger.info("Migrating 'res.partners' without parent_id...")
        remote_partners = noderpc.env['res.partner'].search_read([
            ('id', 'not in', partners_migrated_remote_ids),
            ('parent_id', '=', False),
            ('user_ids', '=', False),
            ('write_date', self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            '|', ('active', '=', True), ('active', '=', False),
            '|', ('vat', '!=', False), ('document_number', '!=', False),
        ], partner_remote_fields)
        total_records = len(remote_partners)
        count = 0
        total_count = 0
        for remote_res_partner in remote_partners:

            _logger.info('(%s/%s) User #%s started migration of res.partner with remote ID: [%s]',
                         total_records, count, self._uid, remote_res_partner["id"])
            self.with_delay().migration_partner(remote_res_partner, country_map_ids, country_state_map_ids, category_map_ids)
            count += 1
            total_count += 1

        # Second, import remote partners with contacts (already created in the previous step)
        # TODO
        _logger.info("Migrating 'res.partners' with parent_id...")
        remote_partners = noderpc.env['res.partner'].search_read([
            ('id', 'not in', partners_migrated_remote_ids),
            ('parent_id', '!=', False),
            ('user_ids', '=', False),
            ('create_date', self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            '|', ('active', '=', True), ('active', '=', False),
        ], partner_remote_fields)
        total_records = len(remote_partners)
        count = 0
        for remote_res_partner in remote_partners:
            _logger.info('(%s/%s) User #%s started migration of res.partner with remote ID: [%s]',
                         total_records, count, self._uid, remote_res_partner["id"])
            self.with_delay().migration_partner(remote_res_partner, country_map_ids, country_state_map_ids, category_map_ids)
            count += 1
            total_count += 1
        self.last_import_partners = self.fields.Datetime.now()
        self.count_migrated_partners = self.env["migrated.partner"].search_count([("migrated_hotel_id", "=", self.id)])
        noderpc.logout()

    def migration_partner(self, rpc_res_partner, country_map_ids, country_state_map_ids, category_map_ids):
        context_no_mail = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
        }
        PartnersMigrated = self.env["migrated.partner"]
        is_company = rpc_res_partner['is_company']
        is_ota = rpc_res_partner["is_tour_operator"]
        # search document number
        document_data = False
        migrated_res_partner = False
        if rpc_res_partner['document_number'] and rpc_res_partner['document_type'] and not is_company and not is_ota:
            category_id = self.env["res.partner.id_category"].search([("code", "=", rpc_res_partner['document_type'])]).id
            partner_document = self.env["res.partner.id_number"].search([
                ("category_id", "=", category_id),
                ("name", "=", rpc_res_partner['document_number'])
            ])
            if partner_document:
                migrated_res_partner = partner_document.partner_id
                PartnersMigrated.create({
                    "date_time": fields.Datetime.now(),
                    "migrated_hotel_id": self.id,
                    "remote_id": rpc_res_partner["id"],
                    "partner_id": partner_document.partner_id.id
                })
            else:
                document_data = {
                    "category_id": category_id,
                    "name": rpc_res_partner["document_number"],
                    "valid_from": rpc_res_partner["document_expedition_date"],
                }
        if migrated_res_partner:
            _logger.info('User #%s found with identity document: [%s]',
                         rpc_res_partner["id"], rpc_res_partner['document_number'])
        elif document_data or rpc_res_partner["vat"] and (is_company or is_ota):
            vals = self._prepare_partner_remote_data(
                rpc_res_partner,
                country_map_ids,
                country_state_map_ids,
                category_map_ids,
                document_data,
            )
            migrated_res_partner = self.env['res.partner'].with_context(context_no_mail).create(vals)
            PartnersMigrated.create({
                "date_time": fields.Datetime.now(),
                "migrated_hotel_id": self.id,
                "remote_id": rpc_res_partner["id"],
                "partner_id": migrated_res_partner.id
            })
            _logger.info('User #%s migrated res.partner with ID [local, remote]: %s',
                         migrated_res_partner.id, rpc_res_partner["id"])
        else:
            PartnersMigrated.create({
                "date_time": fields.Datetime.now(),
                "migrated_hotel_id": self.id,
                "remote_id": rpc_res_partner["id"],
                "partner_id": False,
            })
            _logger.info('Partner without documentation: [%s] (not migrated)',
                         rpc_res_partner["id"])
    # FOLIOS ---------------------------------------------------------------------------------------------------------------------------

    def _prepare_folio_remote_data(self, rpc_hotel_folio,
                                   res_users_map_ids, category_map_ids,
                                   reservations_folio, reservation_lines_folio,
                                   services_folio, service_lines_folio,
                                   remote_checkin_partners, remote_bindings):
        # search res_partner id
        remote_id = rpc_hotel_folio['partner_id'] and rpc_hotel_folio['partner_id'][0]
        res_partner = self.env['migrated.partner'].search([
            ('remote_id', '=', remote_id),
            ('migrated_hotel_id', '=', self.id),
        ]).partner_id or False
        if not res_partner:
            # REVIEW: if partner not found, search name??
            partner_name = rpc_hotel_folio['partner_id'][1]
            partner_email = rpc_hotel_folio['email']
            partner_mobile = rpc_hotel_folio['mobile'] if rpc_hotel_folio['mobile'] else rpc_hotel_folio['phone']
        else:
            partner_name = res_partner.name
            partner_email = res_partner.email
            partner_mobile = res_partner.mobile if res_partner.mobile else res_partner.phone

        # search res_partner invoice id
        res_partner_invoice_id = False
        remote_id = rpc_hotel_folio['partner_invoice_id'] and rpc_hotel_folio['partner_invoice_id'][0]
        res_partner_invoice = self.env['migrated.partner'].search([
            ('remote_id', '=', remote_id),
            ('migrated_hotel_id', '=', self.id),
        ]).partner_id
        if res_partner_invoice:
            res_partner_invoice_id = res_partner_invoice.id
        else:
            if res_partner:
                res_partner_invoice_id = res_partner.id
            else:
                # REVIEW: Atención! Sería una factura simplificada pero en la migración no se debería dar este caso en un folio facturado
                res_partner_invoice_id = False

        # search res_users ids
        remote_id = rpc_hotel_folio['user_id'] and rpc_hotel_folio['user_id'][0]
        res_user_id = remote_id and res_users_map_ids.get(remote_id)
        remote_id = rpc_hotel_folio['create_uid'] and rpc_hotel_folio['create_uid'][0]
        res_create_uid = remote_id and res_users_map_ids.get(remote_id)

        # prepare category_ids related field
        remote_ids = rpc_hotel_folio['segmentation_ids'] and rpc_hotel_folio['segmentation_ids']
        category_ids = remote_ids and [category_map_ids.get(str(r)) for r in remote_ids] or False

        # Prepare pricelist
        remote_id = rpc_hotel_folio['pricelist_id'][0]
        pricelist_id = self.env["migrated.pricelist"].search([("remote_id", "=", remote_id), ("migrated_hotel_id", "=", self.id)]).pms_pricelist_id.id

        # prepare default state value
        state = 'confirm'
        if rpc_hotel_folio['state'] != 'sale':
            state = rpc_hotel_folio['state']

        # Prepare service in folio without reservation assigned
        services_vals = False
        if rpc_hotel_folio['service_ids']:
            remote_services = [ser for ser in services_folio if not ser["ser_room_line"]]
            for remote_service in remote_services:
                remote_service_lines = [line for line in service_lines_folio if line["service_id"] == remote_service["id"]]
                services_vals = [(0, 0, self._prepare_migrate_services(remote_service, remote_service_lines))]

        vals = {
            'remote_id': rpc_hotel_folio['id'],
            'name': self.folio_prefix + rpc_hotel_folio['name'],
            'partner_name': partner_name,
            'mobile': partner_mobile,
            'email': partner_email,
            'pricelist_id': pricelist_id,
            'service_ids': services_vals,
            'segmentation_ids': category_ids and [[6, False, category_ids]] or False,
            'reservation_type': rpc_hotel_folio['reservation_type'],
            # TODO: Mover a reservations: 'internal_comment': rpc_hotel_folio['customer_notes'],
            'internal_comment': rpc_hotel_folio['internal_comment'],
            'state': state,
            'cancelled_reason': rpc_hotel_folio['cancelled_reason'],
            'date_order': rpc_hotel_folio['date_order'],
            'confirmation_date': rpc_hotel_folio['confirmation_date'],
            'create_date': rpc_hotel_folio['create_date'],
            'pms_property_id': self.pms_property_id.id,
            'user_id': res_user_id,
            'create_uid': res_create_uid,
        }
        if res_partner:
            vals.update({
                'partner_id': res_partner.id,
                'partner_invoice_ids': [(4, res_partner_invoice_id)],
            })
        if rpc_hotel_folio['reservation_type'] == 'out':
            vals.update({'closure_reason_id': self.dummy_closure_reason_id.id})

        if rpc_hotel_folio['room_lines']:
            reservations_vals = self._prepare_folio_reservations(
                reservations_folio, reservation_lines_folio,
                services_folio, service_lines_folio, remote_checkin_partners, res_users_map_ids)
            vals.update({'reservation_ids': reservations_vals})

        # Prepare channel and binding
        # Wubook
        if reservations_folio and reservations_folio[0]['external_id']:
            reservation = reservations_folio[0]
            binding = [b for b in remote_bindings if b['external_id'] == reservation['external_id']][0]
            remote_ota_id = reservation['ota_id'] and reservation['ota_id'][1] or None
            if remote_ota_id:
                vals["channel_type_id"] = self.default_ota_channel.id
                if remote_ota_id == "Booking.com":
                    vals["agency_id"] = self.booking_agency.id
                if remote_ota_id == "Expedia":
                    vals["agency_id"] = self.expedia_agency.id
                if remote_ota_id == "HotelBeds":
                    vals["agency_id"] = self.hotelbeds_agency.id
            vals["reservation_origin_code"] = binding['ota_reservation_id']
            binding_vals = {
                'backend_id': self.backend_id.id,
                'external_id': binding['external_id'],
                'wubook_status': binding['channel_status'],
            }
            vals.update({'channel_wubook_bind_ids': [(0, False, binding_vals)]})
        # Not Wubook
        else:
            remote_id = rpc_hotel_folio['tour_operator_id'] and rpc_hotel_folio['tour_operator_id'][0]
            agency = remote_id and self.env["migrated.partner"].search([("remote_id", "=", remote_id)]).partner_id
            if remote_id:
                vals["agency_id"] = agency.id
                vals["channel_type_id"] = agency.sale_channel_id.id
            else:
                vals["agency_id"] = False
                vals["channel_type_id"] = self.env["migrated.channel.type"].search([("remote_name", "=", rpc_hotel_folio['channel_type']), ("migrated_hotel_id", "=", self.id)]).channel_type_id.id

        return vals

    def action_migrate_folios(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

        try:
            # prepare res.users ids
            _logger.info("Mapping local with remote 'res.users' ids...")
            remote_ids = noderpc.env['res.users'].search([])
            remote_records = noderpc.env['res.users'].browse(remote_ids)
            res_users_map_ids = {}
            for record in remote_records:
                res_users = self.env['res.users'].search([
                    ('login', '=', record.login),
                ])
                res_users_id = res_users.id if res_users else self._context.get('uid', self._uid)
                res_users_map_ids.update({record.id: res_users_id})

            # prepare res.partner.category ids
            _logger.info("Mapping local with remote 'res.partner.category' ids...")
            remote_ids = noderpc.env['res.partner.category'].search([])
            remote_records = noderpc.env['res.partner.category'].browse(remote_ids)
            category_map_ids = {}
            for record in remote_records:
                if record.parent_ids:
                    res_partner_category = self.env['res.partner.category'].search([
                        ('name', '=', record.name),
                        ('parent_id.name', '=', record.parent_id.name),
                    ])
                else:
                    res_partner_category = self.env['res.partner.category'].search([
                        ('name', '=', record.name)
                    ])
                if res_partner_category:
                    category_map_ids.update({record.id: res_partner_category.id})
                else:
                    parent = False
                    if record.parent_id:
                        parent = self.env['res.partner.category'].create({'name': record.parent_id.name})
                    res_partner_category = self.env['res.partner.category'].create({
                        'name' : record.name,
                        'parent_id': parent.id if parent else False,
                    })
                    category_map_ids.update({record.id: res_partner_category.id})

            # prepare folios of interest
            _logger.info("Preparing 'hotel.folio' of interest...")

            remote_hotel_folios = noderpc.env['hotel.folio'].search_read([
                ("write_date", self.migration_date_operator, self.migration_date_d.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                '|',
                ("room_lines", "!=", False),
                ("service_ids", "!=", False),
            ],
            [
                "id",
                "name",
                "partner_id",
                "email",
                "phone",
                "mobile",
                "pricelist_id",
                "tour_operator_id",
                "service_ids",
                "segmentation_ids",
                "reservation_type",
                "channel_type",
                "internal_comment",
                "state",
                "cancelled_reason",
                "date_order",
                "confirmation_date",
                "create_date",
                "user_id",
                "create_uid",
                "room_lines",
                "partner_invoice_id",
            ]) or []
            _logger.info("%s Folios to migrate", len(remote_hotel_folios))

            _logger.info("Preparing 'hotel.reservation' of interest...")

            remote_hotel_reservations = noderpc.env['hotel.reservation'].search_read([
                ("folio_id", "in", [fol['id'] for fol in remote_hotel_folios]),
            ],
            [
                'id',
                'folio_id',
                'room_id',
                'room_type_id',
                'discount',
                'checkin',
                'checkout',
                'arrival_hour',
                'departure_hour',
                'board_service_room_id',
                'to_assign',
                'state',
                'cancelled_reason',
                'out_service_description',
                'adults',
                'children',
                'splitted',
                'parent_reservation',
                'overbooking',
                'channel_type',
                'call_center',
                'external_id',
                'ota_id',
                'reservation_line_ids',
                'checkin_partner_ids',
                'service_ids',
                'create_uid',
                'last_updated_res',
                'ota_id',
            ],) or []
            # Reservation Bindings
            remote_bindings = noderpc.env['channel.hotel.reservation'].search_read([
                ("odoo_id", "in", [res['id'] for res in remote_hotel_reservations]),
            ],
            [
                'id',
                'odoo_id',
                'ota_id',
                'ota_reservation_id',
                'channel_status',
                'external_id',
            ])
            _logger.info("%s Reservations to migrate", len(remote_hotel_reservations))

            _logger.info("Preparing 'hotel.reservetion.line' of interest...")

            remote_hotel_reservation_lines = noderpc.env['hotel.reservation.line'].search_read([
                ("reservation_id", "in", [r['id'] for r in remote_hotel_reservations]),
            ],
            [
                'id',
                'reservation_id',
                'room_id',
                'date',
                'discount',
                'cancel_discount',
                'price'
            ]) or []

            _logger.info("%s Reservation lines to migrate", len(remote_hotel_reservation_lines))
            _logger.info("Preparing 'hotel.service' of interest...")

            remote_hotel_services = noderpc.env['hotel.service'].search_read([
                '|',
                ("folio_id", "in", [folio['id'] for folio in remote_hotel_folios]),
                ("ser_room_line", "in", [reservation['id'] for reservation in remote_hotel_reservations]),
            ],
            [
                'id',
                'folio_id',
                'ser_room_line',
                'product_id',
                'name',
                'is_board_service',
                'discount',
                'channel_type',
                'service_line_ids',
            ])

            _logger.info("%s Services to migrate", len(remote_hotel_services))
            _logger.info("Preparing 'hotel.service.line' of interest...")

            remote_hotel_service_lines = noderpc.env['hotel.service.line'].search_read([
                ("service_id", "in", [service['id'] for service in remote_hotel_services]),
            ], ["service_id", "date", "create_date", "day_qty", "price_unit"])

            _logger.info("%s Service lines to migrate", len(remote_hotel_service_lines))
            _logger.info("Preparing 'hotel.checkin.partner' of interest...")

            remote_checkin_partners = noderpc.env['hotel.checkin.partner'].search_read(
                [('reservation_id', 'in', [r['id'] for r in remote_hotel_reservations])],
                ['reservation_id', 'partner_id', 'enter_date', 'exit_date', 'state']
            )
            _logger.info("%s Checkin partners to migrate", len(remote_checkin_partners))
            # TODO: Revisar Folios ya migrados
            # folios_migrated_remote_ids = []
            # folios_migrated = self.env["pms.folio"].search([("pms_property_id", "=", self.pms_property_id.id)])
            # if folios_migrated:
            #     folios_migrated_remote_ids = folios_migrated.mapped("remote_id")
            # remote_hotel_folio_ids = list(set(remote_hotel_folios) - set(folios_migrated_remote_ids))
            remote_folio_ids = self.env["pms.folio"].search([("pms_property_id", "=", self.pms_property_id.id)]).mapped("remote_id")
            count = 0
            errors_count = 0
            total = len(remote_hotel_folios)
            _logger.info("Migrating 'hotel.folio'... Number of Folios: %s", total)
            for remote_hotel_folio in remote_hotel_folios:
                if remote_hotel_folio['id'] in remote_folio_ids:
                    _logger.info("Folio %s already migrated", remote_hotel_folio['id'])
                    continue
                _logger.info('Started migration of hotel.folio with remote ID: [%s]', remote_hotel_folio)
                reservations_folio = [res for res in remote_hotel_reservations if res['folio_id'][0] == remote_hotel_folio['id']]
                reservation_lines_folio = [res for res in remote_hotel_reservation_lines if res['reservation_id'][0] in [item["id"] for item in reservations_folio]]
                services_folio = [res for res in remote_hotel_services if res['folio_id'][0] == remote_hotel_folio['id']]
                service_lines_folio = [res for res in remote_hotel_service_lines if res['service_id'][0] in [item["id"] for item in services_folio]]
                checkins_partners_folio = [res for res in remote_checkin_partners if res['reservation_id'][0] in [item["id"] for item in reservations_folio]]
                self.with_delay().migration_folio(
                    remote_hotel_folio,
                    res_users_map_ids,
                    category_map_ids,
                    reservations_folio,
                    reservation_lines_folio,
                    services_folio,
                    service_lines_folio,
                    checkins_partners_folio,
                    remote_bindings,
                )
                count += 1
                _logger.info('Finished migration of hotel.folio with remote ID: [%s]', remote_hotel_folio)
                _logger.info('Migrated %s of %s hotel.folio', count, total)
                _logger.info('Errors: %s', errors_count)
                _logger.info('==============================================================')

            self.count_migrated_folios = self.env["pms.folio"].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])
            self.count_migrated_reservations = self.env["pms.reservation"].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])
            self.count_migrated_checkins = self.env["pms.checkin.partner"].search_count([("remote_id", "!=", False), ("pms_property_id", "=", self.pms_property_id.id)])

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        else:
            noderpc.logout()

    def migration_folio(self, remote_hotel_folio, res_users_map_ids, category_map_ids, reservations, reservation_lines, services, service_lines, remote_checkin_partners, remote_bindings):
        vals = self._prepare_folio_remote_data(
            remote_hotel_folio,
            res_users_map_ids,
            category_map_ids,
            reservations,
            reservation_lines,
            services,
            service_lines,
            remote_checkin_partners,
            remote_bindings,
        )
        # disable mail feature to speed-up migration
        context_no_mail = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'connector_no_export': True,
        }
        self.env['pms.folio'].with_context(
            context_no_mail
        ).create(vals)

    # RESERVATIONS ---------------------------------------------------------------------------------------------------------------------------

    def _prepare_reservation_remote_data(self, reservation, reservation_lines, services, service_lines, remote_checkin_partners, res_users_map_ids):

        # prepare hotel_room_type related field
        remote_id = reservation['room_type_id'] and reservation['room_type_id'][0]
        room_type_id = self.env["migrated.room.type"].search([("remote_id", "=", remote_id), ("migrated_hotel_id", "=", self.id)]).pms_room_type_id.id
        # prepare hotel_room related field
        remote_id = reservation['room_id'] and reservation['room_id'][0]
        preferred_room_id = remote_id and self.env["migrated.room"].search([("remote_id", "=", remote_id), ("migrated_hotel_id", "=", self.id)]).pms_room_id.id
        # prepare channel_ota_info related field
        # remote_id = reservation['wchannel_id'] and reservation['wchannel_id'][0] or None
        # ota_id = remote_id and ota_map_ids.get(remote_id) or None

        # search res_users ids
        remote_id = reservation['create_uid'] and reservation['create_uid'][0]
        res_create_uid = remote_id and res_users_map_ids.get(remote_id)

        # prepare checkins
        remote_ids = reservation['checkin_partner_ids'] and reservation['checkin_partner_ids']
        hotel_checkin_partners = [checkin for checkin in remote_checkin_partners if checkin['id'] in remote_ids]
        checkins_cmds = []

        for hotel_checkin in hotel_checkin_partners:
            partner_id = self.env["migrated.partner"].search([("remote_id", "=", hotel_checkin['partner_id'][0]), ("migrated_hotel_id", "=", self.id)]).partner_id.id

            state = hotel_checkin["state"]
            if state == "booking":
                state = "onboard"
            if state == "cancelled":
                state = "cancel"

            checkins_cmds.append((0, False, {
                'partner_id': partner_id,
                'arrival': fields.Date.from_string(hotel_checkin['enter_date']).strftime(DEFAULT_SERVER_DATE_FORMAT),
                'departure': fields.Date.from_string(hotel_checkin['exit_date']).strftime(DEFAULT_SERVER_DATE_FORMAT),
                'state': state,
            }))

        # prepare_reservation_lines
        remote_ids = reservation['reservation_line_ids'] and reservation['reservation_line_ids']
        hotel_reservation_lines = [line for line in reservation_lines if line['id'] in remote_ids]

        reservation_line_cmds = []
        for reservation_line in hotel_reservation_lines:
            room_line_id = self.env["migrated.room"].search([("remote_id", "=", reservation_line['room_id'][0]), ("migrated_hotel_id", "=", self.id)]).pms_room_id.id
            reservation_line_cmds.append((0, False, {
                'date': reservation_line['date'],
                'price': reservation_line['price'],
                'discount': reservation_line['discount'],
                'cancel_discount': reservation_line['cancel_discount'],
                'room_id': room_line_id,
            }))

        board_service = False
        if reservation['board_service_room_id']:
            board_service = self.env["migrated.board.service.room.type"].search([
                ("remote_id", "=", reservation['board_service_room_id'][0]),
                ("migrated_hotel_id", "=", self.id)])
        board_service_room_id = board_service.board_service_room_type_id.id if board_service else False

        # TODO 'splitted': reservation['splitted']
        # if reservation['parent_reservation']:
        #     parent_reservation_id = self.env['hotel.reservation'].search([
        #         ('remote_id', '=', reservation['parent_reservation'][0])
        #     ]).id or None
        #     vals.update({'parent_reservation': parent_reservation_id})

        # TODO 'call_center': reservation['call_center'],

        # Mapper Cancel state
        state = reservation['state']
        if reservation['state'] == 'cancelled':
            state = 'cancel'
        elif reservation['state'] == 'booking':
            state = 'onboard'

        services_vals = False
        if reservation['service_ids'] and state != "cancel":
            remote_records = [service for service in services if service['id'] in reservation['service_ids']]
            for remote_service in remote_records:
                lines = [line for line in service_lines if line['service_id'][0] in remote_service['service_line_ids']]
                services_vals = [(0, 0, self._prepare_migrate_services(remote_service, lines))]

        # prepare pms.folio.reservation_ids
        vals = {
            # folio_id': folio_id,
            'remote_id': reservation['id'],
            'room_type_id': room_type_id,
            'preferred_room_id': preferred_room_id,
            'checkin': fields.Date.from_string(
                reservation['checkin']).strftime(DEFAULT_SERVER_DATE_FORMAT),
            'checkout': fields.Date.from_string(
                reservation['checkout']).strftime(DEFAULT_SERVER_DATE_FORMAT),
            'arrival_hour': reservation['arrival_hour'],
            'departure_hour': reservation['departure_hour'],
            'board_service_room_id': board_service_room_id,
            # 'nights': reservation['nights'],
            'to_assign': reservation['to_assign'],
            # 'to_send': reservation['to_send'],
            'state': state,
            'cancelled_reason': reservation['cancelled_reason'],
            'out_service_description': reservation['out_service_description'],
            'adults': min(reservation['adults'], self.env['pms.room'].browse(preferred_room_id).capacity),
            'children': reservation['children'],
            'overbooking': reservation['overbooking'],
            'service_ids': services_vals,
            'reservation_line_ids': reservation_line_cmds,
            'create_uid': res_create_uid,
        }

        if len(checkins_cmds) > 0:
            vals['checkin_partner_ids'] = checkins_cmds

        return vals

    def _prepare_folio_reservations(self, reservations, reservation_lines, services, service_lines, remote_checkin_partners, res_users_map_ids):
        # TODO: OTAs de Booking como Agencias

        # prepare channel.ota.info ids
        # _logger.info("Mapping local with remote 'channel.ota.info' ids...")
        # remote_ids = noderpc.env['wubook.channel.info'].search([])
        # remote_records = noderpc.env['wubook.channel.info'].browse(remote_ids)
        # ota_map_ids = {}
        # for record in remote_records:
        #     res_ota_id = self.env['channel.ota.info'].search([
        #         ('ota_id', '=', int(record.wid)),
        #     ]).id
        #     ota_map_ids.update({record.id: res_ota_id})

        # prepare reservation of interest
        _logger.info("Preparing folio reservations")
        reservation_vals = [] if reservations else False
        for remote_hotel_reservation in reservations:
            # REVIEW: reservas ya migradas
            # migrated_hotel_reservation = self.env['pms.reservation'].search([
            #     ('remote_id', '=', remote_hotel_reservation_id),
            #     ('pms_property_id', '=', self.pms_property_id.id),
            # ]) or None

            # if not migrated_hotel_reservation:
            _logger.info('User #%s started migration of hotel.reservation with remote ID: [%s]',
                         self._uid, remote_hotel_reservation["id"])
            lines = [line for line in reservation_lines if line["reservation_id"][0] == remote_hotel_reservation["id"]]
            res_services = [service for service in services if service["ser_room_line"] and service["ser_room_line"][0] == remote_hotel_reservation["id"]]
            res_service_lines = [ser_line for ser_line in service_lines if ser_line["service_id"][0] in [service["id"] for service in res_services]]
            reservation_vals.append((0, 0, self._prepare_reservation_remote_data(
                # hotel_folio_id,
                remote_hotel_reservation,
                lines,
                res_services,
                res_service_lines,
                remote_checkin_partners,
                res_users_map_ids,
                # room_type_map_ids,
                # room_map_ids,
                # ota_map_ids,
            )))
            # migrated_hotel_reservation = self.env['hotel.reservation'].with_context(context_no_mail).create(vals)

            # _logger.info('User #%s migrated hotel.reservation with ID [local, remote]: [%s, %s]',
            #              self._uid, migrated_hotel_reservation.id, remote_hotel_reservation_id)

        return reservation_vals

    # SERVICES ---------------------------------------------------------------------------------------------------------------------------

    def _prepare_migrate_services(self, remote_service, remote_service_lines):
        try:
            self.ensure_one()
            # Check product per_day
            remote_id = remote_service["product_id"][0]
            product = self.env["migrated.product"].search([
                ("remote_id", "=", remote_id),
                ("migrated_hotel_id", "=", self.id),
            ]).product_id

            # Prepare service lines
            service_lines_cmds = False
            if len(remote_service_lines) > 0:
                service_lines_cmds = []
                for line in remote_service_lines:
                    date = line["date"]
                    if not date:
                        date = remote_service_lines["create_date"]
                    date = fields.Date.from_string(date).strftime(DEFAULT_SERVER_DATE_FORMAT)
                    service_lines_cmds.append((0, 0, {
                        'date': date,
                        'day_qty': line["day_qty"],
                        'price_unit': line["price_unit"],
                    }))

            service_vals = {
                'remote_id': remote_service['id'],
                'product_id': product.id if product else self.dummy_product_id.id,
                'per_day': product.per_day,
                'name': remote_service['name'],
                'discount': remote_service['discount'],
                'channel_type': remote_service['channel_type'] or 'door',
                'is_board_service': remote_service['is_board_service'],
                'service_line_ids': service_lines_cmds,
            }
            return service_vals
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

    # PAYMENTS ---------------------------------------------------------------------------------------------------------------------------

    def action_migrate_payments(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

        try:
            # Funtion to group by journal
            def journal_func(k):
                return k['journal_id']

            # Funtion to group by date
            def date_func(k):
                return k['payment_date']

            # Prepare Users
            _logger.info("Mapping local with remote 'res.users' ids...")
            remote_ids = noderpc.env['res.users'].search([])
            remote_records = noderpc.env['res.users'].browse(remote_ids)
            res_users_map_ids = {}
            for record in remote_records:
                res_users = self.env['res.users'].search([
                    ('login', '=', record.login),
                ])
                res_users_id = res_users.id if res_users else self._context.get('uid', self._uid)
                res_users_map_ids.update({record.id: res_users_id})

            migrated_folio_ids = self.env["pms.folio"].search([
                ("pms_property_id", "=", self.pms_property_id.id)
            ]).mapped("remote_id")
            remote_payment_vals = noderpc.env['account.payment'].search_read(
                [
                    '|',
                    ("folio_id", "=", False),
                    ("folio_id", "in", migrated_folio_ids)
                ],
                [
                    "payment_type",
                    "partner_type",
                    "partner_id",
                    "amount",
                    "journal_id",
                    "destination_journal_id",
                    "payment_date",
                    "communication",
                    "folio_id",
                    "state",
                    "create_uid"
                ],
            )
            total = len(remote_payment_vals)
            _logger.info("Total Number of Payments: %s", total)
            remote_payment_by_journal_vals = sorted(remote_payment_vals, key=journal_func)
            migrated_journals = []
            count = 0
            for remote_journal, journal_payments in groupby(remote_payment_by_journal_vals, journal_func):
                if remote_journal[0] in migrated_journals:
                    continue
                journal_id = self.env["migrated.journal"].search([
                    ("migrated_hotel_id", "=", self.id),
                    ("remote_id", "=", remote_journal[0]),
                ]).account_journal_id.id
                if not journal_id:
                    _logger.info("Journal No MAPPED: %s", remote_journal[1])
                    continue
                journal = self.env["account.journal"].browse(journal_id)
                remote_journal_ids = self.env["migrated.journal"].search([("account_journal_id", "=", journal_id)]).mapped("remote_id")
                migrated_journals.extend(remote_journal_ids)

                # compute ending balance
                latest_statement = self.env['account.bank.statement'].search([('journal_id', '=', journal_id)], limit=1)
                if latest_statement:
                    balance = latest_statement.balance_end_real
                else:
                    balance = 0

                journal_payments_tarjet = list(filter(lambda x: x["journal_id"][0] in remote_journal_ids, remote_payment_vals))
                journal_payments_tarjet = sorted(journal_payments_tarjet, key=date_func)
                for date_str, payments in groupby(journal_payments_tarjet, key=date_func):
                    date = fields.Datetime.from_string(date_str)
                    # Some payment are garbage, so we skip them (know by old dates)
                    if date < (datetime.datetime.now() - datetime.timedelta(days=2000)):
                        continue
                    line_vals = []
                    st_values = {
                        "journal_id": journal_id,
                        "user_id": self.env.user.id,
                        "pms_property_id": self.pms_property_id.id,
                        "name": date_str,
                        "balance_start": balance,
                        "move_line_ids": line_vals,
                        "date": date,
                    }
                    context_no_mail = {
                        'tracking_disable': True,
                        'mail_notrack': True,
                        'mail_create_nolog': True,
                        'company_id': self.pms_property_id.company_id.id,
                    }
                    statement = (
                        self.env["account.bank.statement"]
                        .with_context(context_no_mail)
                        .sudo()
                        .create(st_values)
                    )
                    _logger.info('NEW STATEMENT: %s',
                                 date_str)
                    for payment in payments:
                        _logger.info('Normal Payments')
                        balance += self.create_payment_migration(payment, res_users_map_ids, remote_journal, date_str, journal, statement)
                        count += 1
                        _logger.info('(%s/%s) Migrated account.payment with ID (remote): %s',
                                     count, total, payment['id'])

                    # Add payments internal transfer with same date and journal like destination journal
                    destination_payment_vals = list(filter(lambda x: x["payment_type"] == "transfer" and x["payment_date"] == date and x["destination_journal_id"][0] == remote_journal[0], journal_payments_tarjet))
                    for pay in destination_payment_vals:
                        _logger.info('Destination Journal Payments')
                        balance += self.create_payment_migration(pay, res_users_map_ids, remote_journal, date_str, journal, statement)
                        count += 1
                        _logger.info('(%s/%s) Migrated account.payment with ID (remote): %s',
                                     count, total, payment['id'])
                    statement.write({
                        "balance_end_real": balance,
                        "move_line_ids": line_vals,
                        "date_done": fields.Date.from_string(date_str).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    })
                    statement.button_post()
                    # statement.button_validate()

        except (ValueError, ValidationError, Exception) as err:
            migrated_log = self.env['migrated.log'].create({
                'name': err,
                'date_time': fields.Datetime.now(),
                'migrated_hotel_id': self.id,
                'model': 'payment',
            })
            _logger.error('ERROR account.payment with LOG #%s: (%s)',
                          migrated_log.id, err)

    def create_payment_migration(self, payment, res_users_map_ids, remote_journal, date_str, journal, statement):
        remote_id = payment['create_uid'] and payment['create_uid'][0]
        res_create_uid = remote_id and res_users_map_ids.get(remote_id)
        if payment["partner_id"]:
            partner_id = self.env["migrated.partner"].search([
                ("remote_id", "=", payment['partner_id'][0]),
                ("migrated_hotel_id", "=", self.id)
            ]).partner_id.id or False
        else:
            partner_id = False
        remote_folio_id = payment["folio_id"] and payment["folio_id"][0]
        if remote_folio_id:
            folio_id = self.env["pms.folio"].search([
                ("remote_id", "=", remote_folio_id),
                ("pms_property_id", "=", self.pms_property_id.id),
            ], limit=1).id or False
        else:
            folio_id = False
        payment_ref = payment["communication"]
        if not payment_ref:
            if payment["folio_id"]:
                payment_ref = payment["folio_id"][1]
            else:
                payment_ref = "Transaccion"

        # Check Payment
        if payment["payment_type"] == "inbound":
            amount = payment["amount"]
        elif payment["payment_type"] == "outbound":
            amount = -payment["amount"]
        elif payment["payment_type"] == "transfer":
            if payment["destination_journal_id"][0] == remote_journal[0]:
                amount = payment["amount"]
            elif payment["journal_id"][0] == remote_journal[0]:
                amount = -payment["amount"]
        vals = {
            "date": fields.Date.from_string(date_str).strftime(DEFAULT_SERVER_DATE_FORMAT),
            "amount": amount,
            "partner_id": partner_id,
            "payment_ref": payment_ref,
            "journal_id": journal.id,
            "counterpart_account_id": journal.suspense_account_id.id,
            "statement_id": statement.id,
            "create_uid": res_create_uid,
        }
        if folio_id:
            vals["folio_ids"] = [(6, 0, [folio_id])]
        self.env["account.bank.statement.line"].create(vals)
        return amount

    def action_migrate_payment_returns(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

        try:
            _logger.info("Preparing 'payment.return' of interest...")
            remote_payment_return_ids = noderpc.env['payment.return'].search(
                [('state', '=', 'done')]
            )
            _logger.info("Migrating 'payment.return'...")
            # disable mail feature to speed-up migration
            context_no_mail = {
                'tracking_disable': True,
                'mail_notrack': True,
                'mail_create_nolog': True,
            }
            for payment_return_id in remote_payment_return_ids:
                try:
                    remote_payment_return = noderpc.env['payment.return'].browse(payment_return_id)
                    remote_payment_return_line = remote_payment_return.line_ids

                    # prepare related payment
                    remote_payment_id = remote_payment_return_line.move_line_ids.payment_id.id
                    account_payment = self.env['account.payment'].search([
                        ('remote_id', '=', remote_payment_id)
                    ]) or None
                    account_move_lines = account_payment.move_line_ids.filtered(
                        lambda x: (x.account_id.internal_type == 'receivable')
                    )
                    line_ids_vals = {
                        'move_line_ids': [(6, False, [x.id for x in account_move_lines])],
                        'partner_id': account_payment.partner_id.id,
                        'amount': remote_payment_return_line.amount,
                        'reference': remote_payment_return_line.reference,
                    }
                    vals = {
                        'name': remote_payment_return.name,
                        'journal_id': account_payment.journal_id.id,
                        'date': remote_payment_return.date,
                        'line_ids': [(0, 0, line_ids_vals)],
                    }

                    payment_return = self.env['payment.return'].with_context(
                        context_no_mail
                    ).create(vals)
                    payment_return.action_confirm()

                    _logger.info('User #%s migrated payment.return for account.payment with ID '
                                 '[local, remote]: [%s, %s]',
                                 self._uid, account_payment.id, remote_payment_id)

                except (ValueError, ValidationError, Exception) as err:
                    migrated_log = self.env['migrated.log'].create({
                        'name': err,
                        'date_time': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'model': 'return',
                        'remote_id': payment_return_id,
                    })
                    _logger.error('Remote payment.return with ID remote: [%s] with ERROR LOG #%s: (%s)',
                                  payment_return_id, migrated_log.id, err)
                    continue

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        else:
            noderpc.logout()

    # INVOICES ---------------------------------------------------------------------------------------------------------------------------

    def _prepare_invoice_remote_data(self, account_invoice, res_users_map_ids, noderpc):
        # search res_users ids
        remote_id = account_invoice['user_id'] and account_invoice['user_id'][0]
        res_user_id = remote_id and res_users_map_ids.get(remote_id) or self._context.get('uid', self._uid)

        # prepare partner_id related field
        default_res_partner = self.env['res.partner'].search([
            ('user_ids', 'in', self._context.get('uid', self._uid))
        ])
        # search res_partner id
        remote_id = account_invoice['partner_id'] and account_invoice['partner_id'][0]
        res_partner_id = self.env['res.partner'].search([
            ('remote_id', '=', remote_id)
        ]).id or None
        # take into account merged partners are not active
        if not res_partner_id:
            res_partner_id = self.env['res.partner'].search([
                ('remote_id', '=', remote_id),
                ('active', '=', False)
            ]).main_partner_id.id or None
        res_partner_id = res_partner_id or default_res_partner.id

        # search related refund_invoice_id
        refund_invoice_id = None
        if account_invoice['refund_invoice_id']:
            refund_invoice_id = self.env['account.invoice'].search([
                ('remote_id', '=', account_invoice['refund_invoice_id'][0])
            ]).id or None

        remote_ids = account_invoice['invoice_line_ids'] and account_invoice['invoice_line_ids']
        invoice_lines = noderpc.env['account.invoice.line'].search_read(
            [('id', 'in', remote_ids)])
        invoice_line_cmds = []
        # prepare invoice lines
        reservation_ids_cmds = reservation_line_ids_cmds = service_ids_cmds = None
        for invoice_line in invoice_lines:
            # search for reservation in sale_order_line
            remote_reservation_ids = noderpc.env['hotel.reservation'].search([
                ('order_line_id', 'in', invoice_line['sale_line_ids'])
            ]) or None
            if remote_reservation_ids:
                reservation_ids = self.env['hotel.reservation'].search([
                    ('remote_id', 'in', remote_reservation_ids)
                ]).ids or None
                reservation_ids_cmds = reservation_ids and [[6, False, reservation_ids]] or None
                # The night is dark and full of terrors
                reservation_line_ids = self.env['hotel.reservation.line'].search([
                    ('reservation_id', 'in', reservation_ids)
                ]).ids
                reservation_line_ids_cmds = reservation_line_ids and [[6, False, reservation_line_ids]] or None

            # search for services in sale_order_line
            remote_service_ids = noderpc.env['hotel.service.line'].search([
                ('service_line_id', 'in', invoice_line['sale_line_ids'])
            ]) or None
            if remote_service_ids:
                service_ids = self.env['hotel.service'].search([
                    ('remote_id', 'in', remote_service_ids)
                ]).ids or None
                service_ids_cmds = service_ids and [[6, False, service_ids]] or None

            # take invoice line taxes
            invoice_line_tax_ids = invoice_line['invoice_line_tax_ids'] and invoice_line['invoice_line_tax_ids'][0] or False
            invoice_line_cmds.append((0, False, {
                'name': invoice_line['name'],
                'origin': invoice_line['origin'],
                'reservation_ids': remote_reservation_ids and reservation_ids_cmds,
                'reservation_line_ids': remote_reservation_ids and reservation_line_ids_cmds,
                'service_ids': remote_service_ids and service_ids_cmds,
                # [480, '700000 Ventas de mercaderías en España']
                'account_id': invoice_line['account_id'] and invoice_line['account_id'][0] or 480,
                'price_unit': invoice_line['price_unit'],
                'quantity': invoice_line['quantity'],
                'discount': invoice_line['discount'],
                'uom_id': invoice_line['uom_id'] and invoice_line['uom_id'][0] or 1,
                'invoice_line_tax_ids': [[6, False, [invoice_line_tax_ids or 59]]],  # 10% (services) as default
            }))

        vals = {
            'remote_id': account_invoice['id'],
            'number': account_invoice['number'],
            'invoice_number': account_invoice['invoice_number'],
            'name': account_invoice['name'],
            'display_name': account_invoice['display_name'],
            'origin': account_invoice['origin'],
            'date_invoice': account_invoice['date_invoice'],
            'type': account_invoice['type'],
            'refund_invoice_id': account_invoice['refund_invoice_id'] and refund_invoice_id,
            'reference': False,
            # [193, '430000 Clientes (euros)']
            'account_id': account_invoice['account_id'] and account_invoice['account_id'][0] or 193,
            'partner_id': res_partner_id,
            # [1, 'EUR']
            'currency_id': account_invoice['currency_id'] and account_invoice['currency_id'][0] or 1,
            'comment': account_invoice['comment'],
            'invoice_line_ids': invoice_line_cmds,
            'user_id': res_user_id,
        }

        return vals

    def action_migrate_invoices(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

        try:
            # prepare res.users ids
            _logger.info("Mapping local with remote 'res.users' ids...")
            remote_ids = noderpc.env['res.users'].search([])
            remote_records = noderpc.env['res.users'].browse(remote_ids)
            res_users_map_ids = {}
            for record in remote_records:
                res_users_id = self.env['res.users'].search([
                    ('login', '=', record.login),
                ]).id or self._context.get('uid', self._uid)
                res_users_map_ids.update({record.id: res_users_id})

            _logger.info("Preparing 'account.invoice' of interest...")
            remote_account_invoice_ids = noderpc.env['account.invoice'].search(
                [('number', 'not in', [False])],
                order='id ASC'  # ensure refunded invoices are retrieved after the normal invoice
            )

            _logger.info("Migrating 'account.invoice'...")
            # disable mail feature to speed-up migration
            context_no_mail = {
                'tracking_disable': True,
                'mail_notrack': True,
                'mail_create_nolog': True,
            }
            for remote_account_invoice_id in remote_account_invoice_ids:
                try:
                    migrated_account_invoice = self.env['account.invoice'].search(
                        [('remote_id', '=', remote_account_invoice_id)]
                    ) or None
                    if not migrated_account_invoice:
                        _logger.info('User #%s started migration of account.invoice with remote ID: [%s]',
                                     self._uid, remote_account_invoice_id)

                        rpc_account_invoice = noderpc.env['account.invoice'].search_read(
                            [('id', '=', remote_account_invoice_id)],
                        )[0]

                        if rpc_account_invoice['number'].strip() == '':
                            continue

                        vals = self._prepare_invoice_remote_data(
                            rpc_account_invoice,
                            res_users_map_ids,
                            noderpc,
                        )

                        migrated_account_invoice = self.env['account.invoice'].with_context(
                            context_no_mail
                        ).create(vals)
                        # this function require a valid vat number in the associated partner_id
                        migrated_account_invoice.with_context(
                            {'validate_vat_number': False}
                        ).action_invoice_open()
                        #
                        payment_ids = self.env['account.payment'].search([
                            ('remote_id', 'in', rpc_account_invoice['payment_ids'])
                        ]).ids or None
                        #
                        if payment_ids:
                            domain = [
                                ('account_id', '=', migrated_account_invoice.account_id.id),
                                ('payment_id', 'in', payment_ids),
                                ('reconciled', '=', False),
                                '|', ('amount_residual', '!=', 0.0),
                                ('amount_residual_currency', '!=', 0.0)
                            ]
                            if migrated_account_invoice.type in ('out_invoice', 'in_refund'):
                                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                            else:
                                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                            lines = self.env['account.move.line'].search(domain)
                            for line in lines:
                                migrated_account_invoice.assign_outstanding_credit(line.id)

                        _logger.info('User #%s migrated account.invoice with ID [local, remote]: [%s, %s]',
                                     self._uid, migrated_account_invoice.id, remote_account_invoice_id)

                except (ValueError, ValidationError, Exception) as err:
                    migrated_log = self.env['migrated.log'].create({
                        'name': err,
                        'date_time': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'model': 'invoice',
                        'remote_id': remote_account_invoice_id,
                    })
                    _logger.error('Remote account.invoice with ID remote: [%s] with ERROR LOG #%s: (%s)',
                                  remote_account_invoice_id, migrated_log.id, err)
                    continue

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        else:
            noderpc.logout()

    def _update_special_field_names(self, model, model_log_code, res_users_map_ids, noderpc):
        # prepare record ids
        _logger.info("Updating '%s' special field names..", model)
        record_ids = self.env[model].search([
            ('remote_id', '>', 0)
        ])
        for record in record_ids:
            try:
                rpc_record = noderpc.env[model].search_read(
                    [('id', '=', record.remote_id)],
                    ['create_uid', 'create_date'],
                ) or False

                if rpc_record:
                    rpc_record = rpc_record[0]
                    create_uid = rpc_record['create_uid'] and rpc_record['create_uid'][0] or False
                    create_uid = create_uid and res_users_map_ids.get(create_uid) or self._uid
                    create_date = rpc_record['create_date'] and rpc_record['create_date'] or record.create_date

                    self.env.cr.execute('''UPDATE ''' + self.env[model]._table + '''
                                           SET create_uid = %s, create_date = %s WHERE id = %s''',
                                        (create_uid, create_date, record.id))

                    _logger.info('User #%s has updated %s with ID [local, remote]: [%s, %s]',
                                 self._uid, model, record.id, record.remote_id)
                else:
                    self.env['migrated.log'].create({
                        'name': 'Remote record not found!',
                        'date_time': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'model': model_log_code,
                        'remote_id': record.remote_id,
                    })

            except (ValueError, ValidationError, Exception) as err:
                migrated_log = self.env['migrated.log'].create({
                    'name': err,
                    'date_time': fields.Datetime.now(),
                    'migrated_hotel_id': self.id,
                    'model': model_log_code,
                    'remote_id': record.remote_id,
                })
                _logger.error('Failed updating hotel.folio with ID [local]: [%s] with ERROR LOG #%s: (%s)',
                              record.id, migrated_log.id, err)
                continue

    def action_update_special_field_names(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

        try:
            # prepare res.users ids
            _logger.info("Mapping local with remote 'res.users' ids...")
            remote_ids = noderpc.env['res.users'].search([])
            remote_records = noderpc.env['res.users'].browse(remote_ids)
            res_users_map_ids = {}
            for record in remote_records:
                res_users_id = self.env['res.users'].search([
                    ('login', '=', record.login),
                ]).id or self._context.get('uid', self._uid)
                res_users_map_ids.update({record.id: res_users_id})

            self._update_special_field_names('hotel.folio', 'folio', res_users_map_ids, noderpc)
            self._update_special_field_names('hotel.reservation', 'reservation', res_users_map_ids, noderpc)
            self._update_special_field_names('account.payment', 'payment', res_users_map_ids, noderpc)
            self._update_special_field_names('account.invoice', 'invoice', res_users_map_ids, noderpc)

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        else:
            noderpc.logout()

    # CLEAN (review)-----

    def action_clean_up(self):
        self.ensure_one()
        # disable Odoo 10 products
        product_product = self.env['product.product'].search([
            ('remote_id', '>', 0)
        ])
        product_product.product_tmpl_id.write({'active': False})
        product_product.write({'active': False})
        # disable specific closure_reason created for migration ¿?

    # DEBUG --------------

    def action_migrate_debug(self):
        self.ensure_one()
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)

        import wdb
        wdb.set_trace()

    @api.model
    def cron_migrate_partners(self):
        hotel = self.env[self._name].search([])
        hotel.action_migrate_partners()

    @api.model
    def cron_migrate_folios(self):
        hotel = self.env[self._name].search([])
        hotel.action_migrate_folios()

    @api.model
    def cron_migrate_reservations(self):
        hotel = self.env[self._name].search([])
        hotel.action_migrate_reservations()

    @api.model
    def cron_migrate_services(self):
        hotel = self.env[self._name].search([])
        hotel.action_migrate_services()

    @api.model
    def cron_migrate_invoices(self):
        hotel = self.env[self._name].search([])
        hotel.action_migrate_invoices()

    @api.model
    def cron_migrate_account_models(self):
        hotel = self.env[self._name].search([])
        hotel.action_migrate_payments()
        hotel.action_migrate_payment_returns()
        hotel.action_migrate_invoices()

    @api.model
    def cron_migrate_hotel(self):
        self.cron_migrate_partners()
        self.cron_migrate_folios()
        self.cron_migrate_reservations()
        self.cron_migrate_services()

    @api.model
    def cron_update_special_field_names(self):
        hotel = self.env[self._name].search([])
        hotel.action_update_special_field_names()

    def import_pricelists(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Pricelists...")
            import_datetime = fields.Datetime.now()
            remote_ids = noderpc.env['product.pricelist'].search([])
            remote_records = noderpc.env['product.pricelist'].browse(remote_ids)
            pricelist_migrated_ids = self.mapped("migrated_pricelist_ids.remote_id")
            for record in remote_records:
                match_record = self.env['product.pricelist'].search([
                    ('name', '=', record.name),
                ])
                # TODO: Create Binding Wubook??
                if record.id not in pricelist_migrated_ids:
                    self.migrated_pricelist_ids = [(0, 0, {
                        'remote_id': record.id,
                        'remote_name': record.name,
                        'last_sync': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'pms_pricelist_id': match_record.id if match_record else False,
                    })]
                    if match_record.pms_property_ids:
                        match_record.pms_property_ids = [(4, self.pms_property_id.id)]
                    _logger.info('Pricelist imported: %s',
                                 record.name)
            self.last_import_pricelists = import_datetime
            self.count_migrated_pricelists = len(self.migrated_pricelist_ids)
        except (ValueError, ValidationError, Exception) as err:
            self.env['migrated.log'].create({
                'name': err,
                'date_time': fields.Datetime.now(),
                'migrated_hotel_id': self.id,
                'model': 'product.pricelist',
                'remote_id': record.id,
            })
            _logger.error('pricelist import error:%s', err)

    def import_room_type_classes(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Room Types Classes...")
            remote_ids = noderpc.env['hotel.room.type.class'].search([])
            remote_records = noderpc.env['hotel.room.type.class'].browse(remote_ids)
            room_type_class_migrated_ids = self.mapped("migrated_room_type_class_ids.remote_id")
            for record in remote_records:
                match_record = self.env['pms.room.type.class'].search([
                    '|',
                    ('name', '=', record.name),
                    ('default_code', '=', record.code_class),
                ])
                # TODO: Create Binding Wubook??
                if record.id not in room_type_class_migrated_ids:
                    self.migrated_room_type_class_ids = [(0, 0, {
                        'remote_id': record.id,
                        'remote_name': record.name,
                        'last_sync': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'pms_room_type_class_id': match_record.id if match_record and len(match_record) == 1 else False,
                    })]
                    if match_record.pms_property_ids:
                        match_record.pms_property_ids = [(4, self.pms_property_id.id)]
                    _logger.info('RoomType Class imported: %s',
                                 record.name)
        except (ValueError, ValidationError, Exception) as err:
            _logger.error('roomtype class import error:%s', err)

    def import_room_types(self):
        if not self.migrated_room_type_class_ids:
            raise UserError(_("You must configure room type class previusly to room types import"))
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Room Types...")
            remote_ids = noderpc.env['hotel.room.type'].search([])
            remote_records = noderpc.env['hotel.room.type'].browse(remote_ids)
            room_type_migrated_ids = self.mapped("migrated_room_type_ids.remote_id")
            for record in remote_records:
                match_record = self.env['pms.room.type'].search([
                    '|',
                    ('name', '=', record.name),
                    ('default_code', '=', record.code_class),
                ])
                # TODO: Create Binding Wubook??
                if record.id not in room_type_migrated_ids:
                    self.migrated_room_type_ids = [(0, 0, {
                        'remote_id': record.id,
                        'remote_name': record.name,
                        'last_sync': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'pms_room_type_id': match_record.id if match_record and len(match_record) == 1 else False,
                    })]
                    if match_record.pms_property_ids:
                        match_record.pms_property_ids = [(4, self.pms_property_id.id)]
                    _logger.info('RoomType imported: %s',
                                 record.name)
            self.count_migrated_room_types = len(self.migrated_room_type_ids)
        except (ValueError, ValidationError, Exception) as err:
            _logger.error('roomtype import error:%s', err)

    def import_rooms(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Rooms...")
            import_datetime = fields.Datetime.now()
            remote_ids = noderpc.env['hotel.room'].search([])
            remote_records = noderpc.env['hotel.room'].browse(remote_ids)
            room_migrated_ids = self.mapped("migrated_room_ids.remote_id")
            total_records = len(remote_records)
            count = 0
            for record in remote_records:
                room_clean_name = [int(item) for item in record.name.split() if item.isdigit()]
                room_clean_name = room_clean_name[0] if len(room_clean_name) == 1 else False
                # TODO: Habitaciones compartidas tienen el mismo room_clean_name!!
                match_record = self.env['pms.room'].search([
                    ("pms_property_id", "=", self.pms_property_id.id),
                    '|',
                    ('name', '=', record.name),
                    ('name', '=', room_clean_name),
                ])
                if record.id not in room_migrated_ids:
                    if match_record:
                        self.migrated_room_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': record.name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                            'pms_room_id': match_record.id if match_record and len(match_record) == 1 else False,
                        })]
                        count += 1
                        _logger.info('(%s/%s) Room Matching imported: %s',
                                     total_records, count, record.name)
                    elif self.auto_create_rooms:
                        room_type = self.migrated_room_type_ids.filtered(
                            lambda r: r.remote_id == record.room_type_id.id
                        ).pms_room_type_id
                        if not room_type:
                            raise UserError(_("Room type dont found in v14 mapping: %s", record.room_type.name))
                        new_room = self.env["pms.room"].create({
                            'name': room_clean_name or record.name,
                            'room_type_id': room_type.id,
                            'capacity': record.capacity,
                            'extra_beds_allowed': record.extra_beds_allowed,
                            'sequence': record.sequence,
                            'in_ine': record.in_ine,
                            'pms_property_id': self.pms_property_id.id,
                        })
                        count += 1
                        self.migrated_room_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': record.name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                            'pms_room_id': new_room.id,
                        })]
                        _logger.info('(%s/%s) Remote Room created: %s',
                                     total_records, count, record.name)
                    else:
                        self.migrated_room_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': record.name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                        })]
                        count += 1
                        _logger.info('(%s/%s) Room imported without v14 related: %s',
                                     total_records, count, record.name)
            self.last_import_rooms = import_datetime
            self.count_migrated_rooms = len(self.migrated_room_ids)
        except (ValueError, ValidationError, Exception) as err:
            _logger.error('room import error:%s', err)

    def import_products(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Products...")
            import_datetime = fields.Datetime.now()
            remote_ids = noderpc.env['product.product'].search([])
            # We want discard room type products associated
            remote_room_type_ids = noderpc.env['hotel.room.type'].search([])
            remote_room_types = noderpc.env['hotel.room.type'].browse(remote_room_type_ids)
            remote_product_discard_ids = []
            for room_type in remote_room_types:
                remote_product_discard_ids.append(room_type.product_id.id)

            remote_records = noderpc.env['product.product'].browse(remote_ids)
            product_migrated_ids = self.mapped("migrated_product_ids.remote_id")
            total_records = len(remote_records)
            count = 0
            for record in remote_records:
                if record.id in remote_product_discard_ids:
                    continue
                match_record = self.env['product.product'].search([
                    ('name', '=', record.name),
                ])
                if record.id not in product_migrated_ids:
                    if match_record:
                        self.migrated_product_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': record.name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                            'product_id': match_record.id if match_record and len(match_record) == 1 else False,
                        })]
                        if match_record.pms_property_ids:
                            match_record.pms_property_ids = [(4, self.pms_property_id.id)]
                        count += 1
                        _logger.info('(%s/%s) Product Matching imported: %s',
                                     total_records, count, record.name)
                    elif self.auto_create_products:
                        new_product = self.env["product.product"].create({
                            'name': record.name,
                            'pms_property_ids': [(4, self.pms_property_id.id)],
                            'list_price': record.list_price,
                            'type': 'service',
                            'is_extra_bed': record.is_extra_bed,
                            'per_day': record.per_day,
                            'per_person': record.per_person,
                            'daily_limit': record.daily_limit,
                            'consumed_on': record.consumed_on,
                        })
                        count += 1
                        self.migrated_product_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': record.name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                            'product_id': new_product.id,
                        })]
                        _logger.info('(%s/%s) Remote Product created: %s',
                                     total_records, count, record.name)
                    else:
                        self.migrated_product_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': record.name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                        })]
                        count += 1
                        _logger.info('(%s/%s) Product imported without v14 related: %s',
                                     total_records, count, record.name)
            self.last_import_products = import_datetime
            self.count_migrated_products = len(self.migrated_product_ids)
        except (ValueError, ValidationError, Exception) as err:
            _logger.error('product import error:%s', err)

    def import_board_services(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Board Services...")
            remote_ids = noderpc.env['hotel.board.service'].search([])
            remote_records = noderpc.env['hotel.board.service'].browse(remote_ids)
            board_service_migrated_ids = self.mapped("migrated_board_service_ids.remote_id")
            for record in remote_records:
                match_record = self.env['pms.board.service'].search([
                    ('name', '=', record.name),
                ])
                # TODO: Create Binding Wubook??
                if record.id not in board_service_migrated_ids:
                    self.migrated_board_service_ids = [(0, 0, {
                        'remote_id': record.id,
                        'remote_name': record.name,
                        'last_sync': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'board_service_id': match_record.id if match_record and len(match_record) == 1 else False,
                    })]
                    if match_record.pms_property_ids:
                        match_record.pms_property_ids = [(4, self.pms_property_id.id)]
                    _logger.info('Board Service Class imported: %s',
                                 record.name)
        except (ValueError, ValidationError, Exception) as err:
            _logger.error('boardservice class import error:%s', err)

    def import_board_service_room_types(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Board Services Room types...")
            import_datetime = fields.Datetime.now()
            remote_ids = noderpc.env['hotel.board.service.room.type'].search([])
            remote_records = noderpc.env['hotel.board.service.room.type'].browse(remote_ids)
            board_service_room_type_migrated_ids = self.mapped("migrated_board_service_room_type_ids.remote_id")
            total_records = len(remote_records)
            count = 0
            for record in remote_records:
                room_type_id = self.migrated_room_type_ids.filtered(
                    lambda b: b.remote_id == record.hotel_room_type_id.id
                ).pms_room_type_id.id
                if not room_type_id:
                    raise UserError(_("Room type dont found in v14 mapping: %s", record.hotel_room_type_id.name))
                board_service_id = self.migrated_board_service_ids.filtered(
                    lambda b: b.remote_id == record.hotel_board_service_id.id
                ).board_service_id.id
                if not board_service_id:
                    raise UserError(_("Main Board Service dont found in v14 mapping: %s", record.hotel_board_service_id.name))
                match_record = self.env['pms.board.service.room.type'].search([
                    ('pms_board_service_id', '=', board_service_id),
                    ('pms_room_type_id', '=', room_type_id),
                    '|',
                    ("pms_property_ids", "=", False),
                    ("pms_property_ids", "in", self.pms_property_id.id),
                ])
                if record.id not in board_service_room_type_migrated_ids:
                    if match_record:
                        self.migrated_board_service_room_type_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': match_record.display_name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                            'board_service_room_type_id': match_record.id if match_record and len(match_record) == 1 else False,
                        })]
                        count += 1
                        _logger.info('(%s/%s) Board Service Room Type Matching imported: %s',
                                     total_records, count, record.name)
                    elif self.auto_create_board_service_room_types:
                        # Prepare board service room type lines
                        line_vals = []
                        remote_line_ids = record.board_service_line_ids
                        for line in remote_line_ids:
                            product_id = self.migrated_product_ids.filtered(
                                lambda b: b.remote_id == line.product_id.id
                            ).product_id.id
                            if not product_id:
                                remote_product_id = noderpc.env['product.product'].search([
                                    ('id', '=', line.product_id.id),
                                    '|', ('active', '=', True), ('active', '=', False),
                                ])
                                remote_product = noderpc.env['product.product'].browse(remote_product_id)
                                if remote_product:
                                    new_product = self.env["product.product"].create({
                                        'name': remote_product.name,
                                        'pms_property_ids': [(4, self.pms_property_id.id)],
                                        'list_price': remote_product.list_price,
                                        'type': 'service',
                                        'is_extra_bed': remote_product.is_extra_bed,
                                        'per_day': remote_product.per_day,
                                        'per_person': remote_product.per_person,
                                        'daily_limit': remote_product.daily_limit,
                                        'consumed_on': remote_product.consumed_on,
                                        'active': False,
                                    })
                                    product_id = new_product.id
                                else:
                                    raise UserError(_("Product dont found in v14 mapping: %s", line.product_id.name))
                            line_vals.append((0, 0, {
                                'product_id': product_id,
                                'amount': record.amount,
                            }))
                        new_board = self.env["pms.board.service.room.type"].create({
                            'pms_room_type_id': room_type_id,
                            'board_service_line_ids': line_vals,
                            'pms_board_service_id': board_service_id,
                        })
                        count += 1
                        self.migrated_board_service_room_type_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': match_record.display_name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                            'board_service_room_type_id': new_board.id,
                        })]
                        _logger.info('(%s/%s) Board Service Room Type created: %s',
                                     total_records, count, record.name)
                    else:
                        self.migrated_board_service_room_type_ids = [(0, 0, {
                            'remote_id': record.id,
                            'remote_name': match_record.display_name,
                            'last_sync': fields.Datetime.now(),
                            'migrated_hotel_id': self.id,
                        })]
                        count += 1
                        _logger.info('(%s/%s) Board Service Room Type imported without v14 related: %s',
                                     total_records, count, record.display_name)
            self.last_import_board_services = import_datetime
            self.count_migrated_board_services = len(self.migrated_board_service_room_type_ids)
        except (ValueError, ValidationError, Exception) as err:
            _logger.error('Board services import error: %s', err)

    def import_journals(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        try:
            _logger.info("Importing Remote Jorunals...")
            remote_ids = noderpc.env['account.journal'].search([])
            remote_records = noderpc.env['account.journal'].browse(remote_ids)
            journal_migrated_ids = self.mapped("migrated_journal_ids.remote_id")
            for record in remote_records:
                match_record = self.env['account.journal'].search([
                    ('name', '=', record.name),
                    ("company_id", "=", self.pms_property_id.company_id.id),
                    '|',
                    ("pms_property_ids", "=", False),
                    ("pms_property_ids", "in", self.pms_property_id.id),
                ])
                if record.id not in journal_migrated_ids:
                    self.migrated_journal_ids = [(0, 0, {
                        'remote_id': record.id,
                        'remote_name': record.name,
                        'last_sync': fields.Datetime.now(),
                        'migrated_hotel_id': self.id,
                        'account_journal_id': match_record.id if match_record else False,
                    })]
                    if match_record.pms_property_ids:
                        match_record.pms_property_ids = [(4, self.pms_property_id.id)]
                    _logger.info('Pricelist imported: %s',
                                 record.name)
            self.count_migrated_journals = len(self.migrated_journal_ids)
        except (ValueError, ValidationError, Exception) as err:
            self.env['migrated.log'].create({
                'name': err,
                'date_time': fields.Datetime.now(),
                'migrated_hotel_id': self.id,
                'model': 'journal',
                'remote_id': record.id,
            })
            _logger.error('journal import error:%s', err)

    def import_channel_types(self):
        _logger.info("Creating remote channel types...")
        remote_channels = [
            ('door', 'Door'),
            ('mail', 'Mail'),
            ('phone', 'Phone'),
            ('call', 'Call Center'),
            ('web', 'Web'),
            ('agency', 'Agencia'),
            ('operator', 'Tour operador'),
            ('virtualdoor', 'Virtual Door'),
            ('detour', 'Detour')
        ]
        for channel in remote_channels:
            match_record = self.env['pms.sale.channel'].search([
                ('name', '=', channel[1]),
            ])
            if channel[0] not in self.migrated_channel_type_ids.mapped("remote_name"):
                self.migrated_channel_type_ids = [(0, 0, {
                    'remote_name': channel[0],
                    'last_sync': fields.Datetime.now(),
                    'migrated_hotel_id': self.id,
                    'channel_type_id': match_record.id if match_record and len(match_record) == 1 else False,
                })]
                _logger.info('RoomType Class imported: %s', channel[1])

