import requests
import pprint

GRAPHQL_URL = "http://localhost:8080/api/graphql"
CATALOG_URN = "urn:li:catalogRecord:(urn:li:dataPlatform:geoserver,7eea5c42-212f-4099-b9df-1e3703fbc616,PROD)"
PLATFORM_RESOURCE_URN = "urn:li:platformResource:geoserver-7eea5c42-212f-4099-b9df-1e3703fbc616"

def run_graphql_query(query, variables=None):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()

def main():
    print("🔍 Consultando CatalogRecord para ver asociación con PlatformResource...")

    query = """
    query getCatalogWithRelationships($urn: String!) {
      catalogRecord(urn: $urn) {
        urn
        properties {
          name
          description
        }
        relationships(input: {types: ["AssociatedWith"], direction: OUTGOING}) {
          relationships {
            entity {
              urn
            }
            type
          }
        }
      }
    }
    """

    resp_json = run_graphql_query(query, {"urn": CATALOG_URN})

    print("\n=== GraphQL Response ===")
    pprint.pprint(resp_json)

    # Validaciones seguras
    if "data" not in resp_json or not resp_json["data"].get("catalogRecord"):
        raise ValueError(f"❌ No se encontró el CatalogRecord {CATALOG_URN}")

    catalog = resp_json["data"]["catalogRecord"]
    rels = catalog.get("relationships", {}).get("relationships", [])
    related_urns = [r["entity"]["urn"] for r in rels]

    if PLATFORM_RESOURCE_URN in related_urns:
        print(f"✅ El CatalogRecord {CATALOG_URN} está asociado correctamente con {PLATFORM_RESOURCE_URN}")
    else:
        print(f"❌ No se encontró relación 'AssociatedWith' entre {CATALOG_URN} y {PLATFORM_RESOURCE_URN}")

if __name__ == "__main__":
    main()
