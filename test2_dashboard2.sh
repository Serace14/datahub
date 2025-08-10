#!/bin/bash

# Permite que el script siga ejecutándose aunque ocurran errores
set +e

TOKEN="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6IjQ0YzBkZTc4LWJlNTctNDA0Yi1hMmIzLTNjNjA3Zjg3MDYwNiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjAyMTA4ODAsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.ym_uhasuF7scL_x4ug1lezvu-o3fhvdtph9hZ-yVByQ"
API_URL="http://localhost:8080"
ENTITY_TYPE="dashboard2"
ASPECT_NAME="dashboard2Info"
DASHBOARD_ID=$((1000 + RANDOM % 9000))
URN="urn:li:dashboard2:(looker,looker.com/dashboards/$DASHBOARD_ID)"
ASPECT_FILE="dashboard2info.json"

FAILED_TESTS=()

# Test 1: Verifica que la entidad 'dashboard2' está registrada en el modelo de metadatos
echo
echo ">> Test 1: Verificar que la entidad '$ENTITY_TYPE' está registrada en metadata-model (search)"
RESPONSE=$(curl -s -X POST "$API_URL/entities?action=search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{ \"input\": \"*\", \"entity\": \"$ENTITY_TYPE\", \"start\": 0, \"count\": 10 }")

if echo "$RESPONSE" | jq -e .value >/dev/null; then
  echo "✅ Test 1 superado"
else
  echo "❌ Test 1 fallido: No se ha podido encontrar la entidad"
  echo "Mensaje de error completo:"
  echo "$RESPONSE"
  FAILED_TESTS+=("Test 1")
fi

# Test 2: Inserta un aspecto 'dashboard2Info' a la entidad 'dashboard2'
echo
echo ">> Test 2: Insertar aspecto '$ASPECT_NAME' para URN: $URN"
cat > "$ASPECT_FILE" <<EOF
{
  "title": "Mi Dashboard2",
  "description": "Descripción de prueba para dashboard2"
}
EOF

PUT_OUTPUT=$(datahub put --urn "$URN" --aspect "$ASPECT_NAME" -d "$ASPECT_FILE" 2>&1)
if echo "$PUT_OUTPUT" | grep -q "Update succeeded with status 200"; then
  echo "✅ Test 2 superado"
else
  echo "⚠️ Test 2: Puede que el aspecto ya exista o no se haya insertado correctamente"
  echo "Mensaje de error completo:"
  echo "$PUT_OUTPUT"
fi

# Test 3: Comprueba que el URN insertado existe
echo
echo ">> Test 3: Comprobar existencia del URN"
EXISTS_OUTPUT=$(datahub exists --urn "$URN" 2>&1)
if echo "$EXISTS_OUTPUT" | grep -q "true"; then
  echo "✅ Test 3 superado"
else
  echo "❌ Test 3 fallido: El URN no existe"
  echo "Mensaje de error completo:"
  echo "$EXISTS_OUTPUT"
  FAILED_TESTS+=("Test 3")
fi

# Test 4: Recupera el aspecto 'dashboard2Info' del URN
echo
echo ">> Test 4: Obtener aspecto '$ASPECT_NAME'"
GET_ASPECT=$(datahub get --urn "$URN" --aspect "$ASPECT_NAME" 2>&1)
if echo "$GET_ASPECT" | grep -q "title"; then
  echo "✅ Test 4 superado"
else
  echo "❌ Test 4 fallido: No se ha podido obtener el aspecto"
  echo "Mensaje de error completo:"
  echo "$GET_ASPECT"
  FAILED_TESTS+=("Test 4")
fi

# Test 5: Verifica que 'DASHBOARD2' está definido como EntityType en GraphQL
echo
echo ">> Test 5: Verificar que 'DASHBOARD2' aparece como EntityType en GraphQL"
GRAPHQL_QUERY='{"query":"{ __type(name: \"EntityType\") { enumValues { name } } }"}'

