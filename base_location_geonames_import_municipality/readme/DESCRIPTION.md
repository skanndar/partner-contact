`base_location_geonames_import` names each imported city after the Geonames
`place_name`. Geonames postal rows are flat: hamlets, districts and
urbanisations sit at the same level as the municipality they belong to, so for
many postal codes the imported city ends up being the hamlet instead of the
municipality (e.g. in Spain a partner in Vallpineda gets the city `Vallpineda`
instead of `Molins de Rei`), and that name propagates to the partner address,
invoices and legal documents.

This module adds an option to the Geonames import wizard that names cities
after their **municipality** (the `admin_name3` column of the Geonames file),
keeping the place in parentheses: `Molins de Rei (Vallpineda)`.

It is a pure extension: nothing changes unless the module is installed, and
countries for which Geonames provides no `admin_name3` are left untouched.
