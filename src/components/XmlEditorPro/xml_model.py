import xml.etree.ElementTree as ET
from xml.dom import minidom


def parse_xml_text(xml_text: str) -> ET.Element:
    xml_text = (xml_text or "").strip()
    if not xml_text:
        raise ValueError("XML 内容为空")
    return ET.fromstring(xml_text)


def format_xml(element: ET.Element, indent: str = "  ") -> str:
    rough = ET.tostring(element, encoding="unicode")
    reparsed = minidom.parseString(rough)
    formatted = reparsed.toprettyxml(indent=indent)
    lines = [line for line in formatted.split("\n") if line.strip()]
    if lines:
        if lines[0].startswith("<?xml"):
            lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
        else:
            lines.insert(0, '<?xml version="1.0" encoding="UTF-8"?>')
    return "\n".join(lines)


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