GRAPHQL_RESPONSE=$(curl -s -X POST "$API_URL/api/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "$GRAPHQL_QUERY")

if echo "$GRAPHQL_RESPONSE" | jq -e '.data.__type.enumValues[] | select(.name=="DASHBOARD2")' >/dev/null; then
  echo "✅ Test 5 superado"
else
  echo "❌ Test 5 fallido: DASHBOARD2 no está definido como EntityType"
  echo "Mensaje de error completo:"
  echo "$GRAPHQL_RESPONSE"
  FAILED_TESTS+=("Test 5")
fi

# Test 6: Ejecuta una búsqueda GraphQL para entidades DASHBOARD2
echo
echo ">> Test 6: Buscar entidades de tipo DASHBOARD2 por GraphQL"
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

RESULT=$(curl -s -X POST "$API_URL/api/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$SEARCH_QUERY")

if echo "$RESULT" | jq -e '.data.search.searchResults' >/dev/null; then
  echo "✅ Test 6 superado"
else
  echo "❌ Test 6 fallido: Error en la consulta de búsqueda"
  echo "Mensaje de error completo:"
  echo "$RESULT"
  FAILED_TESTS+=("Test 6")
fi

# Test 9: Valida que los datos del aspecto 'dashboard2Info' son correctos
echo
echo ">> Test 9: Validar estructura de dashboard2Info obtenida"
if echo "$GET_ASPECT" | jq -e '.title == "Mi Dashboard2"' >/dev/null; then
  echo "✅ Test 9 superado"
else
  echo "❌ Test 9 fallido: Los datos del aspecto no son correctos"
  echo "Mensaje de error completo:"
  echo "$GET_ASPECT"
  FAILED_TESTS+=("Test 9")
fi

# Test 10: Confirma que el URN sigue siendo accesible
echo
echo ">> Test 10: Comprobar que URN sigue siendo accesible"
EXISTS_AGAIN=$(datahub exists --urn "$URN" 2>&1)
if echo "$EXISTS_AGAIN" | grep -q "true"; then
  echo "✅ Test 10 superado"
else
  echo "❌ Test 10 fallido: El URN ha desaparecido"
  echo "Mensaje de error completo:"
  echo "$EXISTS_AGAIN"
  FAILED_TESTS+=("Test 10")
fi

# Test 11: Modifica el título del aspecto y lo vuelve a insertar
echo
echo ">> Test 11: Modificar el título del aspecto y volver a insertar"
cat > "$ASPECT_FILE" <<EOF
{
  "title": "Dashboard2 actualizado",
  "description": "Descripción modificada"
}
EOF

PUT_MOD=$(datahub put --urn "$URN" --aspect "$ASPECT_NAME" -d "$ASPECT_FILE" 2>&1)
if echo "$PUT_MOD" | grep -q "Update succeeded"; then
  echo "✅ Test 11 superado"
else
  echo "❌ Test 11 fallido: No se ha podido sobreescribir el aspecto"
  echo "Mensaje de error completo:"
  echo "$PUT_MOD"
  FAILED_TESTS+=("Test 11")
fi

# Test 12: Verifica que el nuevo título del aspecto se refleje
echo
echo ">> Test 12: Verificar actualización del título del aspecto"
UPDATED_ASPECT=$(datahub get --urn "$URN" --aspect "$ASPECT_NAME" 2>&1)
if echo "$UPDATED_ASPECT" | grep -q "Dashboard2 actualizado"; then
  echo "✅ Test 12 superado"
else
  echo "❌ Test 12 fallido: No se reflejó la modificación"
  echo "Mensaje de error completo:"
  echo "$UPDATED_ASPECT"
  FAILED_TESTS+=("Test 12")
fi

# Test 13: Verifica que browsePaths están disponibles para la entidad
echo
echo ">> Test 13: Verificar navegación con browsePaths para el URN"

GRAPHQL_BROWSEPATHS_QUERY=$(cat <<EOF
{
  "query": "query {
    entity(urn: \\"$URN\\") {
      ... on Dashboard2 {
        browsePaths
      }
    }
  }"
}
EOF
)

BROWSEPATHS_RESULT=$(curl -s -X POST "$API_URL/api/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$GRAPHQL_BROWSEPATHS_QUERY")

if echo "$BROWSEPATHS_RESULT" | jq -e '.data.entity.browsePaths | length > 0' >/dev/null; then
  echo "✅ Test 13 superado: browsePaths está presente"
else
  echo "❌ Test 13 fallido: browsePaths no encontrado"
  echo "Mensaje de error completo:"
  echo "$BROWSEPATHS_RESULT"
  FAILED_TESTS+=("Test 13")
fi

# Test 14: Búsqueda GraphQL con filtro por título actualizado
echo
echo ">> Test 14: Búsqueda parcial por título 'Dashboard2 actualizado'"

SEARCH_TITLE_QUERY=$(cat <<EOF
{
  "query": "query {
    search(input: {
      type: DASHBOARD2,
      query: \\"Dashboard2 actualizado\\",
      start: 0,
      count: 10
    }) {
      total
      searchResults {
        entity { urn }
      }
    }
  }"
}
EOF
)

TITLE_RESULT=$(curl -s -X POST "$API_URL/api/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$SEARCH_TITLE_QUERY")

if echo "$TITLE_RESULT" | jq -e ".data.search.searchResults[] | select(.entity.urn == \"$URN\")" >/dev/null; then
  echo "✅ Test 14 superado: La búsqueda devolvió el URN esperado"
else
  echo "❌ Test 14 fallido: La búsqueda no encontró el URN"
  echo "Mensaje de error completo:"
  echo "$TITLE_RESULT"
  FAILED_TESTS+=("Test 14")
fi

# Test 15: Consulta directa del dashboard2 por URN con GraphQL
echo
echo ">> Test 15: Ejecutar query específica dashboard2(urn: String)"

DASHBOARD2_QUERY=$(cat <<EOF
{
  "query": "query {
    dashboard2(urn: \\"$URN\\") {
      urn
      type
      dashboard2Info {
        name
        description
      }
    }
  }"
}
EOF
)

DASHBOARD2_RESULT=$(curl -s -X POST "$API_URL/api/graphql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DASHBOARD2_QUERY")

if echo "$DASHBOARD2_RESULT" | jq -e ".data.dashboard2.urn == \"$URN\"" >/dev/null; then
  echo "✅ Test 15 superado: Se ha podido consultar dashboard2 por URN"
else
  echo "❌ Test 15 fallido: La query específica no devolvió el resultado esperado"
  echo "Mensaje de error completo:"
  echo "$DASHBOARD2_RESULT"
  FAILED_TESTS+=("Test 15")
fi
