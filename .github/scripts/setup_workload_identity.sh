#!/usr/bin/env bash
# =============================================================================
# setup_workload_identity.sh — Configura Workload Identity Federation (WIF)
# entre o GitHub Actions e o Google Cloud, para o Job 2 (Gemini 3 Pro) operar
# SEM nenhum secret no repositório.
#
# Execução: UMA única vez, FORA do agente, por um operador com permissão de
# IAM no projeto GCP do escritório Ribeiro & Tigre.
#
#   ./setup_workload_identity.sh \
#       --repo "martbarreto-sudo/supreme-drafter" \
#       --project "[PROJECT_ID]"
#
# Ao final, imprime os valores a cadastrar em:
#   Settings > Secrets and variables > Actions > Repository VARIABLES
#     - GCP_WIF_PROVIDER
#     - GCP_SERVICE_ACCOUNT
#
# Pré-requisitos: gcloud autenticado (gcloud auth login) e APIs habilitadas:
#   iam.googleapis.com, iamcredentials.googleapis.com,
#   sts.googleapis.com, aiplatform.googleapis.com
# =============================================================================
set -euo pipefail

REPO=""
PROJECT=""
POOL="github-pool"
PROVIDER="github-provider"
SA_NAME="gemini-peer-review"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --pool) POOL="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    *) echo "Argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$REPO" || -z "$PROJECT" ]]; then
  echo "Uso: $0 --repo OWNER/REPO --project PROJECT_ID" >&2
  exit 2
fi

OWNER="${REPO%%/*}"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"

echo ">> Projeto: $PROJECT (número $PROJECT_NUMBER)"
echo ">> Repositório: $REPO (owner $OWNER)"

# 1) Service account dedicada para a revisão Gemini.
gcloud iam service-accounts create "$SA_NAME" \
  --project "$PROJECT" \
  --display-name "Gemini Peer-Review (R&T NEXUM TIER 0)" || true

# 2) Papel mínimo para chamar a Vertex AI (Gemini).
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member "serviceAccount:${SA_EMAIL}" \
  --role "roles/aiplatform.user"

# 3) Workload Identity Pool.
gcloud iam workload-identity-pools create "$POOL" \
  --project "$PROJECT" --location "global" \
  --display-name "GitHub Actions Pool" || true

# 4) Provider OIDC do GitHub, restrito ao repositório R&T.
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --project "$PROJECT" --location "global" \
  --workload-identity-pool "$POOL" \
  --display-name "GitHub OIDC" \
  --issuer-uri "https://token.actions.githubusercontent.com" \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition "assertion.repository == '${REPO}'" || true

# 5) Permite que o repositório assuma a service account (impersonation).
WIF_PRINCIPAL="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --project "$PROJECT" \
  --role "roles/iam.workloadIdentityUser" \
  --member "$WIF_PRINCIPAL"

PROVIDER_RESOURCE="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"

cat <<EOF

============================================================================
WIF configurado. Cadastre em Repository VARIABLES (NÃO secrets):

  GCP_WIF_PROVIDER  = ${PROVIDER_RESOURCE}
  GCP_SERVICE_ACCOUNT = ${SA_EMAIL}

Comando gh equivalente:
  gh variable set GCP_WIF_PROVIDER --repo "${REPO}" --body "${PROVIDER_RESOURCE}"
  gh variable set GCP_SERVICE_ACCOUNT --repo "${REPO}" --body "${SA_EMAIL}"
============================================================================
EOF
