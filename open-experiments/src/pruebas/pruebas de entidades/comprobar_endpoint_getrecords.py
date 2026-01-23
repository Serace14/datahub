import requests
import xml.etree.ElementTree as ET

# Endpoint del CSW
csw_url = "https://www.idee.es/csw-inspire-idee/srv/spa/csw"

# Parámetros para GetRecords (CSW 2.0.2, formato XML)
params = {
    "service": "CSW",
    "version": "2.0.2",
    "request": "GetRecords",
    "resultType": "results",       # Solo resultados (no count)
    "outputSchema": "http://www.opengis.net/cat/csw/2.0.2",
    "typeNames": "csw:Record",
    "elementSetName": "full",
    "startPosition": "1",          # Desde el primer registro
    "maxRecords": "5"              # Número de registros que queremos
}

# Realizar la petición
response = requests.get(csw_url, params=params)
response.raise_for_status()

# Ver respuesta cruda (XML)
print("XML recibido:")
print(response.text[:500] + "\n...")  # Solo primeros 500 caracteres

# Parsear el XML
root = ET.fromstring(response.content)

# Namespace para buscar elementos
ns = {
    "csw": "http://www.opengis.net/cat/csw/2.0.2",
    "dc": "http://purl.org/dc/elements/1.1/"
}

# Extraer títulos de registros
print("\nRegistros encontrados:")
for rec in root.findall(".//csw:Record", ns):
    title = rec.find("dc:title", ns)
    if title is not None:
        print("-", title.text)
