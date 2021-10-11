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
from datetime import date, datetime, timedelta

from odoo import api, models

_logger = logging.getLogger(__name__)


class DataBi(models.Model):
    """Management and export data for MopSolution MyDataBI."""

    _name = "data_bi"

    @api.model
    def export_data_bi(self, archivo=0, default_property=False, fechafoto=False):
        u"""Prepare a Json Objet to export data for MyDataBI.

        Generate a dicctionary to by send in JSON
        archivo = response file type
            archivo == 0 'ALL'
            archivo == 1 'Tarifa'
            archivo == 2 'Canal'
            archivo == 3 'Hotel'
            archivo == 4 'Pais'
            archivo == 5 'Regimen'
            archivo == 6 'Reservas'
            archivo == 7 'Capacidad'
            archivo == 8 'Tipo Habitación'
            archivo == 9 'Budget'
            archivo == 10 'Bloqueos'
            archivo == 11 'Motivo Bloqueo'
            archivo == 12 'Segmentos'
            archivo == 13 'Clientes'
            archivo == 14 'Estado Reservas'
            archivo == 15 'Room names'
        fechafoto = start date to take data
        """
        if not fechafoto:
            fechafoto = date.today().strftime("%Y-%m-%d")
        _logger.warning(
            "--- ### Init Export Data_Bi Module parameters:  %s, %s, %s ### ---",
            archivo,
            default_property,
            fechafoto,
        )

        if type(fechafoto) is dict:
            fechafoto = date.today()
        else:
            fechafoto = datetime.strptime(fechafoto, "%Y-%m-%d").date()

        propertys = self.env["pms.property"].search([])
        if type(default_property) is int:
            default_property = self.env["pms.property"].search(
                [("id", "=", default_property)]
            )
            if len(default_property) == 1:
                propertys = default_property

        dias = self.env.user.data_bi_days
        limit_ago = (fechafoto - timedelta(days=dias)).strftime("%Y-%m-%d")

        _logger.info("Export Data %s days ago. From %s", dias, limit_ago)
        estado_array = [
            "draft",
            "confirm",
            "onboard",
            "done",
            "cancel",
            "arrival_delayed",
            "departure_delayed",
        ]

        if archivo == 0:
            dic_export = self.export_all(propertys, limit_ago, estado_array)
        else:
            dic_export = self.export_one(propertys, limit_ago, estado_array, archivo)

        dictionary_to_json = json.dumps(dic_export)
        _logger.warning("--- ### End Export Data_Bi Module to Json ### ---")
        return dictionary_to_json

    @api.model
    def export_all(self, propertys, limit_ago, estado_array):
        line_res = self.env["pms.reservation.line"].search(
            [("date", ">=", limit_ago)], order="id"
        )
        dic_reservas = self.data_bi_reservas(
            propertys,
            line_res,
            estado_array,
        )
        dic_export = [
            {"Tarifa": self.data_bi_tarifa(propertys)},
            {"Canal": self.data_bi_canal(propertys)},
            {"Hotel": self.data_bi_hotel()},
            {"Pais": self.data_bi_pais(propertys)},
            {"Regimen": self.data_bi_regimen(propertys)},
            {"Reservas": dic_reservas},
            {"Capacidad": self.data_bi_capacidad(propertys)},
            {"Tipo Habitación": self.data_bi_habitacione(propertys)},
            {"Budget": self.data_bi_budget(propertys)},
            {"Bloqueos": self.data_bi_bloqueos(propertys, line_res)},
            {"data_bi_moti_bloq": self.data_bi_moti_bloq(propertys)},
            {"Segmentos": self.data_bi_segment(propertys)},
            {"Clientes": self.data_bi_client(propertys)},
            {"Estado Reservas": self.data_bi_estados(propertys, estado_array)},
            {"Nombre Habitaciones": self.data_bi_rooms(propertys)},
        ]
        return dic_export

    @api.model
    def export_one(self, propertys, limit_ago, estado_array, archivo):
        if (archivo == 0) or (archivo == 10) or (archivo == 6):
            line_res = self.env["pms.reservation.line"].search(
                [("date", ">=", limit_ago)], order="id"
            )
            dic_reservas = self.data_bi_reservas(
                propertys,
                line_res,
                estado_array,
            )
        dic_export = []
        if archivo == 1:
            dic_export.append({"Tarifa": self.data_bi_tarifa(propertys)})
        elif archivo == 2:
            dic_export.append({"Canal": self.data_bi_canal(propertys)})
        elif archivo == 3:
            dic_export.append({"Hotel": self.data_bi_hotel()})
        elif archivo == 4:
            dic_export.append({"Pais": self.data_bi_pais(propertys)})
        elif archivo == 5:
            dic_export.append({"Regimen": self.data_bi_regimen(propertys)})
        elif archivo == 6:
            dic_export.append({"Reservas": dic_reservas})
        elif archivo == 7:
            dic_export.append({"Capacidad": self.data_bi_capacidad(propertys)})
        elif archivo == 8:
            dic_export.append({"Tipo Habitación": self.data_bi_habitacione(propertys)})
        elif archivo == 9:
            dic_export.append({"Budget": self.data_bi_budget(propertys)})
        elif archivo == 10:
            dic_export.append({"Bloqueos": self.data_bi_bloqueos(propertys, line_res)})
        elif archivo == 11:
            dic_export.append({"data_bi_moti_bloq": self.data_bi_moti_bloq(propertys)})
        elif archivo == 12:
            dic_export.append({"Segmentos": self.data_bi_segment(propertys)})
        elif archivo == 13:
            dic_export.append({"Clientes": self.data_bi_client(propertys)})
        elif archivo == 14:
            dic_export.append(
                {"Estado Reservas": self.data_bi_estados(propertys, estado_array)}
            )
        elif archivo == 15:
            dic_export.append({"Nombre Habitaciones": self.data_bi_rooms(propertys)})
        return dic_export

    @api.model
    def data_bi_tarifa(self, propertys):
        # Diccionario con las tarifas [1]
        dic_tarifa = []

        for prop in propertys:
            tarifas = self.env["product.pricelist"].search_read(
                [
                    "|",
                    ("active", "=", False),
                    ("active", "=", True),
                    "|",
                    ("pms_property_ids", "=", prop.id),
                    ("pms_property_ids", "=", False),
                ],
                ["name"],
            )
            _logger.info(
                "DataBi: Calculating %s fees in %s", str(len(tarifas)), prop.name
            )
            for tarifa in tarifas:
                dic_tarifa.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Tarifa": tarifa["id"],
                        "Descripcion": tarifa["name"],
                    }
                )
        return dic_tarifa

    @api.model
    def data_bi_canal(self, propertys):
        # Diccionario con los Canales [2]
        dic_canal = []
        channels = self.env["pms.sale.channel"].search([])
        _logger.info("DataBi: Calculating %s Channels", str(len(channels)))
        for prop in propertys:
            dic_canal.append(
                {"ID_Hotel": prop.id, "ID_Canal": "0", "Descripcion": u"Ninguno"}
            )
            for channel in channels:
                dic_canal.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Canal": channel["id"],
                        "Descripcion": channel["name"],
                    }
                )
        return dic_canal

    @api.model
    def data_bi_hotel(self):
        # Diccionario con el/los nombre de los hoteles  [3]
        hoteles = self.env["pms.property"].search([])
        _logger.info("DataBi: Calculating %s hotel names", str(len(hoteles)))

        dic_hotel = []
        for hotel in hoteles:
            dic_hotel.append({"ID_Hotel": hotel.id, "Descripcion": hotel.name})
        return dic_hotel

    @api.model
    def data_bi_pais(self, propertys):
        dic_pais = []
        dic_ine = [{"ID_Pais": "NONE", "Descripcion": "No Asignado"},
             {"ID_Pais": "AFG", "Descripcion": "Afganistán"},
             {"ID_Pais": "ALB", "Descripcion": "Albania"},
             {"ID_Pais": "DEU", "Descripcion": "Alemania"},
             {"ID_Pais": "AND", "Descripcion": "Andorra"},
             {"ID_Pais": "AGO", "Descripcion": "Angola"},
             {"ID_Pais": "AIA", "Descripcion": "Anguila"},
             {"ID_Pais": "ATG", "Descripcion": "Antigua y Barbuda"},
             {"ID_Pais": "ANT", "Descripcion": "Antillas Neerlandesas"},
             {"ID_Pais": "ATA", "Descripcion": "Antártida"},
             {"ID_Pais": "SAU", "Descripcion": "Arabia Saudita"},
             {"ID_Pais": "DZA", "Descripcion": "Argelia"},
             {"ID_Pais": "ARG", "Descripcion": "Argentina"},
             {"ID_Pais": "ARM", "Descripcion": "Armenia"},
             {"ID_Pais": "ABW", "Descripcion": "Aruba"},
             {"ID_Pais": "AUS", "Descripcion": "Australia"},
             {"ID_Pais": "AUT", "Descripcion": "Austria"},
             {"ID_Pais": "AZE", "Descripcion": "Azerbaiyán"},
             {"ID_Pais": "BHS", "Descripcion": "Bahamas"},
             {"ID_Pais": "BHR", "Descripcion": "Bahrein"},
             {"ID_Pais": "BGD", "Descripcion": "Bangladesh"},
             {"ID_Pais": "BRB", "Descripcion": "Barbados"},
             {"ID_Pais": "BLZ", "Descripcion": "Belice"},
             {"ID_Pais": "BEN", "Descripcion": "Benin"},
             {"ID_Pais": "BMU", "Descripcion": "Bermudas"},
             {"ID_Pais": "BTN", "Descripcion": "Bhután"},
             {"ID_Pais": "BLR", "Descripcion": "Bielorrusia"},
             {"ID_Pais": "BOL", "Descripcion": "Bolivia"},
             {"ID_Pais": "BIH", "Descripcion": "Bosnia-Herzegovina"},
             {"ID_Pais": "BWA", "Descripcion": "Botswana"},
             {"ID_Pais": "BRA", "Descripcion": "Brasil"},
             {"ID_Pais": "BRN", "Descripcion": "Brunéi"},
             {"ID_Pais": "BGR", "Descripcion": "Bulgaria"},
             {"ID_Pais": "BFA", "Descripcion": "Burkina Fasso"},
             {"ID_Pais": "BDI", "Descripcion": "Burundi"},
             {"ID_Pais": "BEL", "Descripcion": "Bélgica"},
             {"ID_Pais": "CPV", "Descripcion": "Cabo Verde"},
             {"ID_Pais": "KHM", "Descripcion": "Camboya"},
             {"ID_Pais": "CMR", "Descripcion": "Camerún"},
             {"ID_Pais": "CAN", "Descripcion": "Canadá"},
             {"ID_Pais": "TCD", "Descripcion": "Chad"},
             {"ID_Pais": "CHL", "Descripcion": "Chile"},
             {"ID_Pais": "CHN", "Descripcion": "China"},
             {"ID_Pais": "CYP", "Descripcion": "Chipre"},
             {"ID_Pais": "COL", "Descripcion": "Colombia"},
             {"ID_Pais": "COM", "Descripcion": "Comoras"},
             {"ID_Pais": "COG", "Descripcion": "Congo, República del"},
             {"ID_Pais": "COD", "Descripcion": "Congo, República Democrática del"},
             {"ID_Pais": "PRK", "Descripcion": "Corea, Rep. Popular Democrática"},
             {"ID_Pais": "KOR", "Descripcion": "Corea, República de"},
             {"ID_Pais": "CIV", "Descripcion": "Costa de Marfil"},
             {"ID_Pais": "CRI", "Descripcion": "Costa Rica"},
             {"ID_Pais": "HRV", "Descripcion": "Croacia"},
             {"ID_Pais": "CUB", "Descripcion": "Cuba"},
             {"ID_Pais": "DNK", "Descripcion": "Dinamarca"},
             {"ID_Pais": "DMA", "Descripcion": "Dominica"},
             {"ID_Pais": "ECU", "Descripcion": "Ecuador"},
             {"ID_Pais": "EGY", "Descripcion": "Egipto"},
             {"ID_Pais": "SLV", "Descripcion": "El Salvador"},
             {"ID_Pais": "ARE", "Descripcion": "Emiratos Arabes Unidos"},
             {"ID_Pais": "ERI", "Descripcion": "Eritrea"},
             {"ID_Pais": "SVK", "Descripcion": "Eslovaquia"},
             {"ID_Pais": "SVN", "Descripcion": "Eslovenia"},
             {"ID_Pais": "USA", "Descripcion": "Estados Unidos de América"},
             {"ID_Pais": "EST", "Descripcion": "Estonia"},
             {"ID_Pais": "ETH", "Descripcion": "Etiopía"},
             {"ID_Pais": "PHL", "Descripcion": "Filipinas"},
             {"ID_Pais": "FIN", "Descripcion": "Finlandia"},
             {"ID_Pais": "FRA", "Descripcion": "Francia"},
             {"ID_Pais": "GAB", "Descripcion": "Gabón"},
             {"ID_Pais": "GMB", "Descripcion": "Gambia"},
             {"ID_Pais": "GEO", "Descripcion": "Georgia"},
             {"ID_Pais": "GHA", "Descripcion": "Ghana"},
             {"ID_Pais": "GIB", "Descripcion": "Gibraltar"},
             {"ID_Pais": "GRD", "Descripcion": "Granada"},
             {"ID_Pais": "GRC", "Descripcion": "Grecia"},
             {"ID_Pais": "GRL", "Descripcion": "Groenlandia"},
             {"ID_Pais": "GLP", "Descripcion": "Guadalupe"},
             {"ID_Pais": "GUM", "Descripcion": "Guam"},
             {"ID_Pais": "GTM", "Descripcion": "Guatemala"},
             {"ID_Pais": "GUF", "Descripcion": "Guayana Francesa"},
             {"ID_Pais": "GIN", "Descripcion": "Guinea"},
             {"ID_Pais": "GNQ", "Descripcion": "Guinea Ecuatorial"},
             {"ID_Pais": "GNB", "Descripcion": "Guinea-Bissau"},
             {"ID_Pais": "GUY", "Descripcion": "Guyana"},
             {"ID_Pais": "HTI", "Descripcion": "Haití"},
             {"ID_Pais": "HND", "Descripcion": "Honduras"},
             {"ID_Pais": "HKG", "Descripcion": "Hong-Kong"},
             {"ID_Pais": "HUN", "Descripcion": "Hungría"},
             {"ID_Pais": "IND", "Descripcion": "India"},
             {"ID_Pais": "IDN", "Descripcion": "Indonesia"},
             {"ID_Pais": "IRQ", "Descripcion": "Irak"},
             {"ID_Pais": "IRL", "Descripcion": "Irlanda"},
             {"ID_Pais": "IRN", "Descripcion": "Irán"},
             {"ID_Pais": "BVT", "Descripcion": "Isla Bouvert"},
             {"ID_Pais": "GGY", "Descripcion": "Isla de Guernesey"},
             {"ID_Pais": "JEY", "Descripcion": "Isla de Jersey"},
             {"ID_Pais": "IMN", "Descripcion": "Isla de Man"},
             {"ID_Pais": "CXR", "Descripcion": "Isla de Navidad"},
             {"ID_Pais": "ISL", "Descripcion": "Islandia"},
             {"ID_Pais": "CYM", "Descripcion": "Islas Caimán"},
             {"ID_Pais": "CCK", "Descripcion": "Islas Cocos"},
             {"ID_Pais": "COK", "Descripcion": "Islas Cook"},
             {"ID_Pais": "FLK", "Descripcion": "Islas Falkland (Malvinas)"},
             {"ID_Pais": "FRO", "Descripcion": "Islas Feroé"},
             {"ID_Pais": "FJI", "Descripcion": "Islas Fidji"},
             {"ID_Pais": "SGS", "Descripcion": "Islas Georgias del Sur y Sandwich"},
             {"ID_Pais": "HMD", "Descripcion": "Islas Heard e Mcdonald"},
             {"ID_Pais": "MNP", "Descripcion": "Islas Marianas del Norte"},
             {"ID_Pais": "MHL", "Descripcion": "Islas Marshall"},
             {"ID_Pais": "UMI", "Descripcion": "Islas Menores de EEUU"},
             {"ID_Pais": "NFK", "Descripcion": "Islas Norfolk"},
             {"ID_Pais": "PCN", "Descripcion": "Islas Pitcairn"},
             {"ID_Pais": "SLB", "Descripcion": "Islas Salomón"},
             {"ID_Pais": "TCA", "Descripcion": "Islas Turcas y Caicos"},
             {"ID_Pais": "VGB", "Descripcion": "Islas Vírgenes Británicas"},
             {"ID_Pais": "VIR", "Descripcion": "Islas Vírgenes de los EEUU"},
             {"ID_Pais": "WLF", "Descripcion": "Islas Wallis y Futura"},
             {"ID_Pais": "ALA", "Descripcion": "Islas Åland"},
             {"ID_Pais": "ISR", "Descripcion": "Israel"},
             {"ID_Pais": "ITA", "Descripcion": "Italia"},
             {"ID_Pais": "JAM", "Descripcion": "Jamaica"},
             {"ID_Pais": "JPN", "Descripcion": "Japón"},
             {"ID_Pais": "JOR", "Descripcion": "Jordania"},
             {"ID_Pais": "KAZ", "Descripcion": "Kazajstán"},
             {"ID_Pais": "KEN", "Descripcion": "Kenia"},
             {"ID_Pais": "KGZ", "Descripcion": "Kirguistán"},
             {"ID_Pais": "KIR", "Descripcion": "Kiribati"},
             {"ID_Pais": "KWT", "Descripcion": "Kuwait"},
             {"ID_Pais": "LAO", "Descripcion": "Laos"},
             {"ID_Pais": "LSO", "Descripcion": "Lesotho"},
             {"ID_Pais": "LVA", "Descripcion": "Letonia"},
             {"ID_Pais": "LBY", "Descripcion": "Libia"},
             {"ID_Pais": "LBR", "Descripcion": "Libéria"},
             {"ID_Pais": "LIE", "Descripcion": "Liechtenstein"},
             {"ID_Pais": "LTU", "Descripcion": "Lituania"},
             {"ID_Pais": "LUX", "Descripcion": "Luxemburgo"},
             {"ID_Pais": "LBN", "Descripcion": "Líbano"},
             {"ID_Pais": "MAC", "Descripcion": "Macao"},
             {"ID_Pais": "MKD", "Descripcion": "Macedonia, ARY"},
             {"ID_Pais": "MDG", "Descripcion": "Madagascar"},
             {"ID_Pais": "MYS", "Descripcion": "Malasia"},
             {"ID_Pais": "MWI", "Descripcion": "Malawi"},
             {"ID_Pais": "MDV", "Descripcion": "Maldivas"},
             {"ID_Pais": "MLT", "Descripcion": "Malta"},
             {"ID_Pais": "MLI", "Descripcion": "Malí"},
             {"ID_Pais": "MAR", "Descripcion": "Marruecos"},
             {"ID_Pais": "MTQ", "Descripcion": "Martinica"},
             {"ID_Pais": "MUS", "Descripcion": "Mauricio"},
             {"ID_Pais": "MRT", "Descripcion": "Mauritania"},
             {"ID_Pais": "MYT", "Descripcion": "Mayotte"},
             {"ID_Pais": "FSM", "Descripcion": "Micronesia"},
             {"ID_Pais": "MDA", "Descripcion": "Moldavia"},
             {"ID_Pais": "MNG", "Descripcion": "Mongolia"},
             {"ID_Pais": "MNE", "Descripcion": "Montenegro"},
             {"ID_Pais": "MSR", "Descripcion": "Montserrat"},
             {"ID_Pais": "MOZ", "Descripcion": "Mozambique"},
             {"ID_Pais": "MMR", "Descripcion": "Myanmar"},
             {"ID_Pais": "MEX", "Descripcion": "México"},
             {"ID_Pais": "MCO", "Descripcion": "Mónaco"},
             {"ID_Pais": "NAM", "Descripcion": "Namibia"},
             {"ID_Pais": "NRU", "Descripcion": "Naurú"},
             {"ID_Pais": "NPL", "Descripcion": "Nepal"},
             {"ID_Pais": "NIC", "Descripcion": "Nicaragua"},
             {"ID_Pais": "NGA", "Descripcion": "Nigeria"},
             {"ID_Pais": "NIU", "Descripcion": "Niue"},
             {"ID_Pais": "NOR", "Descripcion": "Noruega"},
             {"ID_Pais": "NCL", "Descripcion": "Nueva Caledonia"},
             {"ID_Pais": "NZL", "Descripcion": "Nueva Zelanda"},
             {"ID_Pais": "NER", "Descripcion": "Níger"},
             {"ID_Pais": "OMN", "Descripcion": "Omán"},
             {"ID_Pais": "PAK", "Descripcion": "Pakistán"},
             {"ID_Pais": "PLW", "Descripcion": "Palau"},
             {"ID_Pais": "PSE", "Descripcion": "Palestina, Territorio ocupado"},
             {"ID_Pais": "PAN", "Descripcion": "Panamá"},
             {"ID_Pais": "PNG", "Descripcion": "Papua Nueva Guinea"},
             {"ID_Pais": "PRY", "Descripcion": "Paraguay"},
             {"ID_Pais": "NLD", "Descripcion": "Países Bajos"},
             {"ID_Pais": "PER", "Descripcion": "Perú"},
             {"ID_Pais": "PYF", "Descripcion": "Polinesia Francesa"},
             {"ID_Pais": "POL", "Descripcion": "Polonia"},
             {"ID_Pais": "PRT", "Descripcion": "Portugal"},
             {"ID_Pais": "PRI", "Descripcion": "Puerto Rico"},
             {"ID_Pais": "QAT", "Descripcion": "Qatar"},
             {"ID_Pais": "GBR", "Descripcion": "Reino Unido"},
             {"ID_Pais": "CAF", "Descripcion": "República Centroafricana"},
             {"ID_Pais": "CZE", "Descripcion": "República Checa"},
             {"ID_Pais": "DOM", "Descripcion": "República Dominicana"},
             {"ID_Pais": "REU", "Descripcion": "Reunión"},
             {"ID_Pais": "ROU", "Descripcion": "Rumania"},
             {"ID_Pais": "RUS", "Descripcion": "Rusia"},
             {"ID_Pais": "RWA", "Descripcion": "Rwanda"},
             {"ID_Pais": "ESH", "Descripcion": "Sahara Occidental"},
             {"ID_Pais": "KNA", "Descripcion": "Saint Kitts y Nevis"},
             {"ID_Pais": "WSM", "Descripcion": "Samoa"},
             {"ID_Pais": "ASM", "Descripcion": "Samoa Americana"},
             {"ID_Pais": "BLM", "Descripcion": "San Bartolomé"},
             {"ID_Pais": "SMR", "Descripcion": "San Marino"},
             {"ID_Pais": "MAF", "Descripcion": "San Martín"},
             {"ID_Pais": "SPM", "Descripcion": "San Pedro y Miquelón"},
             {"ID_Pais": "VCT", "Descripcion": "San Vicente y las Granadinas"},
             {"ID_Pais": "SHN", "Descripcion": "Santa Elena"},
             {"ID_Pais": "LCA", "Descripcion": "Santa Lucía"},
             {"ID_Pais": "STP", "Descripcion": "Santo Tomé y Príncipe"},
             {"ID_Pais": "SEN", "Descripcion": "Senegal"},
             {"ID_Pais": "SRB", "Descripcion": "Serbia"},
             {"ID_Pais": "SYC", "Descripcion": "Seychelles"},
             {"ID_Pais": "SLE", "Descripcion": "Sierra Leona"},
             {"ID_Pais": "SGP", "Descripcion": "Singapur"},
             {"ID_Pais": "SYR", "Descripcion": "Siria"},
             {"ID_Pais": "SOM", "Descripcion": "Somalia"},
             {"ID_Pais": "LKA", "Descripcion": "Sri Lanka"},
             {"ID_Pais": "SWZ", "Descripcion": "Suazilandia"},
             {"ID_Pais": "ZAF", "Descripcion": "Sudáfrica"},
             {"ID_Pais": "SDN", "Descripcion": "Sudán"},
             {"ID_Pais": "SWE", "Descripcion": "Suecia"},
             {"ID_Pais": "CHE", "Descripcion": "Suiza"},
             {"ID_Pais": "SUR", "Descripcion": "Suriname"},
             {"ID_Pais": "SJM", "Descripcion": "Svalbard e Islas de Jan Mayen"},
             {"ID_Pais": "THA", "Descripcion": "Tailandia"},
             {"ID_Pais": "TWN", "Descripcion": "Taiwán"},
             {"ID_Pais": "TZA", "Descripcion": "Tanzania"},
             {"ID_Pais": "TJK", "Descripcion": "Tayikistan"},
             {"ID_Pais": "IOT", "Descripcion": "Terr. Británico del Oc. Indico"},
             {"ID_Pais": "ATF", "Descripcion": "Tierras Australes Francesas"},
             {"ID_Pais": "TLS", "Descripcion": "Timor Oriental"},
             {"ID_Pais": "TGO", "Descripcion": "Togo"},
             {"ID_Pais": "TKL", "Descripcion": "Tokelau"},
             {"ID_Pais": "TON", "Descripcion": "Tonga"},
             {"ID_Pais": "TTO", "Descripcion": "Trinidad y Tobago"},
             {"ID_Pais": "TKM", "Descripcion": "Turkmenistán"},
             {"ID_Pais": "TUR", "Descripcion": "Turquía"},
             {"ID_Pais": "TUV", "Descripcion": "Tuvalu"},
             {"ID_Pais": "TUN", "Descripcion": "Túnez"},
             {"ID_Pais": "UKR", "Descripcion": "Ucrania"},
             {"ID_Pais": "UGA", "Descripcion": "Uganda"},
             {"ID_Pais": "URY", "Descripcion": "Uruguay"},
             {"ID_Pais": "UZB", "Descripcion": "Uzbekistán"},
             {"ID_Pais": "VUT", "Descripcion": "Vanuatu"},
             {"ID_Pais": "VAT", "Descripcion": "Vaticano, Santa Sede"},
             {"ID_Pais": "VEN", "Descripcion": "Venezuela"},
             {"ID_Pais": "VNM", "Descripcion": "Vietnam"},
             {"ID_Pais": "YEM", "Descripcion": "Yemen"},
             {"ID_Pais": "DJI", "Descripcion": "Yibuti"},
             {"ID_Pais": "ZMB", "Descripcion": "Zambia"},
             {"ID_Pais": "ZWE", "Descripcion": "Zimbabwe"},
             {"ID_Pais": "KOS", "Descripcion": "Kosovo"},
             {"ID_Pais": "ES111", "Descripcion": "A Coruña"},
             {"ID_Pais": "ES112", "Descripcion": "Lugo"},
             {"ID_Pais": "ES113", "Descripcion": "Ourense"},
             {"ID_Pais": "ES114", "Descripcion": "Pontevedra"},
             {"ID_Pais": "ES120", "Descripcion": "Asturias"},
             {"ID_Pais": "ES130", "Descripcion": "Cantabria"},
             {"ID_Pais": "ES211", "Descripcion": "Araba/Álava"},
             {"ID_Pais": "ES212", "Descripcion": "Gipuzkoa"},
             {"ID_Pais": "ES213", "Descripcion": "Bizkaia"},
             {"ID_Pais": "ES220", "Descripcion": "Navarra"},
             {"ID_Pais": "ES230", "Descripcion": "La Rioja"},
             {"ID_Pais": "ES241", "Descripcion": "Huesca"},
             {"ID_Pais": "ES242", "Descripcion": "Teruel"},
             {"ID_Pais": "ES243", "Descripcion": "Zaragoza"},
             {"ID_Pais": "ES300", "Descripcion": "Madrid"},
             {"ID_Pais": "ES411", "Descripcion": "Ávila"},
             {"ID_Pais": "ES412", "Descripcion": "Burgos"},
             {"ID_Pais": "ES413", "Descripcion": "León"},
             {"ID_Pais": "ES414", "Descripcion": "Palencia"},
             {"ID_Pais": "ES415", "Descripcion": "Salamanca"},
             {"ID_Pais": "ES416", "Descripcion": "Segovia"},
             {"ID_Pais": "ES417", "Descripcion": "Soria"},
             {"ID_Pais": "ES418", "Descripcion": "Valladolid"},
             {"ID_Pais": "ES419", "Descripcion": "Zamora"},
             {"ID_Pais": "ES421", "Descripcion": "Albacete"},
             {"ID_Pais": "ES422", "Descripcion": "Ciudad Real"},
             {"ID_Pais": "ES423", "Descripcion": "Cuenca"},
             {"ID_Pais": "ES424", "Descripcion": "Guadalajara"},
             {"ID_Pais": "ES425", "Descripcion": "Toledo"},
             {"ID_Pais": "ES431", "Descripcion": "Badajoz"},
             {"ID_Pais": "ES432", "Descripcion": "Cáceres"},
             {"ID_Pais": "ES511", "Descripcion": "Barcelona"},
             {"ID_Pais": "ES512", "Descripcion": "Girona"},
             {"ID_Pais": "ES513", "Descripcion": "Lleida"},
             {"ID_Pais": "ES514", "Descripcion": "Tarragona"},
             {"ID_Pais": "ES521", "Descripcion": "Alicante / Alacant"},
             {"ID_Pais": "ES522", "Descripcion": "Castellón / Castelló"},
             {"ID_Pais": "ES523", "Descripcion": "Valencia / Valéncia"},
             {"ID_Pais": "ES530", "Descripcion": "Illes Balears"},
             {"ID_Pais": "ES531", "Descripcion": "Eivissa y Formentera"},
             {"ID_Pais": "ES532", "Descripcion": "Mallorca"},
             {"ID_Pais": "ES533", "Descripcion": "Menorca"},
             {"ID_Pais": "ES611", "Descripcion": "Almería"},
             {"ID_Pais": "ES612", "Descripcion": "Cádiz"},
             {"ID_Pais": "ES613", "Descripcion": "Córdoba"},
             {"ID_Pais": "ES614", "Descripcion": "Granada"},
             {"ID_Pais": "ES615", "Descripcion": "Huelva"},
             {"ID_Pais": "ES616", "Descripcion": "Jaén"},
             {"ID_Pais": "ES617", "Descripcion": "Málaga"},
             {"ID_Pais": "ES618", "Descripcion": "Sevilla"},
             {"ID_Pais": "ES620", "Descripcion": "Murcia"},
             {"ID_Pais": "ES630", "Descripcion": "Ceuta"},
             {"ID_Pais": "ES640", "Descripcion": "Melilla"},
             {"ID_Pais": "ES701", "Descripcion": "Las Palmas"},
             {"ID_Pais": "ES702", "Descripcion": "Santa Cruz de Tenerife"},
             {"ID_Pais": "ES703", "Descripcion": "El Hierro"},
             {"ID_Pais": "ES704", "Descripcion": "Fuerteventura"},
             {"ID_Pais": "ES705", "Descripcion": "Gran Canaria"},
             {"ID_Pais": "ES706", "Descripcion": "La Gomera"},
             {"ID_Pais": "ES707", "Descripcion": "La Palma"},
             {"ID_Pais": "ES708", "Descripcion": "Lanzarote"},
             {"ID_Pais": "ES709", "Descripcion": "Tenerife"}
             ]
        # Diccionario con los nombre de los Paises usando los del INE [4]
        _logger.info("DataBi: Calculating %s countries", str(len(dic_ine)))
        for prop in propertys:
            for pais in dic_ine:
                dic_pais.append({"ID_Hotel": prop.id,
                                 "ID_Pais": pais["ID_Pais"],
                                 "Descripcion": pais["Descripcion"],})
        return dic_pais

    @api.model
    def data_bi_regimen(self, propertys):
        # Diccionario con los Board Services [5]
        dic_regimen = []
        board_services = self.env["pms.board.service"].search_read([])
        _logger.info("DataBi: Calculating %s board services", str(len(board_services)))
        for prop in propertys:
            dic_regimen.append(
                {
                    "ID_Hotel": prop.id,
                    "ID_Regimen": 0,
                    "Descripcion": u"Sin régimen",
                }
            )
            for board_service in board_services:
                if (not board_service["pms_property_ids"]) or (
                    prop.id in board_service["pms_property_ids"]
                ):
                    dic_regimen.append(
                        {
                            "ID_Hotel": prop.id,
                            "ID_Regimen": board_service["id"],
                            "Descripcion": board_service["name"],
                        }
                    )
        return dic_regimen

    @api.model
    def data_bi_capacidad(self, propertys):
        # Diccionario con las capacidades  [7]
        rooms = self.env["pms.room.type"].search_read([])
        _logger.info("DataBi: Calculating %s room capacity", str(len(rooms)))
        dic_capacidad = []
        for prop in propertys:
            for room in rooms:
                if (not room["pms_property_ids"]) or (
                    prop.id in room["pms_property_ids"]
                ):
                    dic_capacidad.append(
                        {
                            "ID_Hotel": prop.id,
                            "Hasta_Fecha": (
                                date.today() + timedelta(days=365 * 3)
                            ).strftime("%Y-%m-%d"),
                            "ID_Tipo_Habitacion": room["id"],
                            "Nro_Habitaciones": room["total_rooms_count"],
                        }
                    )
        return dic_capacidad

    @api.model
    def data_bi_habitacione(self, propertys):
        # Diccionario con Rooms types [8]
        rooms = self.env["pms.room.type"].search([])
        _logger.info("DataBi: Calculating %s room types", str(len(rooms)))
        dic_tipo_habitacion = []
        for prop in propertys:
            for room in rooms:
                if (not room.pms_property_ids) or (
                    prop.id in room.pms_property_ids.ids
                ):
                    dic_tipo_habitacion.append(
                        {
                            "ID_Hotel": prop.id,
                            "ID_Tipo_Habitacion": room["id"],
                            "Descripcion": room["name"],
                            "Estancias": room.get_capacity(),
                        }
                    )
        return dic_tipo_habitacion

    @api.model
    def data_bi_budget(self, propertys):
        # Diccionario con las previsiones Budget [9]
        budgets = self.env["pms.budget"].search([])
        _logger.info("DataBi: Calculating %s budget", str(len(budgets)))
        dic_budget = []
        for prop in propertys:
            for budget in budgets:
                if budget.pms_property_id.id == prop.id:
                    dic_budget.append(
                        {
                            "ID_Hotel": prop.id,
                            "Fecha": str(budget.year)
                            + "-"
                            + str(budget.month).zfill(2)
                            + "-01",
                            # 'ID_Tarifa': 0,
                            # 'ID_Canal': 0,
                            # 'ID_Pais': 0,
                            # 'ID_Regimen': 0,
                            # 'ID_Tipo_Habitacion': 0,
                            # 'ID_Cliente': 0,
                            "Room_Nights": budget.room_nights,
                            "Room_Revenue": budget.room_revenue,
                            # 'Pension_Revenue': 0,
                            "Estancias": budget.estancias,
                        }
                    )
            # Fecha fecha Primer día del mes
            # ID_Tarifa numérico Código de la Tarifa
            # ID_Canal numérico Código del Canal
            # ID_Pais numérico Código del País
            # ID_Regimen numérico Cóigo del Régimen
            # ID_Tipo_Habitacion numérico Código del Tipo de Habitación
            # iD_Segmento numérico Código del Segmento
            # ID_Cliente numérico Código del Cliente
            # Pension_Revenue numérico con dos decimales Ingresos por Pensión
        return dic_budget

    @api.model
    def data_bi_moti_bloq(self, propertys):
        # Diccionario con Motivo de Bloqueos [11]
        lineas = self.env["room.closure.reason"].search([])
        dic_moti_bloq = []
        _logger.info("DataBi: Calculating %s blocking reasons", str(len(lineas)))
        for prop in propertys:
            dic_moti_bloq.append(
                {
                    "ID_Hotel": prop.id,
                    "ID_Motivo_Bloqueo": "B0",
                    "Descripcion": u"Ninguno",
                }
            )
            dic_moti_bloq.append(
                {
                    "ID_Hotel": prop.id,
                    "ID_Motivo_Bloqueo": "ST",
                    "Descripcion": u"Staff",
                }
            )
            for linea in lineas:
                if (not linea.pms_property_ids) or (
                    prop.id in linea.pms_property_ids.ids
                ):
                    dic_moti_bloq.append(
                        {
                            "ID_Hotel": prop.id,
                            "ID_Motivo_Bloqueo": "B" + str(linea.id),
                            "Descripcion": linea.name,
                        }
                    )
        return dic_moti_bloq

    @api.model
    def data_bi_segment(self, propertys):
        # Diccionario con Segmentación [12]
        # TODO solo las que tienen un padre?... ver la gestion... etc....
        dic_segmentos = []
        lineas = self.env["res.partner.category"].search([])
        _logger.info("DataBi: Calculating %s segmentations", str(len(lineas)))
        for prop in propertys:
            for linea in lineas:
                if linea.parent_id.name:
                    seg_desc = linea.parent_id.name + " / " + linea.name
                    dic_segmentos.append(
                        {
                            "ID_Hotel": prop.id,
                            "ID_Segmento": linea.id,
                            "Descripcion": seg_desc,
                        }
                    )
        return dic_segmentos

    @api.model
    def data_bi_client(self, propertys):
        # Diccionario con Clientes (OTAs y agencias) [13]
        dic_clientes = []
        lineas = self.env["res.partner"].search([("is_agency", "=", True)])
        _logger.info("DataBi: Calculating %s Operators", str(len(lineas)))
        for prop in propertys:
            dic_clientes.append(
                {"ID_Hotel": prop.id, "ID_Cliente": 0, "Descripcion": u"Ninguno"}
            )
            for linea in lineas:
                dic_clientes.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Cliente": linea.id,
                        "Descripcion": linea.name,
                    }
                )
        return dic_clientes

    @api.model
    def data_bi_estados(self, propertys, estado_array):
        # Diccionario con los Estados Reserva [14]
        _logger.info("DataBi: Calculating states of the reserves")
        dic_estados = []
        estado_array_txt = [
            "Borrador",
            "Confirmada",
            "Hospedandose",
            "Checkout",
            "Cancelada",
            "No Show",
            "No Checkout",
        ]
        for prop in propertys:
            for i in range(0, len(estado_array)):
                dic_estados.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_EstadoReserva": str(i),
                        "Descripcion": estado_array_txt[i],
                    }
                )
        return dic_estados

    @api.model
    def data_bi_rooms(self, propertys):
        # Diccionario con las habitaciones [15]
        dic_rooms = []
        rooms = self.env["pms.room"].search([])
        _logger.info("DataBi: Calculating %s name rooms.", str(len(rooms)))
        for prop in propertys:
            for room in rooms.filtered(lambda n: (n.pms_property_id.id == prop.id)):
                dic_rooms.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Room": room.id,
                        "Descripcion": room.name,
                    }
                )
        return dic_rooms

    @api.model
    def data_bi_bloqueos(self, propertys, lines):
        # Diccionario con Bloqueos [10]
        dic_bloqueos = []
        lines = lines.filtered(
            lambda n: (n.reservation_id.reservation_type != "normal")
            and (n.reservation_id.state != "cancelled")
        )
        _logger.info("DataBi: Calculating %s Bloqued", str(len(lines)))
        for line in lines:

            if line.pms_property_id.id in propertys.ids:
                motivo = "0"
                if line.reservation_id.reservation_type == "out":
                    motivo = (
                        "B0"
                        if not line.reservation_id.closure_reason_id.id
                        else ("B" + str(line.reservation_id.closure_reason_id.id))
                    )

                elif line.reservation_id.reservation_type == "staff":
                    motivo = "ST"
                dic_bloqueos.append(
                    {
                        "ID_Hotel": line.pms_property_id.id,
                        "Fecha_desde": line.date.strftime("%Y-%m-%d"),
                        "Fecha_hasta": (line.date + timedelta(days=1)).strftime(
                            "%Y-%m-%d"
                        ),
                        "ID_Tipo_Habitacion": line.reservation_id.room_type_id.id,
                        "ID_Motivo_Bloqueo": motivo,
                        "Nro_Habitaciones": 1,
                    }
                )
        return dic_bloqueos

    @api.model
    def data_bi_reservas(self, propertys, lines, estado_array):
        # Diccionario con Reservas  [6]
        dic_reservas = []

        for prop in propertys:
            lineas = lines.filtered(
                lambda n: (n.pms_property_id.id == prop.id)
                and (n.reservation_id.reservation_type == "normal")
                and (n.price > 0)
            )
            _logger.info(
                "DataBi: Calculating %s reservations in %s ",
                str(len(lineas)),
                prop.name,
            )

            for linea in lineas:
                if linea.reservation_id.segmentation_ids:
                    id_segmen = linea.reservation_id.segmentation_ids[0].id
                elif linea.reservation_id.folio_id.segmentation_ids:
                    id_segmen = linea.reservation_id.folio_id.segmentation_ids[0].id
                else:
                    id_segmen = 0

                regimen = (
                    0
                    if not linea.reservation_id.board_service_room_id
                    else linea.reservation_id.board_service_room_id.id
                )

                cuna = 0
                for service in linea.reservation_id.service_ids:
                    if service.product_id.is_crib:
                        cuna += 1

                canal = (
                    linea.reservation_id.channel_type_id.id
                    if linea.reservation_id.channel_type_id.id
                    else 0
                )

                cliente = (
                    linea.reservation_id.agency_id.id
                    if linea.reservation_id.agency_id.id
                    else 0
                )

                dic_reservas.append(
                    {
                        "ID_Reserva": linea.reservation_id.folio_id.id,
                        "ID_Hotel": prop.id,
                        "ID_EstadoReserva": estado_array.index(
                            linea.reservation_id.state
                        ),
                        "FechaVenta": linea.reservation_id.create_date.strftime(
                            "%Y-%m-%d"
                        ),
                        "ID_Segmento": id_segmen,
                        "ID_Cliente": cliente,
                        "ID_Canal": canal,
                        "FechaExtraccion": date.today().strftime("%Y-%m-%d"),
                        "Entrada": linea.date.strftime("%Y-%m-%d"),
                        "Salida": (linea.date + timedelta(days=1)).strftime("%Y-%m-%d"),
                        "Noches": 1,
                        "ID_TipoHabitacion": linea.reservation_id.room_type_id.id,
                        "ID_HabitacionDuerme": linea.room_id.room_type_id.id,
                        "ID_Regimen": regimen,
                        "Adultos": linea.reservation_id.adults,
                        "Menores": linea.reservation_id.children,
                        "Cunas": cuna,
                        "PrecioDiario": linea.price,
                        "PrecioDto": linea.discount * (linea.price / 100),
                        "PrecioComision": linea.reservation_id.commission_amount
                        / len(linea.reservation_id.reservation_line_ids),
                        "PrecioIva": linea.reservation_id.sale_line_ids.tax_ids.amount
                        * linea.price
                        / 100,
                        "ID_Tarifa": linea.reservation_id.pricelist_id.id,
                        "ID_Pais": self.data_bi_get_codeine(linea),
                        "ID_Room": linea.room_id.id,
                        "FechaCancelacion": "NONE",
                        "ID_Folio": linea.reservation_id.folio_id.name,
                    }
                )

                if linea.reservation_id.state == "cancelled":
                    dic_reservas[-1][
                        "FechaCancelacion"
                    ] = linea.reservation_id.write_date.strftime("%Y-%m-%d")

                # ID_Reserva numérico Código único de la reserva
                # ID_Hotel numérico Código del Hotel
                # ID_EstadoReserva numérico Código del estado de la reserva
                # FechaVenta fecha Fecha de la venta de la reserva
                # ID_Segmento numérico Código del Segmento de la reserva
                # ID_Cliente Numérico Código del Cliente de la reserva
                # ID_Canal numérico Código del Canal
                # FechaExtraccion fecha Fecha de la extracción de los datos (Foto)
                # Entrada fecha Fecha de entrada
                # Salida fecha Fecha de salida
                # Noches numérico Nro. de noches de la reserva
                # ID_TipoHabitacion numérico Código del Tipo de Habitación
                # ID_Regimen numérico Código del Tipo de Régimen
                # Adultos numérico Nro. de adultos
                # Menores numérico Nro. de menores
                # Cunas numérico Nro. de cunas
                # PrecioDiario numérico con 2 decimales Precio por noche de la reserva
                # ID_Tarifa numérico Código de la tarifa aplicada a la reserva
                # ID_Pais alfanumérico Código del país

        return dic_reservas

    @api.model
    def data_bi_get_codeine(self, reserva):
        response = "NONE"
        if reserva.reservation_id.partner_id.ine_code:
            response = reserva.reservation_id.partner_id.ine_code
        else:
            for partner in reserva.reservation_id.checkin_partner_ids:
                if partner.partner_id.ine_code:
                    response = partner.partner_id.ine_code
        return response
