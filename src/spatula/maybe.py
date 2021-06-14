# utilities for working with optional dependencies
try:
    from attr import has as attr_has
    from attr import fields as attr_fields
    from attr import asdict as attr_asdict
except ImportError:  # pragma: no cover
    attr_has = lambda x: False  # type: ignore # noqa
    attr_fields = lambda x: []  # type: ignore # noqa
    attr_asdict = lambda x: {}  # type: ignore # noqa
