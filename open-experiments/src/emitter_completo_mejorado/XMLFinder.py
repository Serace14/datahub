from typing import List, Optional, Any
from lxml import etree
from datahub.specific.dataset import DatasetPatchBuilder

class XMLFinder:
    def __init__(self, tree: etree._Element, ns: dict):
        self.tree = tree
        self.ns = ns

    def find_first_text(self, xpaths: List[str]) -> Optional[str]:
        for xp in xpaths:
            el = self.tree.find(xp, namespaces=self.ns)
            if el is not None and el.text:
                value = el.text.strip()
                if value:
                    return value
        return None

    def find_all_texts(self, xpath: str) -> List[str]:
        values = []
        for el in self.tree.findall(xpath, namespaces=self.ns):
            if el is not None and el.text:
                values.append(el.text.strip())
        return values

