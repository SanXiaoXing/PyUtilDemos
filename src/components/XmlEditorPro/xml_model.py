import xml.etree.ElementTree as ET
from typing import List


def parse_xml_text(xml_text: str) -> ET.Element:
    xml_text = (xml_text or "").strip()
    if not xml_text:
        raise ValueError("XML 内容为空")
    return ET.fromstring(xml_text)


def format_xml(element: ET.Element, indent: str = "  ") -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    _format_element(element, lines, "", indent)
    return "\n".join(lines)


def _format_element(element: ET.Element, lines: List[str], prefix: str, indent: str) -> None:
    tag = element.tag
    attrs = _format_attrs(element.attrib)
    children = list(element)

    text = (element.text or "").strip()
    tail = (element.tail or "").strip()

    has_children = len(children) > 0
    has_text = bool(text)

    if not has_children and not has_text:
        line = f"{prefix}<{tag}{attrs} />"
        lines.append(line)
    else:
        line = f"{prefix}<{tag}{attrs}>"
        lines.append(line)

        if has_text:
            lines.append(f"{prefix}{indent}{_escape_text(text)}")

        for child in children:
            _format_element(child, lines, prefix + indent, indent)

        lines.append(f"{prefix}</{tag}>")

    if tail:
        lines[-1] = lines[-1] + tail


def _format_attrs(attrib: dict) -> str:
    if not attrib:
        return ""
    parts = []
    for k, v in attrib.items():
        v = v or ""
        if '"' in v and "'" not in v:
            parts.append(f'{k}=\'{v}\'')
        else:
            parts.append(f'{k}="{_escape_attr(v)}"')
    return " " + " ".join(parts)


def _escape_attr(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;")


def _escape_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clone_element(element: ET.Element) -> ET.Element:
    return ET.fromstring(ET.tostring(element, encoding="utf-8"))


def element_label(element: ET.Element) -> str:
    tag = element.tag or ""
    return str(tag)


def element_text_preview(element: ET.Element, limit: int = 28) -> str:
    text = (element.text or "").strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"

