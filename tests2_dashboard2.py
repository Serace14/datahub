import requests
import subprocess
import json
import random

TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImQyNDU4YTRkLTc2YTYtNDQ4My1iNWYyLTA2MDRiMjZiYmE4NiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NTU2ODA3NzksImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.pO264G1P2YRwLdIumiiT5s49wY7tmD0MLSpKHNaCOH8"
API_URL = "http://localhost:8080"
ENTITY_TYPE = "dashboard2"
ASPECT_NAME = "dashboard2Info"
DASHBOARD_ID = 1000 + random.randint(0, 8999)
URN = f"urn:li:dashboard2:(looker,looker.com/dashboards/{DASHBOARD_ID})"
ASPECT_FILE = "dashboard2info.json"

failed_tests = []

def run_datahub_command(args):
    """Ejecuta el comando datahub y devuelve stdout+stderr"""
    result = subprocess.run(["datahub"] + args, capture_output=True, text=True)
    return result.stdout + result.stderr

def test_1_entity_registered():
    print("\n>> Test 1: Verificar que la entidad está registrada")
    payload = {
        "input": "*",
        "entity": ENTITY_TYPE,
        "start": 0,
        "count": 10
    }
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(f"{API_URL}/entities?action=search", headers=headers, json=payload)
    try:
        r.json()["value"]
        print("✅ Test 1 superado")
    except (KeyError, json.JSONDecodeError):
        print("❌ Test 1 fallido: No se ha podido encontrar la entidad")
        print("Respuesta completa:", r.text)
        failed_tests.append("Test 1")

def test_2_insert_aspect():
    print("\n>> Test 2: Insertar aspecto dashboard2Info")
    aspect_data = {
        "title": "Mi Dashboard2",
        "description": "Descripcion de prueba para dashboard2"
    }
    with open(ASPECT_FILE, "w") as f:
        json.dump(aspect_data, f)

    output = run_datahub_command(["put", "--urn", URN, "--aspect", ASPECT_NAME, "-d", ASPECT_FILE])
    if "Update succeeded with status 200" in output:
        print("✅ Test 2 superado")
    else:
        print("⚠️ Test 2: Puede que el aspecto ya exista o no se haya insertado correctamente")
        print("Mensaje completo:", output)

def test_3_check_urn_exists():
    print("\n>> Test 3: Comprobar existencia del URN")
    output = run_datahub_command(["exists", "--urn", URN])
    if "true" in output.lower():
        print("✅ Test 3 superado")
    else:
        print("❌ Test 3 fallido: El URN no existe")
        print("Mensaje completo:", output)
        failed_tests.append("Test 3")

def test_4_get_aspect():
    print("\n>> Test 4: Obtener aspecto dashboard2Info")
    output = run_datahub_command(["get", "--urn", URN, "--aspect", ASPECT_NAME])
    if "title" in output:
        print("✅ Test 4 superado")
    else:
        print("❌ Test 4 fallido: No se ha podido obtener el aspecto")
        print("Mensaje completo:", output)
        failed_tests.append("Test 4")
    return output

def test_5_graphql_entitytype():
    print("\n>> Test 5: Verificar 'DASHBOARD2' en EntityType GraphQL")
    graphql_query = {"query": '{ __type(name: "EntityType") { enumValues { name } } }'}
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers, json=graphql_query)
    data = r.json()
    enum_values = data.get("data", {}).get("__type", {}).get("enumValues", [])
    if any(ev.get("name") == "DASHBOARD2" for ev in enum_values):
        print("✅ Test 5 superado")
    else:
        print("❌ Test 5 fallido: DASHBOARD2 no está definido")
        print("Respuesta completa:", r.text)
        failed_tests.append("Test 5")

def test_6_graphql_search():
    print("\n>> Test 6: Buscar entidades DASHBOARD2 por GraphQL")
    search_query = {
        "query": """
        query {
          search(input: {
            type: DASHBOARD2,
            query: "*",
            start: 0,
            count: 10
          }) {
            total
            searchResults {
              entity {
                urn
                type
              }
            }
          }
        }
        """
    }
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers, json=search_query)
    try:
        if r.json().get("data", {}).get("search", {}).get("searchResults") is not None:
            print("✅ Test 6 superado")
        else:
            raise ValueError()
    except Exception:
        print("❌ Test 6 fallido: Error en consulta búsqueda")
        print("Respuesta completa:", r.text)
        failed_tests.append("Test 6")

def test_7_graphql_search():
    print("\n>> Test 7: Buscar entidades DASHBOARD por GraphQL")
    search_query = {
        "query": """
        query {
          search(input: {
            type: DASHBOARD,
            query: "*",
            start: 0,
            count: 10
          }) {
            total
            searchResults {
              entity {
                urn
                type
              }
            }
          }
        }
        """
    }
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers, json=search_query)
    try:
        if r.json().get("data", {}).get("search", {}).get("searchResults") is not None:
            print("✅ Test 7 superado")
        else:
            raise ValueError()
    except Exception:
        print("❌ Test 7 fallido: Error en consulta búsqueda")
        print("Respuesta completa:", r.text)
        failed_tests.append("Test 7")

