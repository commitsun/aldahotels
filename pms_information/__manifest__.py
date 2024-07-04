# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'PMS Property Information',
    'version': '14.0.1.0.0',
    'category': 'PMS',
    "summary": """ Information related of property """,
    "author": "Irlui Ramirez,José Luis Algara,Odoo Community Association (OCA)",
    "depends": ["base", "pms", "pms_data_bi"],
    'data': [
        'views/pms_property_information_views.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}