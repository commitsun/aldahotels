##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 -2021 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
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
import json
import logging
import urllib.error

import odoorpc.odoo

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

mapping_estados = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 2,
    7: 3,
}


class MigratedHotel(models.Model):

    _inherit = "migrated.hotel"

    json_to_export_reservations_v2_data = fields.Text(
        string="Json to export", readonly=True
    )
    json_to_export_outs_v2_data = fields.Text(string="Json to export", readonly=True)

    def export_reservations_data_mapping_v2(self):
        """
        Mapping strcuture data V14 to V11 version
        """
        json_data = self.env["data_bi"].export_reservations_data(
            [self.pms_property_id.id]
        )
        json_reservas = json.loads(json_data)[0][0].get("Reservas")
        mapping_categories = self.get_dict_categories()
        total = len(json_reservas)
        _logger.info("Total de reservas a exportar: %s", total)
        i = 0
        mapping_reservas = []
        for reserva_vals in json_reservas:
            mapping_res = {}
            reserva = self.env["pms.reservation"].browse(reserva_vals["ID_Reserva"])
            mapping_res["ID_Reserva"] = reserva.remote_id or (reserva.id * 100000)
            mapping_res["ID_Hotel"] = 1
            mapping_res["ID_EstadoReserva"] = mapping_estados[
                reserva_vals["ID_EstadoReserva"]
            ]
            mapping_res["ID_Segmento"] = (
                mapping_categories.get(reserva_vals["ID_Segmento"]) or 1
            )
            mapping_res["ID_Cliente"] = self.get_mapping_partners(
                reserva_vals["ID_Cliente"]
            )
            mapping_res["ID_Canal"] = self.get_mapping_channels(
                reserva_vals["ID_Canal"]
            )
            mapping_res["ID_TipoHabitacion"] = self.get_mapping_room_type(
                reserva_vals["ID_TipoHabitacion"]
            )
            mapping_res["ID_HabitacionDuerme"] = self.get_mapping_room_type(
                reserva_vals["ID_HabitacionDuerme"]
            )
            mapping_res["ID_Regimen"] = self.get_mapping_regimen(
                reserva_vals["ID_Regimen"]
            )
            mapping_res["ID_Tarifa"] = self.get_mapping_pricelists(
                reserva_vals["ID_Tarifa"]
            )
            mapping_res["ID_Pais"] = reserva_vals["ID_Pais"]
            mapping_res["ID_Room"] = self.get_mapping_rooms(reserva_vals["ID_Room"])
            mapping_res["ID_Folio"] = reserva.folio_id.remote_id or (
                reserva.folio_id.id * 100000
            )
            mapping_reservas.append(mapping_res)
            i += 1
            _logger.info("%s/%s", i, total)

        json_bloqueos = json.loads(json_data)[0][0].get("Bloqueos")
        mapping_bloqueos = []
        if json_bloqueos:
            total = len(json_bloqueos)
            i = 0
            for bloqueo_vals in json_bloqueos:
                mapping_blo = {}
                mapping_blo["ID_Hotel"] = 1
                mapping_blo["ID_Tipo_Habitacion"] = self.get_mapping_room_type(
                    bloqueo_vals["ID_Tipo_Habitacion"]
                )
                mapping_blo["ID_Motivo_bloqueo"] = 1
                mapping_bloqueos.append(mapping_blo)
                i += 1
                _logger.info("%s/%s", i, total)

        self.json_to_export_reservations_v2_data = json.dumps(mapping_reservas)
        self.json_to_export_outs_v2_data = json.dumps(mapping_bloqueos)

    def get_mapping_room_type(self, room_type_id):
        return (
            self.env["migrated.room.type"]
            .search(
                [
                    ("migrated_hotel_id", "=", self.id),
                    ("pms_room_type_id", "=", room_type_id),
                ]
            )
            .remote_id
        )

    def get_mapping_pricelists(self, pricelist_id):
        return (
            self.env["migrated.pricelist"]
            .search(
                [
                    ("migrated_hotel_id", "=", self.id),
                    ("pms_pricelist_id", "=", pricelist_id),
                ]
            )[0]
            .remote_id
        )

    def get_mapping_channels(self, channel_id):
        return (
            self.env["migrated.channel.type"]
            .search(
                [
                    ("migrated_hotel_id", "=", self.id),
                    ("channel_type_id", "=", channel_id),
                ]
            )
            .remote_name
        )

    def get_mapping_partners(self, partner_id):
        return (
            self.env["migrated.partner"]
            .search(
                [("migrated_hotel_id", "=", self.id), ("partner_id", "=", partner_id)]
            )
            .remote_id
        )

    def get_mapping_rooms(self, room_id):
        return (
            self.env["migrated.room"]
            .search(
                [("migrated_hotel_id", "=", self.id), ("pms_room_id", "=", room_id)]
            )
            .remote_id
        )

    def get_mapping_regimen(self, board_service_room_type_id):
        board_service_id = (
            self.env["pms.board.service.room.type"]
            .browse(board_service_room_type_id)
            .pms_board_service_id.id
        )
        return (
            self.env["migrated.board.service"]
            .search(
                [
                    ("migrated_hotel_id", "=", self.id),
                    ("board_service_id", "=", board_service_id),
                ]
            )
            .remote_id
        )

    def get_dict_categories(self):
        try:
            noderpc = odoorpc.ODOO(self.odoo_host, self.odoo_protocol, self.odoo_port)
            noderpc.login(self.odoo_db, self.odoo_user, self.odoo_password)
        except (
            odoorpc.error.RPCError,
            odoorpc.error.InternalError,
            urllib.error.URLError,
        ) as err:
            raise ValidationError(err)

        try:
            remote_ids = noderpc.env["res.partner.category"].search([])
            remote_records = noderpc.env["res.partner.category"].browse(remote_ids)
            category_map_ids = {}
            for record in remote_records:
                if record.parent_id:
                    res_partner_category = self.env["res.partner.category"].search(
                        [
                            ("name", "=", record.name.lower()),
                            ("parent_id.name", "=", record.parent_id.name.lower()),
                        ]
                    )
                else:
                    res_partner_category = self.env["res.partner.category"].search(
                        [("name", "=", record.name.lower())]
                    )
                if res_partner_category:
                    category_map_ids.update({str(record.id): res_partner_category.id})
            return category_map_ids
        except Exception as err:
            raise ValidationError(err)

    def databi_export_json(self):
        centro = self._ids[0]
        hotel = self.env["migrated.hotel"].search([("odoo_host", "=", centro)])
        if len(hotel) == 1:
            if hotel.in_live:
                if hotel.json_to_export_reservations_v2_data:
                    respuesta = str(hotel.json_to_export_reservations_v2_data)
                    respuesta += str(hotel.json_to_export_outs_v2_data)
                else:
                    respuesta = "Error: Listo SIN datos"
            else:
                respuesta = "Error: En proceso"
        else:
            respuesta = "Error: " + str(len(hotel))
        return respuesta
