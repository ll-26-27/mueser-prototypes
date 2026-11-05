from .base import Candidate, Resolver  # noqa: F401


def resolvers(names: list[str] | None = None) -> list[Resolver]:
    """Instantiate resolvers in lookup priority order: gov, wikidata, whg, geonames."""
    from .geonames import GeoNamesResolver
    from .gov import GOVResolver
    from .whg import WHGResolver
    from .wikidata import WikidataResolver

    all_ = {"gov": GOVResolver, "wikidata": WikidataResolver, "whg": WHGResolver, "geonames": GeoNamesResolver}
    names = names or list(all_)
    return [all_[n]() for n in names]
