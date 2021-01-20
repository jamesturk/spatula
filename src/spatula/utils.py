import pprint
from lxml.etree import _Element


def _display_element(obj: _Element) -> str:
    elem_str = f"<{obj.tag} "

    if id_str := obj.get("id"):
        elem_str += f"id='{id_str}'"
    elif class_str := obj.get("class"):
        elem_str += f"class='{class_str}'"
    else:
        elem_str += " ".join(f"{k}='{v}'" for k, v in obj.attrib.items())

    return elem_str + f"> @ line {obj.sourceline}"


def _display(obj) -> str:
    if isinstance(obj, dict):
        return pprint.pformat(obj)
    elif hasattr(obj, "to_dict"):
        return pprint.pformat(obj.to_dict())
    elif isinstance(obj, _Element):
        return _display_element(obj)
    else:
        return repr(obj)
