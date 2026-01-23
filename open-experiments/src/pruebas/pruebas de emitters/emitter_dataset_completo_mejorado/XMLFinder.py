from typing import Any, Dict, List, Optional, Union
from lxml import etree


class PropertyExtractor:
    def __init__(self, tree: etree._Element, ns: dict):
        self.tree = tree
        self.ns = ns

    def _extract_values(self, xpaths: List[str], as_list: bool = False) -> Union[str, List[str], None]:
        """
        Recorre varios xpaths y devuelve el primer valor encontrado
        o todos si as_list=True.
        """
        results = []

        for xp in xpaths:
            # ¿Es un atributo? (contiene '@')
            if "@" in xp:
                els = self.tree.xpath(xp, namespaces=self.ns)
                if els:
                    if as_list:
                        results.extend([str(el).strip() for el in els if str(el).strip()])
                    else:
                        return str(els[0]).strip()
            else:
                # Elemento normal
                for el in self.tree.findall(xp, namespaces=self.ns):
                    if el is not None and el.text:
                        text = el.text.strip()
                        if text:
                            if as_list:
                                results.append(text)
                            else:
                                return text

        if as_list:
            return results
        return None

    def extract_property(self, prop_config: Dict[str, Any]) -> Union[str, List[str], None]:
        """
        Extrae un valor de propiedad a partir de la configuración.
        Adapta el modo de extracción según el tipo de propiedad.
        """
        xpaths = prop_config.get("xpaths", [])
        prop_type = prop_config.get("type")

        # Algunos tipos se esperan como listas (ej: tags, rights, urls)
        if prop_type in ["tags", "ownership", "structuredPropertyList"]:
            return self._extract_values(xpaths, as_list=True)

        # Otros como string simple
        return self._extract_values(xpaths, as_list=False)
