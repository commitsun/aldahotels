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
estado_array = [
    "draft",
    "confirm",
    "onboard",
    "done",
    "cancel",
    "arrival_delayed",
    "departure_delayed",
]


class DataBi(models.Model):
    """Management and export data for MopSolution MyDataBI."""

    _name = "data_bi"
    _description = "Export DataBI"

    @api.model
    def export_reservations_data(self, hotelsdata=[0], fechafoto=False):
        limit_ago = self.calc_date_limit(fechafoto)
        hotels = self.calc_hoteles(hotelsdata)
        _logger.info("Exporting Reservations data Hotels IDs %s", hotels.ids)
        response = []
        for hotel in hotels:
            response.append(self.export_one(hotel, limit_ago, 6))
            response.append(self.export_one(hotel, limit_ago, 7))
            response.append(self.export_one(hotel, limit_ago, 9))
            response.append(self.export_one(hotel, limit_ago, 10))
        return json.dumps(response, ensure_ascii=False)

    @api.model
    def export_general_data(self, default_property=False):
        _logger.info("Exporting General data DataBI")
        response = []
        dic_hotel = []
        hotel = False
        propertys = self.env["pms.property"].search([])
        for property in propertys:
            dic_hotel.append({"ID_Hotel": property.id, "Descripci??n": property.name})
            if property.id == default_property:
                hotel = property
        response.append({"Hotel": dic_hotel})
        if not hotel:
            hotel = propertys[0]

        metodos = [
            [self.data_bi_tarifa, "Tarifa"],
            [self.data_bi_canal, "Canal"],
            [self.data_bi_pais, "Pais"],
            [self.data_bi_regimen, "Regimen"],
            [self.data_bi_moti_bloq, "Motivo Bloqueo"],
            [self.data_bi_segment, "Segmentos"],
            [self.data_bi_client, "Clientes"],
            [self.data_bi_habitacione, "Tipo Habitaci??n"],
            [self.data_bi_estados, "Estado Reservas"],
        ]
        for meto in metodos:
            response.append({meto[1]: self.clean_hotel_ids(meto[0](hotel))})
        response.append({"Nombre Habitaciones": self.data_bi_rooms(hotel)})
        return json.dumps(response, ensure_ascii=False)

    @api.model
    def calc_hoteles(self, hotelsdata):
        hotels = self.env["pms.property"].search([])
        if hotelsdata != [0]:
            hotels = self.env["pms.property"].search([("id", "in", hotelsdata)])
        return hotels

    @api.model
    def calc_date_limit(self, fechafoto):
        if not fechafoto:
            fechafoto = date.today().strftime("%Y-%m-%d")
        if type(fechafoto) is dict:
            fechafoto = date.today()
        else:
            fechafoto = datetime.strptime(fechafoto, "%Y-%m-%d").date()
        dias = self.env.user.data_bi_days
        limit_ago = (fechafoto - timedelta(days=dias)).strftime("%Y-%m-%d")
        _logger.info("Export Data %s days ago. From %s", dias, limit_ago)
        return limit_ago

    @api.model
    def clean_hotel_ids(self, datadict):
        for da in datadict:
            da.pop("ID_Hotel", None)
        return datadict

    @api.model
    def export_data_bi(self, archivo=0, default_property=[0], fechafoto=False):
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
            archivo == 8 'Tipo Habitaci??n'
            archivo == 9 'Budget'
            archivo == 10 'Bloqueos'
            archivo == 11 'Motivo Bloqueo'
            archivo == 12 'Segmentos'
            archivo == 13 'Clientes'
            archivo == 14 'Estado Reservas'
            archivo == 15 'Room names'
        fechafoto = start date to take data
        """
        limit_ago = self.calc_date_limit(fechafoto)
        hotels = self.calc_hoteles(default_property)

        _logger.warning(
            "-- ### Init Export Data_Bi Module parameters:  %s, %s, %s ### --",
            archivo,
            hotels.ids,
            fechafoto,
        )

        if archivo == 0:
            dic_export = self.export_all(hotels, limit_ago)
        else:
            dic_export = self.export_one(hotels, limit_ago, archivo)

        _logger.warning("--- ### End Export Data_Bi Module to Json ### ---")
        return json.dumps(dic_export, ensure_ascii=False)

    @api.model
    def export_all(self, hotels, limit_ago):
        line_res = self.env["pms.reservation.line"].search(
            [("pms_property_id", "in", hotels.ids),
             ("date", ">=", limit_ago)],
            order="id"
        )
        dic_reservas = self.data_bi_reservas(
            hotels,
            line_res,
            estado_array,
        )
        dic_export = [
            {"Tarifa": self.data_bi_tarifa(hotels)},
            {"Canal": self.data_bi_canal(hotels)},
            {"Hotel": self.data_bi_hotel()},
            {"Pais": self.data_bi_pais(hotels)},
            {"Regimen": self.data_bi_regimen(hotels)},
            {"Reservas": dic_reservas},
            {"Capacidad": self.data_bi_capacidad(hotels)},
            {"Tipo Habitaci??n": self.data_bi_habitacione(hotels)},
            {"Budget": self.data_bi_budget(hotels)},
            {"Bloqueos": self.data_bi_bloqueos(hotels, line_res)},
            {"Motivo Bloqueo": self.data_bi_moti_bloq(hotels)},
            {"Segmentos": self.data_bi_segment(hotels)},
            {"Clientes": self.data_bi_client(hotels)},
            {"Estado Reservas": self.data_bi_estados(hotels)},
            {"Nombre Habitaciones": self.data_bi_rooms(hotels, True)},
        ]
        return dic_export

    @api.model
    def export_one(self, hotels, limit_ago, archivo):
        if (archivo == 0) or (archivo == 10) or (archivo == 6):
            line_res = self.env["pms.reservation.line"].search(
                [("pms_property_id", "in", hotels.ids),
                 ("date", ">=", limit_ago)],
                order="id"
            )
            dic_reservas = self.data_bi_reservas(
                hotels,
                line_res,
                estado_array,
            )
        dic_export = []
        if archivo == 1:
            dic_export.append({"Tarifa": self.data_bi_tarifa(hotels)})
        elif archivo == 2:
            dic_export.append({"Canal": self.data_bi_canal(hotels)})
        elif archivo == 3:
            dic_export.append({"Hotel": self.data_bi_hotel()})
        elif archivo == 4:
            dic_export.append({"Pais": self.data_bi_pais(hotels)})
        elif archivo == 5:
            dic_export.append({"Regimen": self.data_bi_regimen(hotels)})
        elif archivo == 6:
            dic_export.append({"Reservas": dic_reservas})
        elif archivo == 7:
            dic_export.append({"Capacidad": self.data_bi_capacidad(hotels)})
        elif archivo == 8:
            dic_export.append({"Tipo Habitaci??n": self.data_bi_habitacione(hotels)})
        elif archivo == 9:
            dic_export.append({"Budget": self.data_bi_budget(hotels)})
        elif archivo == 10:
            dic_export.append({"Bloqueos": self.data_bi_bloqueos(hotels, line_res)})
        elif archivo == 11:
            dic_export.append({"Motivo Bloqueo": self.data_bi_moti_bloq(hotels)})
        elif archivo == 12:
            dic_export.append({"Segmentos": self.data_bi_segment(hotels)})
        elif archivo == 13:
            dic_export.append({"Clientes": self.data_bi_client(hotels)})
        elif archivo == 14:
            dic_export.append({"Estado Reservas": self.data_bi_estados(hotels)})
        elif archivo == 15:
            dic_export.append({"Nombre Habitaciones": self.data_bi_rooms(hotels, True)})
        return dic_export

    @api.model
    def data_bi_tarifa(self, hotels):
        # Diccionario con las tarifas [1]
        dic_tarifa = []

        for prop in hotels:
            tarifas = self.env["product.pricelist"].search_read(
                [
                    "|",
                    ("active", "=", False),
                    ("active", "=", True),
                    "|",
                    ("pms_property_ids", "in", prop.id),
                    ("pms_property_ids", "=", False),
                ],
                ["name"],
            )
            # _logger.info(
            #     "DataBi: Calculating %s fees in %s", str(len(tarifas)), prop.name
            # )
            for tarifa in tarifas:
                dic_tarifa.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Tarifa": tarifa["id"],
                        "Descripci??n": tarifa["name"],
                    }
                )
        return dic_tarifa

    @api.model
    def data_bi_canal(self, hotels):
        # Diccionario con los Canales [2]
        dic_canal = []
        channels = self.env["pms.sale.channel"].search([])
        # _logger.info("DataBi: Calculating %s Channels", str(len(channels)))
        for prop in hotels:
            dic_canal.append(
                {"ID_Hotel": prop.id, "ID_Canal": "0", "Descripci??n": u"Ninguno"}
            )
            for channel in channels:
                dic_canal.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Canal": channel["id"],
                        "Descripci??n": channel["name"],
                    }
                )
        return dic_canal

    @api.model
    def data_bi_hotel(self):
        # Diccionario con el/los nombre de los hoteles  [3]
        hoteles = self.env["pms.property"].search([])
        # _logger.info("DataBi: Calculating %s hotel names", str(len(hoteles)))

        dic_hotel = []
        for hotel in hoteles:
            dic_hotel.append({"ID_Hotel": hotel.id, "Descripci??n": hotel.name})
        return dic_hotel

    @api.model
    def data_bi_pais(self, hotels):
        dic_pais = []
        dic_ine = [
            {"ID_Pais": "NONE", "Descripci??n": "No Asignado"},
            {"ID_Pais": "AFG", "Descripci??n": "Afganist??n"},
            {"ID_Pais": "ALB", "Descripci??n": "Albania"},
            {"ID_Pais": "DEU", "Descripci??n": "Alemania"},
            {"ID_Pais": "AND", "Descripci??n": "Andorra"},
            {"ID_Pais": "AGO", "Descripci??n": "Angola"},
            {"ID_Pais": "AIA", "Descripci??n": "Anguila"},
            {"ID_Pais": "ATG", "Descripci??n": "Antigua y Barbuda"},
            {"ID_Pais": "ANT", "Descripci??n": "Antillas Neerlandesas"},
            {"ID_Pais": "ATA", "Descripci??n": "Ant??rtida"},
            {"ID_Pais": "SAU", "Descripci??n": "Arabia Saudita"},
            {"ID_Pais": "DZA", "Descripci??n": "Argelia"},
            {"ID_Pais": "ARG", "Descripci??n": "Argentina"},
            {"ID_Pais": "ARM", "Descripci??n": "Armenia"},
            {"ID_Pais": "ABW", "Descripci??n": "Aruba"},
            {"ID_Pais": "AUS", "Descripci??n": "Australia"},
            {"ID_Pais": "AUT", "Descripci??n": "Austria"},
            {"ID_Pais": "AZE", "Descripci??n": "Azerbaiy??n"},
            {"ID_Pais": "BHS", "Descripci??n": "Bahamas"},
            {"ID_Pais": "BHR", "Descripci??n": "Bahrein"},
            {"ID_Pais": "BGD", "Descripci??n": "Bangladesh"},
            {"ID_Pais": "BRB", "Descripci??n": "Barbados"},
            {"ID_Pais": "BLZ", "Descripci??n": "Belice"},
            {"ID_Pais": "BEN", "Descripci??n": "Benin"},
            {"ID_Pais": "BMU", "Descripci??n": "Bermudas"},
            {"ID_Pais": "BTN", "Descripci??n": "Bhut??n"},
            {"ID_Pais": "BLR", "Descripci??n": "Bielorrusia"},
            {"ID_Pais": "BOL", "Descripci??n": "Bolivia"},
            {"ID_Pais": "BIH", "Descripci??n": "Bosnia-Herzegovina"},
            {"ID_Pais": "BWA", "Descripci??n": "Botswana"},
            {"ID_Pais": "BRA", "Descripci??n": "Brasil"},
            {"ID_Pais": "BRN", "Descripci??n": "Brun??i"},
            {"ID_Pais": "BGR", "Descripci??n": "Bulgaria"},
            {"ID_Pais": "BFA", "Descripci??n": "Burkina Fasso"},
            {"ID_Pais": "BDI", "Descripci??n": "Burundi"},
            {"ID_Pais": "BEL", "Descripci??n": "B??lgica"},
            {"ID_Pais": "CPV", "Descripci??n": "Cabo Verde"},
            {"ID_Pais": "KHM", "Descripci??n": "Camboya"},
            {"ID_Pais": "CMR", "Descripci??n": "Camer??n"},
            {"ID_Pais": "CAN", "Descripci??n": "Canad??"},
            {"ID_Pais": "TCD", "Descripci??n": "Chad"},
            {"ID_Pais": "CHL", "Descripci??n": "Chile"},
            {"ID_Pais": "CHN", "Descripci??n": "China"},
            {"ID_Pais": "CYP", "Descripci??n": "Chipre"},
            {"ID_Pais": "COL", "Descripci??n": "Colombia"},
            {"ID_Pais": "COM", "Descripci??n": "Comoras"},
            {"ID_Pais": "COG", "Descripci??n": "Congo, Rep??blica del"},
            {"ID_Pais": "COD", "Descripci??n": "Congo, Rep??blica Democr??tica del"},
            {"ID_Pais": "PRK", "Descripci??n": "Corea, Rep. Popular Democr??tica"},
            {"ID_Pais": "KOR", "Descripci??n": "Corea, Rep??blica de"},
            {"ID_Pais": "CIV", "Descripci??n": "Costa de Marfil"},
            {"ID_Pais": "CRI", "Descripci??n": "Costa Rica"},
            {"ID_Pais": "HRV", "Descripci??n": "Croacia"},
            {"ID_Pais": "CUB", "Descripci??n": "Cuba"},
            {"ID_Pais": "DNK", "Descripci??n": "Dinamarca"},
            {"ID_Pais": "DMA", "Descripci??n": "Dominica"},
            {"ID_Pais": "ECU", "Descripci??n": "Ecuador"},
            {"ID_Pais": "EGY", "Descripci??n": "Egipto"},
            {"ID_Pais": "SLV", "Descripci??n": "El Salvador"},
            {"ID_Pais": "ARE", "Descripci??n": "Emiratos Arabes Unidos"},
            {"ID_Pais": "ERI", "Descripci??n": "Eritrea"},
            {"ID_Pais": "SVK", "Descripci??n": "Eslovaquia"},
            {"ID_Pais": "SVN", "Descripci??n": "Eslovenia"},
            {"ID_Pais": "USA", "Descripci??n": "Estados Unidos de Am??rica"},
            {"ID_Pais": "EST", "Descripci??n": "Estonia"},
            {"ID_Pais": "ETH", "Descripci??n": "Etiop??a"},
            {"ID_Pais": "PHL", "Descripci??n": "Filipinas"},
            {"ID_Pais": "FIN", "Descripci??n": "Finlandia"},
            {"ID_Pais": "FRA", "Descripci??n": "Francia"},
            {"ID_Pais": "GAB", "Descripci??n": "Gab??n"},
            {"ID_Pais": "GMB", "Descripci??n": "Gambia"},
            {"ID_Pais": "GEO", "Descripci??n": "Georgia"},
            {"ID_Pais": "GHA", "Descripci??n": "Ghana"},
            {"ID_Pais": "GIB", "Descripci??n": "Gibraltar"},
            {"ID_Pais": "GRD", "Descripci??n": "Granada"},
            {"ID_Pais": "GRC", "Descripci??n": "Grecia"},
            {"ID_Pais": "GRL", "Descripci??n": "Groenlandia"},
            {"ID_Pais": "GLP", "Descripci??n": "Guadalupe"},
            {"ID_Pais": "GUM", "Descripci??n": "Guam"},
            {"ID_Pais": "GTM", "Descripci??n": "Guatemala"},
            {"ID_Pais": "GUF", "Descripci??n": "Guayana Francesa"},
            {"ID_Pais": "GIN", "Descripci??n": "Guinea"},
            {"ID_Pais": "GNQ", "Descripci??n": "Guinea Ecuatorial"},
            {"ID_Pais": "GNB", "Descripci??n": "Guinea-Bissau"},
            {"ID_Pais": "GUY", "Descripci??n": "Guyana"},
            {"ID_Pais": "HTI", "Descripci??n": "Hait??"},
            {"ID_Pais": "HND", "Descripci??n": "Honduras"},
            {"ID_Pais": "HKG", "Descripci??n": "Hong-Kong"},
            {"ID_Pais": "HUN", "Descripci??n": "Hungr??a"},
            {"ID_Pais": "IND", "Descripci??n": "India"},
            {"ID_Pais": "IDN", "Descripci??n": "Indonesia"},
            {"ID_Pais": "IRQ", "Descripci??n": "Irak"},
            {"ID_Pais": "IRL", "Descripci??n": "Irlanda"},
            {"ID_Pais": "IRN", "Descripci??n": "Ir??n"},
            {"ID_Pais": "BVT", "Descripci??n": "Isla Bouvert"},
            {"ID_Pais": "GGY", "Descripci??n": "Isla de Guernesey"},
            {"ID_Pais": "JEY", "Descripci??n": "Isla de Jersey"},
            {"ID_Pais": "IMN", "Descripci??n": "Isla de Man"},
            {"ID_Pais": "CXR", "Descripci??n": "Isla de Navidad"},
            {"ID_Pais": "ISL", "Descripci??n": "Islandia"},
            {"ID_Pais": "CYM", "Descripci??n": "Islas Caim??n"},
            {"ID_Pais": "CCK", "Descripci??n": "Islas Cocos"},
            {"ID_Pais": "COK", "Descripci??n": "Islas Cook"},
            {"ID_Pais": "FLK", "Descripci??n": "Islas Falkland (Malvinas)"},
            {"ID_Pais": "FRO", "Descripci??n": "Islas Fero??"},
            {"ID_Pais": "FJI", "Descripci??n": "Islas Fidji"},
            {"ID_Pais": "SGS", "Descripci??n": "Islas Georgias del Sur y Sandwich"},
            {"ID_Pais": "HMD", "Descripci??n": "Islas Heard e Mcdonald"},
            {"ID_Pais": "MNP", "Descripci??n": "Islas Marianas del Norte"},
            {"ID_Pais": "MHL", "Descripci??n": "Islas Marshall"},
            {"ID_Pais": "UMI", "Descripci??n": "Islas Menores de EEUU"},
            {"ID_Pais": "NFK", "Descripci??n": "Islas Norfolk"},
            {"ID_Pais": "PCN", "Descripci??n": "Islas Pitcairn"},
            {"ID_Pais": "SLB", "Descripci??n": "Islas Salom??n"},
            {"ID_Pais": "TCA", "Descripci??n": "Islas Turcas y Caicos"},
            {"ID_Pais": "VGB", "Descripci??n": "Islas V??rgenes Brit??nicas"},
            {"ID_Pais": "VIR", "Descripci??n": "Islas V??rgenes de los EEUU"},
            {"ID_Pais": "WLF", "Descripci??n": "Islas Wallis y Futura"},
            {"ID_Pais": "ALA", "Descripci??n": "Islas ??land"},
            {"ID_Pais": "ISR", "Descripci??n": "Israel"},
            {"ID_Pais": "ITA", "Descripci??n": "Italia"},
            {"ID_Pais": "JAM", "Descripci??n": "Jamaica"},
            {"ID_Pais": "JPN", "Descripci??n": "Jap??n"},
            {"ID_Pais": "JOR", "Descripci??n": "Jordania"},
            {"ID_Pais": "KAZ", "Descripci??n": "Kazajst??n"},
            {"ID_Pais": "KEN", "Descripci??n": "Kenia"},
            {"ID_Pais": "KGZ", "Descripci??n": "Kirguist??n"},
            {"ID_Pais": "KIR", "Descripci??n": "Kiribati"},
            {"ID_Pais": "KWT", "Descripci??n": "Kuwait"},
            {"ID_Pais": "LAO", "Descripci??n": "Laos"},
            {"ID_Pais": "LSO", "Descripci??n": "Lesotho"},
            {"ID_Pais": "LVA", "Descripci??n": "Letonia"},
            {"ID_Pais": "LBY", "Descripci??n": "Libia"},
            {"ID_Pais": "LBR", "Descripci??n": "Lib??ria"},
            {"ID_Pais": "LIE", "Descripci??n": "Liechtenstein"},
            {"ID_Pais": "LTU", "Descripci??n": "Lituania"},
            {"ID_Pais": "LUX", "Descripci??n": "Luxemburgo"},
            {"ID_Pais": "LBN", "Descripci??n": "L??bano"},
            {"ID_Pais": "MAC", "Descripci??n": "Macao"},
            {"ID_Pais": "MKD", "Descripci??n": "Macedonia, ARY"},
            {"ID_Pais": "MDG", "Descripci??n": "Madagascar"},
            {"ID_Pais": "MYS", "Descripci??n": "Malasia"},
            {"ID_Pais": "MWI", "Descripci??n": "Malawi"},
            {"ID_Pais": "MDV", "Descripci??n": "Maldivas"},
            {"ID_Pais": "MLT", "Descripci??n": "Malta"},
            {"ID_Pais": "MLI", "Descripci??n": "Mal??"},
            {"ID_Pais": "MAR", "Descripci??n": "Marruecos"},
            {"ID_Pais": "MTQ", "Descripci??n": "Martinica"},
            {"ID_Pais": "MUS", "Descripci??n": "Mauricio"},
            {"ID_Pais": "MRT", "Descripci??n": "Mauritania"},
            {"ID_Pais": "MYT", "Descripci??n": "Mayotte"},
            {"ID_Pais": "FSM", "Descripci??n": "Micronesia"},
            {"ID_Pais": "MDA", "Descripci??n": "Moldavia"},
            {"ID_Pais": "MNG", "Descripci??n": "Mongolia"},
            {"ID_Pais": "MNE", "Descripci??n": "Montenegro"},
            {"ID_Pais": "MSR", "Descripci??n": "Montserrat"},
            {"ID_Pais": "MOZ", "Descripci??n": "Mozambique"},
            {"ID_Pais": "MMR", "Descripci??n": "Myanmar"},
            {"ID_Pais": "MEX", "Descripci??n": "M??xico"},
            {"ID_Pais": "MCO", "Descripci??n": "M??naco"},
            {"ID_Pais": "NAM", "Descripci??n": "Namibia"},
            {"ID_Pais": "NRU", "Descripci??n": "Naur??"},
            {"ID_Pais": "NPL", "Descripci??n": "Nepal"},
            {"ID_Pais": "NIC", "Descripci??n": "Nicaragua"},
            {"ID_Pais": "NGA", "Descripci??n": "Nigeria"},
            {"ID_Pais": "NIU", "Descripci??n": "Niue"},
            {"ID_Pais": "NOR", "Descripci??n": "Noruega"},
            {"ID_Pais": "NCL", "Descripci??n": "Nueva Caledonia"},
            {"ID_Pais": "NZL", "Descripci??n": "Nueva Zelanda"},
            {"ID_Pais": "NER", "Descripci??n": "N??ger"},
            {"ID_Pais": "OMN", "Descripci??n": "Om??n"},
            {"ID_Pais": "PAK", "Descripci??n": "Pakist??n"},
            {"ID_Pais": "PLW", "Descripci??n": "Palau"},
            {"ID_Pais": "PSE", "Descripci??n": "Palestina, Territorio ocupado"},
            {"ID_Pais": "PAN", "Descripci??n": "Panam??"},
            {"ID_Pais": "PNG", "Descripci??n": "Papua Nueva Guinea"},
            {"ID_Pais": "PRY", "Descripci??n": "Paraguay"},
            {"ID_Pais": "NLD", "Descripci??n": "Pa??ses Bajos"},
            {"ID_Pais": "PER", "Descripci??n": "Per??"},
            {"ID_Pais": "PYF", "Descripci??n": "Polinesia Francesa"},
            {"ID_Pais": "POL", "Descripci??n": "Polonia"},
            {"ID_Pais": "PRT", "Descripci??n": "Portugal"},
            {"ID_Pais": "PRI", "Descripci??n": "Puerto Rico"},
            {"ID_Pais": "QAT", "Descripci??n": "Qatar"},
            {"ID_Pais": "GBR", "Descripci??n": "Reino Unido"},
            {"ID_Pais": "CAF", "Descripci??n": "Rep??blica Centroafricana"},
            {"ID_Pais": "CZE", "Descripci??n": "Rep??blica Checa"},
            {"ID_Pais": "DOM", "Descripci??n": "Rep??blica Dominicana"},
            {"ID_Pais": "REU", "Descripci??n": "Reuni??n"},
            {"ID_Pais": "ROU", "Descripci??n": "Rumania"},
            {"ID_Pais": "RUS", "Descripci??n": "Rusia"},
            {"ID_Pais": "RWA", "Descripci??n": "Rwanda"},
            {"ID_Pais": "ESH", "Descripci??n": "Sahara Occidental"},
            {"ID_Pais": "KNA", "Descripci??n": "Saint Kitts y Nevis"},
            {"ID_Pais": "WSM", "Descripci??n": "Samoa"},
            {"ID_Pais": "ASM", "Descripci??n": "Samoa Americana"},
            {"ID_Pais": "BLM", "Descripci??n": "San Bartolom??"},
            {"ID_Pais": "SMR", "Descripci??n": "San Marino"},
            {"ID_Pais": "MAF", "Descripci??n": "San Mart??n"},
            {"ID_Pais": "SPM", "Descripci??n": "San Pedro y Miquel??n"},
            {"ID_Pais": "VCT", "Descripci??n": "San Vicente y las Granadinas"},
            {"ID_Pais": "SHN", "Descripci??n": "Santa Elena"},
            {"ID_Pais": "LCA", "Descripci??n": "Santa Luc??a"},
            {"ID_Pais": "STP", "Descripci??n": "Santo Tom?? y Pr??ncipe"},
            {"ID_Pais": "SEN", "Descripci??n": "Senegal"},
            {"ID_Pais": "SRB", "Descripci??n": "Serbia"},
            {"ID_Pais": "SYC", "Descripci??n": "Seychelles"},
            {"ID_Pais": "SLE", "Descripci??n": "Sierra Leona"},
            {"ID_Pais": "SGP", "Descripci??n": "Singapur"},
            {"ID_Pais": "SYR", "Descripci??n": "Siria"},
            {"ID_Pais": "SOM", "Descripci??n": "Somalia"},
            {"ID_Pais": "LKA", "Descripci??n": "Sri Lanka"},
            {"ID_Pais": "SWZ", "Descripci??n": "Suazilandia"},
            {"ID_Pais": "ZAF", "Descripci??n": "Sud??frica"},
            {"ID_Pais": "SDN", "Descripci??n": "Sud??n"},
            {"ID_Pais": "SWE", "Descripci??n": "Suecia"},
            {"ID_Pais": "CHE", "Descripci??n": "Suiza"},
            {"ID_Pais": "SUR", "Descripci??n": "Suriname"},
            {"ID_Pais": "SJM", "Descripci??n": "Svalbard e Islas de Jan Mayen"},
            {"ID_Pais": "THA", "Descripci??n": "Tailandia"},
            {"ID_Pais": "TWN", "Descripci??n": "Taiw??n"},
            {"ID_Pais": "TZA", "Descripci??n": "Tanzania"},
            {"ID_Pais": "TJK", "Descripci??n": "Tayikistan"},
            {"ID_Pais": "IOT", "Descripci??n": "Terr. Brit??nico del Oc. Indico"},
            {"ID_Pais": "ATF", "Descripci??n": "Tierras Australes Francesas"},
            {"ID_Pais": "TLS", "Descripci??n": "Timor Oriental"},
            {"ID_Pais": "TGO", "Descripci??n": "Togo"},
            {"ID_Pais": "TKL", "Descripci??n": "Tokelau"},
            {"ID_Pais": "TON", "Descripci??n": "Tonga"},
            {"ID_Pais": "TTO", "Descripci??n": "Trinidad y Tobago"},
            {"ID_Pais": "TKM", "Descripci??n": "Turkmenist??n"},
            {"ID_Pais": "TUR", "Descripci??n": "Turqu??a"},
            {"ID_Pais": "TUV", "Descripci??n": "Tuvalu"},
            {"ID_Pais": "TUN", "Descripci??n": "T??nez"},
            {"ID_Pais": "UKR", "Descripci??n": "Ucrania"},
            {"ID_Pais": "UGA", "Descripci??n": "Uganda"},
            {"ID_Pais": "URY", "Descripci??n": "Uruguay"},
            {"ID_Pais": "UZB", "Descripci??n": "Uzbekist??n"},
            {"ID_Pais": "VUT", "Descripci??n": "Vanuatu"},
            {"ID_Pais": "VAT", "Descripci??n": "Vaticano, Santa Sede"},
            {"ID_Pais": "VEN", "Descripci??n": "Venezuela"},
            {"ID_Pais": "VNM", "Descripci??n": "Vietnam"},
            {"ID_Pais": "YEM", "Descripci??n": "Yemen"},
            {"ID_Pais": "DJI", "Descripci??n": "Yibuti"},
            {"ID_Pais": "ZMB", "Descripci??n": "Zambia"},
            {"ID_Pais": "ZWE", "Descripci??n": "Zimbabwe"},
            {"ID_Pais": "KOS", "Descripci??n": "Kosovo"},
            {"ID_Pais": "ES111", "Descripci??n": "A Coru??a"},
            {"ID_Pais": "ES112", "Descripci??n": "Lugo"},
            {"ID_Pais": "ES113", "Descripci??n": "Ourense"},
            {"ID_Pais": "ES114", "Descripci??n": "Pontevedra"},
            {"ID_Pais": "ES120", "Descripci??n": "Asturias"},
            {"ID_Pais": "ES130", "Descripci??n": "Cantabria"},
            {"ID_Pais": "ES211", "Descripci??n": "Araba/??lava"},
            {"ID_Pais": "ES212", "Descripci??n": "Gipuzkoa"},
            {"ID_Pais": "ES213", "Descripci??n": "Bizkaia"},
            {"ID_Pais": "ES220", "Descripci??n": "Navarra"},
            {"ID_Pais": "ES230", "Descripci??n": "La Rioja"},
            {"ID_Pais": "ES241", "Descripci??n": "Huesca"},
            {"ID_Pais": "ES242", "Descripci??n": "Teruel"},
            {"ID_Pais": "ES243", "Descripci??n": "Zaragoza"},
            {"ID_Pais": "ES300", "Descripci??n": "Madrid"},
            {"ID_Pais": "ES411", "Descripci??n": "??vila"},
            {"ID_Pais": "ES412", "Descripci??n": "Burgos"},
            {"ID_Pais": "ES413", "Descripci??n": "Le??n"},
            {"ID_Pais": "ES414", "Descripci??n": "Palencia"},
            {"ID_Pais": "ES415", "Descripci??n": "Salamanca"},
            {"ID_Pais": "ES416", "Descripci??n": "Segovia"},
            {"ID_Pais": "ES417", "Descripci??n": "Soria"},
            {"ID_Pais": "ES418", "Descripci??n": "Valladolid"},
            {"ID_Pais": "ES419", "Descripci??n": "Zamora"},
            {"ID_Pais": "ES421", "Descripci??n": "Albacete"},
            {"ID_Pais": "ES422", "Descripci??n": "Ciudad Real"},
            {"ID_Pais": "ES423", "Descripci??n": "Cuenca"},
            {"ID_Pais": "ES424", "Descripci??n": "Guadalajara"},
            {"ID_Pais": "ES425", "Descripci??n": "Toledo"},
            {"ID_Pais": "ES431", "Descripci??n": "Badajoz"},
            {"ID_Pais": "ES432", "Descripci??n": "C??ceres"},
            {"ID_Pais": "ES511", "Descripci??n": "Barcelona"},
            {"ID_Pais": "ES512", "Descripci??n": "Girona"},
            {"ID_Pais": "ES513", "Descripci??n": "Lleida"},
            {"ID_Pais": "ES514", "Descripci??n": "Tarragona"},
            {"ID_Pais": "ES521", "Descripci??n": "Alicante / Alacant"},
            {"ID_Pais": "ES522", "Descripci??n": "Castell??n / Castell??"},
            {"ID_Pais": "ES523", "Descripci??n": "Valencia / Val??ncia"},
            {"ID_Pais": "ES530", "Descripci??n": "Illes Balears"},
            {"ID_Pais": "ES531", "Descripci??n": "Eivissa y Formentera"},
            {"ID_Pais": "ES532", "Descripci??n": "Mallorca"},
            {"ID_Pais": "ES533", "Descripci??n": "Menorca"},
            {"ID_Pais": "ES611", "Descripci??n": "Almer??a"},
            {"ID_Pais": "ES612", "Descripci??n": "C??diz"},
            {"ID_Pais": "ES613", "Descripci??n": "C??rdoba"},
            {"ID_Pais": "ES614", "Descripci??n": "Granada"},
            {"ID_Pais": "ES615", "Descripci??n": "Huelva"},
            {"ID_Pais": "ES616", "Descripci??n": "Ja??n"},
            {"ID_Pais": "ES617", "Descripci??n": "M??laga"},
            {"ID_Pais": "ES618", "Descripci??n": "Sevilla"},
            {"ID_Pais": "ES620", "Descripci??n": "Murcia"},
            {"ID_Pais": "ES630", "Descripci??n": "Ceuta"},
            {"ID_Pais": "ES640", "Descripci??n": "Melilla"},
            {"ID_Pais": "ES701", "Descripci??n": "Las Palmas"},
            {"ID_Pais": "ES702", "Descripci??n": "Santa Cruz de Tenerife"},
            {"ID_Pais": "ES703", "Descripci??n": "El Hierro"},
            {"ID_Pais": "ES704", "Descripci??n": "Fuerteventura"},
            {"ID_Pais": "ES705", "Descripci??n": "Gran Canaria"},
            {"ID_Pais": "ES706", "Descripci??n": "La Gomera"},
            {"ID_Pais": "ES707", "Descripci??n": "La Palma"},
            {"ID_Pais": "ES708", "Descripci??n": "Lanzarote"},
            {"ID_Pais": "ES709", "Descripci??n": "Tenerife"},
        ]
        # Diccionario con los nombre de los Paises usando los del INE [4]
        # _logger.info("DataBi: Calculating %s countries", str(len(dic_ine)))
        for prop in hotels:
            for pais in dic_ine:
                dic_pais.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Pais": pais["ID_Pais"],
                        "Descripci??n": pais["Descripci??n"],
                    }
                )
        return dic_pais

    @api.model
    def data_bi_regimen(self, hotels):
        # Diccionario con los Board Services [5]
        dic_regimen = []
        board_services = self.env["pms.board.service"].search_read([])
        # _logger.info("DataBi: Calculating %s board services",
        #   str(len(board_services)))
        for prop in hotels:
            dic_regimen.append(
                {
                    "ID_Hotel": prop.id,
                    "ID_Regimen": 0,
                    "Descripci??n": u"Sin r??gimen",
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
                            "Descripci??n": board_service["name"],
                        }
                    )
        return dic_regimen

    @api.model
    def data_bi_capacidad(self, hotels):
        # Diccionario con las capacidades  [7]
        rooms_type = self.env["pms.room.type"].search([])
        # _logger.info("DataBi: Calculating %s room capacity", str(len(rooms)))
        dic_capacidad = []
        for prop in hotels:
            for room_type in rooms_type:
                room_count = self.data_bi_get_capacidad(prop.id, room_type.id)
                if room_count > 0:
                    dic_capacidad.append(
                        {
                            "ID_Hotel": prop.id,
                            "Hasta_Fecha": (
                                date.today() + timedelta(days=365 * 3)
                            ).strftime("%Y-%m-%d"),
                            "ID_Tipo_Habitacion": room_type.id,
                            "Nro_Habitaciones": room_count,
                        }
                    )
        return dic_capacidad

    @api.model
    def data_bi_habitacione(self, hotels):
        # Diccionario con Rooms types [8]
        rooms = self.env["pms.room.type"].search([])
        # _logger.info("DataBi: Calculating %s room types", str(len(rooms)))
        dic_tipo_habitacion = []
        for prop in hotels:
            for room in rooms:
                if (not room.pms_property_ids) or (
                    prop.id in room.pms_property_ids.ids
                ):
                    dic_tipo_habitacion.append(
                        {
                            "ID_Hotel": prop.id,
                            "ID_Tipo_Habitacion": room["id"],
                            "Descripci??n": room["name"],
                            "Estancias": room.get_capacity(),
                        }
                    )
        return dic_tipo_habitacion

    @api.model
    def data_bi_budget(self, hotels):
        # Diccionario con las previsiones Budget [9]
        budgets = self.env["pms.budget"].search([])
        # _logger.info("DataBi: Calculating %s budget", str(len(budgets)))
        dic_budget = []
        for prop in hotels:
            for budget in budgets:
                if budget.pms_property_id.id == prop.id:
                    dic_budget.append(
                        {
                            "ID_Hotel": prop.id,
                            "Fecha": (str(budget.year) + "-" +
                                      str(budget.month).zfill(2) + "-01"),
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
            # Fecha fecha Primer d??a del mes
            # ID_Tarifa num??rico C??digo de la Tarifa
            # ID_Canal num??rico C??digo del Canal
            # ID_Pais num??rico C??digo del Pa??s
            # ID_Regimen num??rico C??igo del R??gimen
            # ID_Tipo_Habitacion num??rico C??digo del Tipo de Habitaci??n
            # iD_Segmento num??rico C??digo del Segmento
            # ID_Cliente num??rico C??digo del Cliente
            # Pension_Revenue num??rico con dos decimales Ingresos por Pensi??n
        return dic_budget

    @api.model
    def data_bi_moti_bloq(self, hotels):
        # Diccionario con Motivo de Bloqueos [11]
        lineas = self.env["room.closure.reason"].search([])
        dic_moti_bloq = []
        # _logger.info("DataBi: Calculating %s blocking reasons",
        #   str(len(lineas)))
        for prop in hotels:
            dic_moti_bloq.append(
                {
                    "ID_Hotel": prop.id,
                    "ID_Motivo_Bloqueo": "B0",
                    "Descripci??n": u"Ninguno",
                }
            )
            dic_moti_bloq.append(
                {
                    "ID_Hotel": prop.id,
                    "ID_Motivo_Bloqueo": "ST",
                    "Descripci??n": u"Staff",
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
                            "Descripci??n": linea.name,
                        }
                    )
        return dic_moti_bloq

    @api.model
    def data_bi_segment(self, hotels):
        # Diccionario con Segmentaci??n [12]
        dic_segmentos = []
        lineas = self.env["res.partner.category"].search([])
        # _logger.info("DataBi: Calculating %s segmentations", str(len(lineas)))
        for prop in hotels:
            for linea in lineas:
                if linea.parent_id.name:
                    seg_desc = linea.parent_id.name + " / " + linea.name
                else:
                    seg_desc = linea.name
                dic_segmentos.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Segmento": linea.id,
                        "Descripci??n": seg_desc,
                    }
                )
        return dic_segmentos

    @api.model
    def data_bi_client(self, hotels):
        # Diccionario con Clientes (OTAs y agencias) [13]
        dic_clientes = []
        lineas = self.env["res.partner"].search([("is_agency", "=", True)])
        # _logger.info("DataBi: Calculating %s Operators", str(len(lineas)))
        for prop in hotels:
            dic_clientes.append(
                {"ID_Hotel": prop.id, "ID_Cliente": 0, "Descripci??n": u"Ninguno"}
            )
            for linea in lineas:
                dic_clientes.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_Cliente": linea.id,
                        "Descripci??n": linea.data_bi_ref if linea.data_bi_ref else linea.name,
                    }
                )
        return dic_clientes

    @api.model
    def data_bi_estados(self, hotels):
        # Diccionario con los Estados Reserva [14]
        # _logger.info("DataBi: Calculating states of the reserves")
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
        for prop in hotels:
            for i in range(0, len(estado_array)):
                dic_estados.append(
                    {
                        "ID_Hotel": prop.id,
                        "ID_EstadoReserva": str(i),
                        "Descripci??n": estado_array_txt[i],
                    }
                )
        return dic_estados

    @api.model
    def data_bi_rooms(self, hotels, filtro=False):
        # Diccionario con las habitaciones [15]
        dic_rooms = []
        rooms = self.env["pms.room"].search([])
        # _logger.info("DataBi: Calculating %s name rooms.", str(len(rooms)))
        for prop in hotels:
            if filtro:
                r = rooms.filtered(lambda n: (n.pms_property_id.id == prop.id))
            else:
                r = rooms
            for room in r:
                dic_rooms.append(
                    {
                        "ID_Hotel": room.pms_property_id.id,
                        "ID_Room": room.id,
                        "Descripci??n": room.name,
                    }
                )
        return dic_rooms

    @api.model
    def data_bi_bloqueos(self, hotels, lines):
        # Diccionario con Bloqueos [10]
        dic_bloqueos = []
        lines = lines.filtered(
            lambda n: ((n.reservation_id.reservation_type != "normal")
                       and (n.reservation_id.state != "cancelled"))
        )
        # _logger.info("DataBi: Calculating %s Bloqued", str(len(lines)))
        for line in lines:

            if line.pms_property_id.id in hotels.ids:
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
    def data_bi_reservas(self, hotels, lines, estado_array):
        # Diccionario con Reservas  [6]
        dic_reservas = []

        for prop in hotels:
            lineas = lines.filtered(
                lambda n: ((n.pms_property_id.id == prop.id)
                           and (n.reservation_id.reservation_type == "normal"))
                # and (n.price > 0)
            )
            # _logger.info(
            #     "DataBi: Calculating %s reservations in %s ",
            #     str(len(lineas)),
            #     prop.name,
            # )

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
                cliente = canal if cliente == 0 else cliente

                precio_comision = round(
                    linea.reservation_id.commission_amount
                    / len(linea.reservation_id.reservation_line_ids),
                    2,
                )
                precio_iva = round(
                    (linea.reservation_id.tax_ids.amount * linea.price / 100), 2
                )

                dic_reservas.append(
                    {
                        "ID_Reserva": linea.reservation_id.id,
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
                        "PrecioDiario": linea.price - precio_comision - precio_iva,
                        "PrecioDto": linea.discount * (linea.price / 100),
                        "PrecioComision": precio_comision,
                        "PrecioIva": precio_iva,
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

                # ID_Reserva num??rico C??digo ??nico de la reserva
                # ID_Hotel num??rico C??digo del Hotel
                # ID_EstadoReserva num??rico C??digo del estado de la reserva
                # FechaVenta fecha Fecha de la venta de la reserva
                # ID_Segmento num??rico C??digo del Segmento de la reserva
                # ID_Cliente Num??rico C??digo del Cliente de la reserva
                # ID_Canal num??rico C??digo del Canal
                # FechaExtraccion fecha Fecha de la extracci??n de los datos (Foto)
                # Entrada fecha Fecha de entrada
                # Salida fecha Fecha de salida
                # Noches num??rico Nro. de noches de la reserva
                # ID_TipoHabitacion num??rico C??digo del Tipo de Habitaci??n
                # ID_Regimen num??rico C??digo del Tipo de R??gimen
                # Adultos num??rico Nro. de adultos
                # Menores num??rico Nro. de menores
                # Cunas num??rico Nro. de cunas
                # PrecioDiario num??rico con 2 decimales Precio por noche de la reserva
                # ID_Tarifa num??rico C??digo de la tarifa aplicada a la reserva
                # ID_Pais alfanum??rico C??digo del pa??s

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

    @api.model
    def data_bi_get_capacidad(self, property, rtype):
        rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", property), ("room_type_id", "=", rtype)]
        )
        return len(rooms)
