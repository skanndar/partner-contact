# Copyright 2026 Alex Abbas Deselaers (Skanndar)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common

# Real rows from http://download.geonames.org/export/zip/ES.zip (2026-10-16),
# official 12-column format; col 7 = admin_name3 (municipality), col 8 = INE.
MOLINS = [
    [
        "ES",
        "08750",
        "Santa Creu D'Olorda",
        "Cataluna",
        "CT",
        "Barcelona",
        "B",
        "Molins de Rei",
        "08123",
        "41.4167",
        "2.025",
        "3",
    ],
    [
        "ES",
        "08750",
        "Vallpineda",
        "Cataluna",
        "CT",
        "Barcelona",
        "B",
        "Molins de Rei",
        "08123",
        "41.4423",
        "2.0553",
        "3",
    ],
    [
        "ES",
        "08750",
        "Sant Bartomeu De La Quadra",
        "Cataluna",
        "CT",
        "Barcelona",
        "B",
        "Molins de Rei",
        "08123",
        "41.4167",
        "2.0333",
        "4",
    ],
    [
        "ES",
        "08750",
        "Molins De Rei",
        "Cataluna",
        "CT",
        "Barcelona",
        "B",
        "Molins de Rei",
        "08123",
        "41.4167",
        "2.0167",
        "4",
    ],
]
ALMERIA = [
    # Capital row (admin3 with accent) + PO-box pseudo-place row (no admin3):
    # both share place_name 'Almeria' in the same province.
    [
        "ES",
        "04001",
        "Almeria",
        "Andalucia",
        "AN",
        "Almería",
        "AL",
        "Almería",
        "04013",
        "36.8381",
        "-2.4597",
        "4",
    ],
    [
        "ES",
        "04070",
        "Almeria",
        "Andalucia",
        "AN",
        "Almería",
        "AL",
        "",
        "",
        "36.8381",
        "-2.4597",
        "4",
    ],
]
ARTICLES = [
    [
        "ES",
        "04280",
        "Los Gallardos",
        "Andalucia",
        "AN",
        "Almería",
        "AL",
        "Gallardos, Los",
        "04048",
        "37.1684",
        "-1.9404",
        "1",
    ],
    [
        "ES",
        "04700",
        "El Ejido",
        "Andalucia",
        "AN",
        "Almería",
        "AL",
        "Ejido, El",
        "04902",
        "36.7729",
        "-2.8135",
        "1",
    ],
    [
        "ES",
        "04700",
        "Santo Domingo",
        "Andalucia",
        "AN",
        "Almería",
        "AL",
        "Ejido, El",
        "04902",
        "36.8254",
        "-2.8537",
        "1",
    ],
    [
        "ES",
        "12110",
        "Alcora, L'",
        "Comunidad Valenciana",
        "VC",
        "Castellón",
        "CS",
        "Alcora, l'",
        "12005",
        "40.0667",
        "-0.2",
        "4",
    ],
]
SEVILLA = [
    # The admin3 of the Sevilla municipality is the English exonym 'Seville'
    # in the Geonames source: corrected by GEONAMES_ADMIN3_OVERRIDES.
    [
        "ES",
        "41001",
        "Sevilla",
        "Andalucia",
        "AN",
        "Sevilla",
        "SE",
        "Seville",
        "41091",
        "37.3885",
        "-5.9977",
        "4",
    ],
    [
        "ES",
        "41500",
        "Torrequinto (Urbanizacion)",
        "Andalucia",
        "AN",
        "Sevilla",
        "SE",
        "Seville",
        "41091",
        "37.3379",
        "-5.8395",
        "3",
    ],
]


