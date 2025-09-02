# emitter_refactor.py
from datahub.metadata._internal_schema_classes import (
    DomainsClass, DomainPropertiesClass, CorpGroupInfoClass,
    OwnershipClass, OwnerClass, OwnershipTypeClass,
    TagAssociationClass, GlobalTagsClass, TagPropertiesClass
)
from owslib.csw import CatalogueServiceWeb
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mce_builder import make_dataset_urn
import datahub.emitter.mce_builder as builder
from datahub.metadata.schema_classes import DatasetPropertiesClass
from datahub.specific.dataset import DatasetPatchBuilder
from datahub.metadata.schema_classes import (
    DataProductPropertiesClass,
    DataProductAssociationClass,
)
from lxml import etree

from propiedades_simples import PROPERTIES_TO_EXTRACT
from XMLFinder import PropertyExtractor
from helpers import *

# === Configuración DataHub ===
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",  # Cambia si tu DataHub está en otra URL
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImJjYzI0YTMwLThiZTUtNGNhMy04MzQ5LTEzYTU0MzJiODE5ZCIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjM0NjA2NTgsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.5S4rfT3P7jdFAutiT5VlqcaOWpyibr7sxc1dD2_7BNw"
)
emitter.test_connection()

# === Conexión al CSW ===
csw = CatalogueServiceWeb("https://www.mapama.gob.es/ide/metadatos/srv/spa/csw")

# === Namespaces para parsear XML ===
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ows": "http://www.opengis.net/ows",
}

start = 0
pagesize = 50  # Número de registros por petición

while True:
    csw.getrecords2(startposition=start + 1, maxrecords=pagesize, esn="full")

    if not csw.records:
        break

    for rec_id, record in csw.records.items():
        dataset_id = record.identifier or f"csw-{rec_id}"
        dataset_urn = make_dataset_urn("geoserver", dataset_id, "PROD")

        # Obtener XML en formato GMD
        csw.getrecordbyid(id=[record.identifier], outputschema="http://www.isotc211.org/2005/gmd")
        xml_raw = csw.response
        if isinstance(xml_raw, str):
            xml_raw = xml_raw.encode("utf-8")
        tree = etree.fromstring(xml_raw)

        # === Finder genérico ===
        finder = PropertyExtractor(tree, ns)

        # === Extraer todas las propiedades declaradas en PROPERTIES_TO_EXTRACT ===
        for config in PROPERTIES_TO_EXTRACT:
            prop_name = config.get("name", "unknown")
            value = finder.extract_property(config)

            if value:
                if config["type"] == "structuredProperty":
                    emit_structured_property(dataset_urn, config["property_urn"], value, emitter)

                elif config["type"] == "ownership":
                    for org in value:
                        org_name = org
                        group_urn = f"urn:li:corpGroup:{org_name.replace(' ', '_')}"
                        create_new_corpgroup(org_name, group_urn, emitter)
                        set_ownership(group_urn, dataset_urn, emitter)

                elif config["type"] == "tags":
                    for tag in value:
                        create_new_tag(tag, emitter)
                    tag_associations = [
                        TagAssociationClass(tag=builder.make_tag_urn(t.replace(" ", "_")))
                        for t in value
                    ]
                    emit_tags(dataset_urn, tag_associations, emitter)

                elif config["type"] == "dominio":
                    create_new_domain(config["domain_name"], config["domain_description"], emitter)
                    asignar_dominio(dataset_urn, config["domain_name"], emitter)

                else:
                    print(f"ℹ Tipo {config.get('type')} no manejado explícitamente para {prop_name}")

            else:
                print(f"⚠ No se encontró {prop_name} en {dataset_id}")

    start += pagesize
    if start >= csw.results.get("matches", 0):
        break

print("✅ Todos los datasets enviados con las propiedades configuradas.")
