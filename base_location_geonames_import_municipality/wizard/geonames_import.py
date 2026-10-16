# Copyright 2026 Alex Abbas Deselaers (Skanndar)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
import re
import unicodedata

from odoo import api, fields, models

logger = logging.getLogger(__name__)

# INE/Geonames style trailing article: "Gallardos, Los" -> "Los Gallardos",
# "Alcora, l'" -> "l'Alcora" (Spanish, Catalan/Valencian, Balearic, Galician).
ARTICLE_RE = re.compile(
    r"^(?P<name>.+), (?P<article>el|la|lo|los|las|l'|els|les|es|sa|ses|so|o|a|os|as)$",
    re.IGNORECASE,
)

# Known bad admin3 values in the Geonames source, per country code. The only
# clear one in the whole ES file (2026-10-16) is the English exonym of the
# Sevilla municipality; it is worth fixing at geonames.org too.
GEONAMES_ADMIN3_OVERRIDES = {
    "ES": {"Seville": "Sevilla"},
}


class CityZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

    use_admin3_in_city_name = fields.Boolean(
        string="Name cities as 'Municipality (Place)'",
        default=True,
        help="Geonames postal rows are flat places (hamlets, districts...). "
        "With this option the city takes the municipality (the admin_name3 "
        "column) first, keeping the place in parentheses when it differs: "
        "'Molins de Rei (Vallpineda)'. Existing cities are renamed in place "
        "so partner ZIP links are preserved. Countries without admin3 data "
        "are not affected.",
    )

    @api.model
    def _geonames_admin3_overrides(self, country):
        """Per-country corrections for bad admin3 source values."""
        return GEONAMES_ADMIN3_OVERRIDES.get(country.code, {})

    @api.model
    def _geonames_invert_article(self, name):
        name = name.strip()
        match = ARTICLE_RE.match(name)
        if not match:
            return name
        article = match.group("article")
        sep = "" if article.endswith("'") else " "
        return f"{article}{sep}{match.group('name')}"

    @api.model
    def _geonames_normalize(self, name):
        # Article position, diacritics, case and punctuation/spacing don't
        # make two names a different place ("Ejido, El" == "El Ejido",
        # "Almeria" == "Almería", "Velez-Malaga" == "Velez Malaga").
        name = unicodedata.normalize("NFKD", self._geonames_invert_article(name))
        return "".join(c for c in name.casefold() if c.isalnum())

    @api.model
    def _compose_city_name(self, row, country):
        """City name for a Geonames row: 'Municipality (Place)'.

        Falls back to the plain place name when the row is not in the official
        12-column format or has no admin_name3.
        """
        place = self.transform_city_name(row[2], country)
        if len(row) < 12:
            return place
        municipality = (row[7] or "").strip()
        if not municipality:
            return place
        overrides = self._geonames_admin3_overrides(country)
        municipality = overrides.get(municipality, municipality)
        municipality = self.transform_city_name(
            self._geonames_invert_article(municipality), country
        )
        if self._geonames_normalize(municipality) == self._geonames_normalize(place):
            # Same place: keep the admin3 spelling, which carries the official
            # case and accents ("Molins De Rei" -> "Molins de Rei").
            return municipality
        return f"{municipality} ({place})"

    @api.model
    def _city_name(self, row, country):
        if not self.use_admin3_in_city_name:
            return super()._city_name(row, country)
        return self._compose_city_name(row, country)

    def _create_cities(
        self, parsed_csv, search_cities, max_import, state_dict, country
    ):
        # Rename existing plain-named cities in place *before* the base method
        # looks them up. Deleting and recreating a renamed city would cascade
        # to its res.city.zip rows and silently NULL the zip_id of every
        # partner pointing at them; renaming keeps res.city/res.city.zip ids.
        if self.use_admin3_in_city_name and search_cities:
            self._rename_cities_to_municipality(
                parsed_csv, state_dict, max_import, country
            )
        return super()._create_cities(
            parsed_csv, search_cities, max_import, state_dict, country
        )

    def _rename_cities_to_municipality(
        self, parsed_csv, state_dict, max_import, country
    ):
        cities = self.env["res.city"].search([("country_id", "=", country.id)])
        if not cities:
            return
        by_key = {(city.name, city.state_id.id): city for city in cities}
        handled = set()
        renamed = 0
        for i, row in enumerate(parsed_csv):
            if max_import and i == max_import:
                break
            plain = self.transform_city_name(row[2], country)
            composed = self._compose_city_name(row, country)
            if composed == plain:
                continue
            state = state_dict[row[country.geonames_state_code_column or 4]]
            key = (plain, state.id)
            if key in handled:
                continue
            handled.add(key)
            if (composed, state.id) in by_key:
                # Already renamed (a previous run or a manual data fix).
                continue
            city = by_key.pop(key, None)
            if city:
                city.name = composed
                by_key[(composed, state.id)] = city
                renamed += 1
        if renamed:
            logger.info(
                "Renamed %d existing cities to 'Municipality (Place)' for %s",
                renamed,
                country.name,
            )
