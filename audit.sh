#!/bin/sh
# Audit de securite : CVE (pip-audit + Trivy) + dependances perimees
set -e
IMAGE="conso-maison-conso"

echo "=============================================="
echo " AUDIT SECURITE - $(date '+%Y-%m-%d %H:%M')"
echo "=============================================="

echo ""
echo ">>> [1/3] Dependances Python vulnérables (pip-audit)"
echo "------------------------------------------------"
docker run --rm -v "$PWD/requirements.txt:/requirements.txt:ro" \
  python:3.12-slim sh -c \
  "pip install -q pip-audit && pip-audit -r /requirements.txt" \
  || echo "(pip-audit termine : voir CVEs eventuelles ci-dessus)"

echo ""
echo ">>> [2/3] Dependances Python perimees (pip list --outdated)"
echo "------------------------------------------------"
echo "NB : perime != vulnérable. Ne bump QUE si CVE avec fix."
docker compose exec conso pip list --outdated \
  || echo "(conteneur conso non demarre ?)"

echo ""
echo ">>> [3/3] Image Docker (Trivy, HIGH/CRITICAL)"
echo "------------------------------------------------"
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --severity HIGH,CRITICAL "$IMAGE" \
  || echo "(Trivy termine : voir CVEs eventuelles ci-dessus)"

echo ""
echo "=============================================="
echo " Pour patcher l'image : docker compose build --pull --no-cache && docker compose up -d"
echo " Pour patcher le Python : voir version 'latest' ci-dessus,"
echo "   editer requirements.txt, puis rebuild + TEST."
echo "=============================================="
