#!/usr/bin/env bash
set -euo pipefail

# Batch runner for requests-library evaluation queries.
# For each query, runs:
#   1) baseline_comparison (full-repo vs Rabt)
#   2) validate_tokens (direct Gemini usage_metadata)
# with ~5s gaps to be gentle on rate limits.

REPO="examples/requests_repo"
OUT="evaluation/requests_queries_results.txt"

queries=(
  "Who calls request?"
  "Which functions call Session.request?"
  "Who calls merge_environment_settings?"
  "Which functions call HTTPAdapter.send?"
  "What functions are impacted if I change HTTPAdapter.build_response?"
  "Where is Response.status_code modified?"
  "Where is Session.cookies modified?"
  "Where is the timeout for a request configured or modified in the requests library?"
  "Where are proxy settings stored or modified in a Session?"
  "What code is impacted if I change Response.raise_for_status?"
  "What other functions are impacted if I change resolve_redirects?"
  "What parts of the code depend on Retry?"
  "Which functions are involved in selecting an HTTP adapter for a request?"
  "Which functions handle connection errors raised by HTTPAdapter.send?"
  "Which functions are involved in applying authentication to a request before it is sent?"
)

echo "Writing results to ${OUT}"
echo "Started at: $(date -Is)" >> "${OUT}"

for q in "${queries[@]}"; do
  echo "================================================================================" | tee -a "${OUT}"
  echo "QUERY: ${q}" | tee -a "${OUT}"
  echo "TIMESTAMP: $(date -Is)" | tee -a "${OUT}"
  echo "--------------------------------------------------------------------------------" | tee -a "${OUT}"

  echo "[1/2] baseline_comparison" | tee -a "${OUT}"
  .venv/bin/python -m evaluation.baseline_comparison --repo "${REPO}" --query "${q}" 2>&1 | tee -a "${OUT}" || true
  echo "" | tee -a "${OUT}"

  sleep 20

  echo "[2/2] validate_tokens" | tee -a "${OUT}"
  .venv/bin/python -m evaluation.validate_tokens --repo "${REPO}" --query "${q}" 2>&1 | tee -a "${OUT}" || true
  echo "" | tee -a "${OUT}"

  # Small gap between queries to respect free-tier rate limits
  sleep 20
done

echo "Finished at: $(date -Is)" >> "${OUT}"

