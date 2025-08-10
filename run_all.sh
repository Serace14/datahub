#!/bin/bash

set -e  # Detiene el script si algún comando falla

./gradlew build -x test
./gradlew :metadata-service:war:build
./gradlew :datahub-frontend:dist -x yarnTest -x yarnLint
./gradlew :metadata-ingestion:installDev
./gradlew :docs-website:yarnLintFix :docs-website:build
./gradlew quickstartDebug
