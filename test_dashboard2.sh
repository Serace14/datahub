#!/bin/bash

set -e

TOKEN="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6IjQ0YzBkZTc4LWJlNTctNDA0Yi1hMmIzLTNjNjA3Zjg3MDYwNiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjAyMTA4ODAsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.ym_uhasuF7scL_x4ug1lezvu-o3fhvdtph9hZ-yVByQ"
API_URL="http://localhost:8080"
ENTITY_TYPE="dashboard2"
ASPECT_NAME="dashboard2Info"
DASHBOARD_ID=$((1000 + RANDOM % 9000))
URN="urn:li:dashboard2:(looker,looker.com/dashboards/$DASHBOARD_ID)"
ASPECT_FILE="dashboard2info.json"

echo ">> Test 1: Comprobar que la entidad '$ENTITY_TYPE' está registrada en metadata-model"
# Verifica si la entidad está registrada en el backend aunque no tenga instancias aún.
RESPONSE=$(curl -s -X POST "$API_URL/entities?action=search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{ \"input\": \"*\", \"entity\": \"$ENTITY_TYPE\", \"start\": 0, \"count\": 10 }" 2>&1 || true)

if echo "$RESPONSE" | jq -e .value >/dev/null; then
  echo "✅ Test 1 superado: La entidad $ENTITY_TYPE existe (aunque no tenga resultados)"
else
  echo "❌ Test 1 fallido: No se ha podido encontrar la entidad"
  echo "Mensaje de error completo:"
  echo "$RESPONSE"
  exit 1
fi

echo
echo ">> Test 2: Insertar aspecto '$ASPECT_NAME' para el URN: $URN"
# Intenta añadir un aspecto (metadata) a una entidad usando DataHub CLI.
cat > "$ASPECT_FILE" <<EOF
{
  "title": "Mi Dashboard2",
  "description": "Descripción de prueba para dashboard2"
}
EOF

RESULT2=$(datahub put --urn "$URN" --aspect "$ASPECT_NAME" -d "$ASPECT_FILE" 2>&1 || true)
if echo "$RESULT2" | grep -q "Update succeeded with status 200"; then
  echo "✅ Test 2 superado: Aspecto insertado correctamente"
else
  echo "⚠️ Test 2: El aspecto ya existe o no se pudo insertar"
  echo "Mensaje de error completo:"
  echo "$RESULT2"
fi

echo
echo ">> Test 3: Comprobar existencia del URN $URN"
# Verifica que el URN ha sido creado correctamente y es visible en el sistema.
EXISTS_RESULT=$(datahub exists --urn "$URN" 2>&1 || true)
if echo "$EXISTS_RESULT" | grep -q "true"; then
  echo "✅ Test 3 superado: El URN existe"
else
  echo "❌ Test 3 fallido: El URN no existe"
  echo "Mensaje de error completo:"
  echo "$EXISTS_RESULT"
  exit 1
fi

echo
echo ">> Test 4: Obtener aspecto '$ASPECT_NAME' del URN"
# Verifica que el aspecto previamente insertado puede recuperarse correctamente.
GET_ASPECT=$(datahub get --urn "$URN" --aspect "$ASPECT_NAME" 2>&1 || true)
if echo "$GET_ASPECT" | grep -q "title"; then
  echo "✅ Test 4 superado: Aspecto obtenido correctamente"
else
  echo "❌ Test 4 fallido: No se ha podido obtener el aspecto"
  echo "Mensaje de error completo:"
  echo "$GET_ASPECT"
  exit 1
fi

echo
echo ">> Test 5: Verificar que 'dashboard2' aparece como tipo GraphQL EntityType"
# Comprueba que la nueva entidad está registrada como tipo de GraphQL en el schema.
GRAPHQL_QUERY='{"query":"{ __type(name: \"EntityType\") { enumValues { name } } }"}'
RESULT5=$(curl -s -X POST "$API_URL/api/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$GRAPHQL_QUERY" 2>&1 || true)

if echo "$RESULT5" | jq -e '.data.__type.enumValues[] | select(.name=="DASHBOARD2")' >/dev/null; then
  echo "✅ Test 5 superado: DASHBOARD2 aparece como EntityType en GraphQL"
else
  echo "❌ Test 5 fallido: DASHBOARD2 no aparece como EntityType"
  echo "Mensaje de error completo:"
  echo "$RESULT5"
  exit 1
fi

echo
echo ">> Test 6: Ejecutar query GraphQL de búsqueda con tipo DASHBOARD2"
# Ejecuta una búsqueda GraphQL para comprobar que el tipo está funcionando correctamente.
SEARCH_QUERY=$(cat <<EOF
{
  "query": "query {
    search(input: {
      type: DASHBOARD2,
      query: \\"*\\",
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
  }"
}
EOF
)

RESULT6=$(curl -s -X POST "$API_URL/api/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$SEARCH_QUERY" 2>&1 || true)

if echo "$RESULT6" | jq -e '.data.search.searchResults' >/dev/null; then
  echo "✅ Test 6 superado: Consulta de búsqueda DASHBOARD2 ejecutada sin errores"
else
  echo "❌ Test 6 fallido: Error en consulta GraphQL"
  echo "Mensaje de error completo:"
  echo "$RESULT6"
  exit 1
fi

# Limpieza opcional
rm -f "$ASPECT_FILE"