def test_9_validate_aspect_structure(get_aspect_output):
    print("\n>> Test 9: Validar estructura de dashboard2Info obtenida")
    try:
        aspect_json = json.loads(get_aspect_output)
        info = aspect_json.get("dashboard2Info", {})
        if info.get("title") == "Mi Dashboard2":
            print("✅ Test 9 superado")
        else:
            raise ValueError()
    except Exception:
        print("❌ Test 9 fallido: Los datos del aspecto no son correctos")
        print("Respuesta completa:", get_aspect_output)
        failed_tests.append("Test 9")

def test_10_check_urn_still_exists():
    print("\n>> Test 10: Comprobar que URN sigue siendo accesible")
    output = run_datahub_command(["exists", "--urn", URN])
    if "true" in output.lower():
        print("✅ Test 10 superado")
    else:
        print("❌ Test 10 fallido: El URN ha desaparecido")
        print("Mensaje completo:", output)
        failed_tests.append("Test 10")

def test_11_modify_aspect():
    print("\n>> Test 11: Modificar título del aspecto y volver a insertar")
    aspect_data = {
        "title": "Dashboard2 actualizado",
        "description": "Descripción modificada"
    }
    with open(ASPECT_FILE, "w") as f:
        json.dump(aspect_data, f)

    output = run_datahub_command(["put", "--urn", URN, "--aspect", ASPECT_NAME, "-d", ASPECT_FILE])
    if "Update succeeded" in output:
        print("✅ Test 11 superado")
    else:
        print("❌ Test 11 fallido: No se pudo sobreescribir el aspecto")
        print("Mensaje completo:", output)
        failed_tests.append("Test 11")

def test_12_verify_aspect_update():
    print("\n>> Test 12: Verificar actualización del título del aspecto")
    output = run_datahub_command(["get", "--urn", URN, "--aspect", ASPECT_NAME])
    if "Dashboard2 actualizado" in output:
        print("✅ Test 12 superado")
    else:
        print("❌ Test 12 fallido: No se reflejó la modificación")
        print("Mensaje completo:", output)
        failed_tests.append("Test 12")

def test_14_search_by_title():
    print("\n>> Test 14: Búsqueda parcial por título 'Dashboard2 actualizado'")
    query = {
        "query": f'''
        query {{
          search(input: {{
            type: DASHBOARD2,
            query: "Dashboard2 actualizado",
            start: 0,
            count: 10
          }}) {{
            total
            searchResults {{
              entity {{ urn }}
            }}
          }}
        }}
        '''
    }
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers, json=query)
    try:
        results = r.json().get("data", {}).get("search", {}).get("searchResults", [])
        if any(res.get("entity", {}).get("urn") == URN for res in results):
            print("✅ Test 14 superado: La búsqueda devolvió el URN esperado")
        else:
            raise ValueError()
    except Exception:
        print("❌ Test 14 fallido: La búsqueda no encontró el URN")
        print("Respuesta completa:", r.text)
        failed_tests.append("Test 14")

def test_15_query_dashboard2_by_urn():
    print("\n>> Test 15: Ejecutar query específica dashboard2(urn: String)")
    query = {
        "query": f'''
        query {{
          dashboard2(urn: "{URN}") {{
            urn
            type
            info {{
              name
              description
            }}
          }}
        }}
        '''
    }
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers, json=query)
    try:
        if r.json().get("data", {}).get("dashboard2", {}).get("urn") == URN:
            print("✅ Test 15 superado: Consulta dashboard2 por URN exitosa")
        else:
            raise ValueError()
    except Exception:
        print("❌ Test 15 fallido: Query específica no devolvió el resultado esperado")
        print("Respuesta completa:", r.text)
        failed_tests.append("Test 15")

def test_16_search_by_title():
    print("\n>> Test 16: Búsqueda parcial por título 'Mi Dashboard2'")
    query = {
        "query": f'''
        query {{
          search(input: {{
            type: DASHBOARD2,
            query: "Mi Dashboard2",
            start: 0,
            count: 10
          }}) {{
            total
            searchResults {{
              entity {{ urn }}
            }}
          }}
        }}
        '''
    }
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers, json=query)
    try:
        results = r.json().get("data", {}).get("search", {}).get("searchResults", [])
        if any(res.get("entity", {}).get("urn") == URN for res in results):
            print("✅ Test 16 superado: La búsqueda devolvió el URN esperado")
        else:
            raise ValueError()
    except Exception:
        print("❌ Test 16 fallido: La búsqueda no encontró el URN")
        print("Respuesta completa:", r.text)
        failed_tests.append("Test 16")

def main():
    test_1_entity_registered()
    test_2_insert_aspect()
    test_3_check_urn_exists()
    get_aspect_output = test_4_get_aspect()
    test_5_graphql_entitytype()
    test_6_graphql_search()
    test_7_graphql_search()
    test_9_validate_aspect_structure(get_aspect_output)
    test_10_check_urn_still_exists()
    test_11_modify_aspect()
    test_12_verify_aspect_update()
    test_14_search_by_title()
    test_15_query_dashboard2_by_urn()
    test_16_search_by_title()

    if failed_tests:
        print("\nTests fallidos:", failed_tests)
    else:
        print("\nTodos los tests superados correctamente.")

if __name__ == "__main__":
    main()
