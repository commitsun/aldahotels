# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Alda import salaries",
    "version": "14.0.1.0.0",
    "summary": "Wizard to import salaries from alda's file",
    "category": "",
    "author": "Comunitea",
    "maintainer": "Comunitea",
    "website": "https://github.com/OCA/aldahotels",
    "license": "AGPL-3",
    "depends": ["pms", "l10n_es_aeat"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/alda_import_salaries_wzd_view.xml",
    ],
    "external_dependencies": {"python": ["xlrd"]},
}
