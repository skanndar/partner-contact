To use this module:

1.  Go to *Contacts > Configuration > Import from Geonames* (or *Settings >
    Technical > Import from Geonames*).
2.  Select one or more countries.
3.  Keep the option **Name cities as 'Municipality (Place)'** enabled (it is on
    by default).
4.  Run the import.

Resulting city names:

- When the place differs from its municipality, the city is named
  `Municipality (Place)`, e.g. `Molins de Rei (Vallpineda)`.
- When the place equals its municipality (ignoring case, accents, punctuation
  and the position of the leading article, so that `Ejido, El` matches
  `El Ejido` and `Almeria` matches `Almería`), the municipality spelling is
  used, e.g. `Molins de Rei`.
- Rows with no `admin_name3`, and countries where Geonames provides none, are
  imported exactly as without this module.
- The wizard's *Letter Case* option is applied to both parts.

On re-import, cities that already exist with a plain name are **renamed in
place** (the `res.city` and `res.city.zip` records keep their ids) instead of
being deleted and recreated, so that the `zip_id` of partners pointing at them
is never lost.