class TestGeonamesImportMunicipality(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env.ref("base.es")
        cls.wizard = cls.env["city.zip.geonames.import"].create(
            {"country_ids": [(6, 0, [cls.country.id])]}
        )
        cls.wizard_plain = cls.env["city.zip.geonames.import"].create(
            {
                "country_ids": [(6, 0, [cls.country.id])],
                "use_admin3_in_city_name": False,
            }
        )

    def _cities(self):
        return self.env["res.city"].search([("country_id", "=", self.country.id)])

    def _zips(self):
        return self.env["res.city.zip"].search(
            [("city_id.country_id", "=", self.country.id)]
        )

    def test_default_option_enabled(self):
        self.assertTrue(self.wizard.use_admin3_in_city_name)

    def test_compose_municipality_first(self):
        self.wizard._process_csv(MOLINS, self.country)
        names = set(self._cities().mapped("name"))
        self.assertEqual(
            names,
            {
                "Molins de Rei",
                "Molins de Rei (Vallpineda)",
                "Molins de Rei (Santa Creu D'Olorda)",
                "Molins de Rei (Sant Bartomeu De La Quadra)",
            },
        )
        zips = self._zips()
        self.assertEqual(len(zips), 4)
        self.assertEqual(set(zips.mapped("name")), {"08750"})

    def test_reimport_is_idempotent(self):
        self.wizard._process_csv(MOLINS, self.country)
        city_ids = set(self._cities().ids)
        zip_ids = set(self._zips().ids)
        self.wizard._process_csv(MOLINS, self.country)
        self.assertEqual(set(self._cities().ids), city_ids)
        self.assertEqual(set(self._zips().ids), zip_ids)

    def test_rename_in_place_preserves_partner_links(self):
        # Prod-like state: a previous import without the option (plain names).
        self.wizard_plain._process_csv(MOLINS, self.country)
        city = self._cities().filtered(lambda c: c.name == "Vallpineda")
        self.assertEqual(len(city), 1)
        zip_rec = self._zips().filtered(lambda z: z.city_id == city)
        partner = self.env["res.partner"].create(
            {"name": "Vecina de Vallpineda", "zip_id": zip_rec.id}
        )
        self.wizard._process_csv(MOLINS, self.country)
        self.assertTrue(city.exists())
        self.assertEqual(city.name, "Molins de Rei (Vallpineda)")
        self.assertTrue(zip_rec.exists())
        self.assertEqual(partner.zip_id, zip_rec)
        self.assertEqual(partner.city_id, city)
        # No duplicates were created.
        self.assertEqual(len(self._cities()), 4)
        self.assertEqual(len(self._zips()), 4)

    def test_manual_composed_rename_is_matched(self):
        # Prod-like state where a city was already renamed by hand.
        self.wizard_plain._process_csv(MOLINS, self.country)
        city = self._cities().filtered(lambda c: c.name == "Vallpineda")
        city.name = "Molins de Rei (Vallpineda)"
        zip_id = self._zips().filtered(lambda z: z.city_id == city).id
        self.wizard._process_csv(MOLINS, self.country)
        self.assertTrue(city.exists())
        self.assertEqual(len(self._cities()), 4)
        zips = self._zips()
        self.assertEqual(len(zips), 4)
        self.assertIn(zip_id, zips.ids)

    def test_empty_admin3_shares_place_name(self):
        # 'Almeria' capital (admin3 'Almería') and 'Almeria' PO boxes (no
        # admin3) coexist: no KeyError and each zip on its own city.
        self.wizard._process_csv(ALMERIA, self.country)
        names = set(self._cities().mapped("name"))
        self.assertEqual(names, {"Almería", "Almeria"})
        for zip_name, city_name in (("04001", "Almería"), ("04070", "Almeria")):
            zip_rec = self._zips().filtered(lambda z, n=zip_name: z.name == n)
            self.assertEqual(zip_rec.city_id.name, city_name)

    def test_article_inversion(self):
        self.wizard._process_csv(ARTICLES, self.country)
        names = set(self._cities().mapped("name"))
        self.assertEqual(
            names,
            {"Los Gallardos", "El Ejido", "El Ejido (Santo Domingo)", "l'Alcora"},
        )

    def test_exonym_is_corrected(self):
        # Known Geonames data wart: admin3 of Sevilla is the English exonym
        # 'Seville'; the per-country overrides map fixes it on the fly.
        self.wizard._process_csv(SEVILLA, self.country)
        self.assertEqual(
            set(self._cities().mapped("name")),
            {"Sevilla", "Sevilla (Torrequinto (Urbanizacion))"},
        )

    def test_letter_case_applies_to_both_parts(self):
        self.wizard.letter_case = "upper"
        self.wizard._process_csv(MOLINS[1:2], self.country)
        self.assertEqual(self._cities().mapped("name"), ["MOLINS DE REI (VALLPINEDA)"])

    def test_option_off_keeps_upstream_behavior(self):
        self.wizard_plain._process_csv(MOLINS, self.country)
        names = set(self._cities().mapped("name"))
        self.assertEqual(
            names,
            {
                "Molins De Rei",
                "Vallpineda",
                "Santa Creu D'Olorda",
                "Sant Bartomeu De La Quadra",
            },
        )

    def test_short_rows_fall_back_to_plain(self):
        # Rows outside the official 12-column format never compose (e.g. the
        # truncated fixtures used by the upstream test suite).
        rows = [row[:10] for row in MOLINS]
        self.wizard._process_csv(rows, self.country)
        self.assertIn("Vallpineda", self._cities().mapped("name"))
