import pprint
import typing
import dataclasses
from lxml.etree import _Element  # type: ignore

# utilities for working with optional dependencies
try:
    from attr import has as attr_has
    from attr import fields as attr_fields
    from attr import asdict as attr_asdict
except ImportError:  # pragma: no cover
    attr_has = lambda x: False  # type: ignore # noqa
    attr_fields = lambda x: []  # type: ignore # noqa
    attr_asdict = lambda x: {}  # type: ignore # noqa


def _display_element(obj: _Element) -> str:
    elem_str = f"<{obj.tag} "

    # := if we drop 3.7
    id_str = obj.get("id")
    class_str = obj.get("class")

    if id_str:
        elem_str += f"id='{id_str}'"
    elif class_str:
        elem_str += f"class='{class_str}'"
    else:
        elem_str += " ".join(f"{k}='{v}'" for k, v in obj.attrib.items())

    return f"{elem_str.strip()}> @ line {obj.sourceline}"


def _is_pydantic(obj: typing.Any) -> bool:
    return hasattr(obj, "__fields__") and hasattr(obj, "dict")


def _display(obj: typing.Any) -> str:
    if isinstance(obj, _Element):
        return _display_element(obj)
    else:
        # if there's a dict representation, use that, otherwise str
        try:
            return pprint.pformat(_obj_to_dict(obj))
        except ValueError:
            return str(obj)


def _obj_to_dict(obj: typing.Any) -> typing.Optional[typing.Dict]:
    if obj is None or isinstance(obj, dict):
        return obj
    elif dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    elif attr_has(obj):
        return attr_asdict(obj)
    elif _is_pydantic(obj):
        return obj.dict()
    else:
        raise ValueError(f"invalid type: {obj} ({type(obj)})")
