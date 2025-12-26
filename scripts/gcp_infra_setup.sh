#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Mozart GCP Infrastructure Setup
# ═══════════════════════════════════════════════════════════════
# Run this script after authenticating with: gcloud auth login
# ═══════════════════════════════════════════════════════════════

set -e

PROJECT_ID="gen-lang-client-0658701327"
REGION="asia-southeast1"

echo "═══════════════════════════════════════════════════════════"
echo "🛡️ Mozart Infrastructure Setup"
echo "═══════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────────────
# Phase 2: Alerting (Free)
# ─────────────────────────────────────────────────────────────────
echo ""
echo "📢 Phase 2: Setting up Alerting..."
echo "⚠️  NOTE: Alerting is best set up via GCP Console:"
echo "   1. Go to: https://console.cloud.google.com/monitoring/alerting"
echo "   2. Click 'Create Policy'"
echo "   3. Add condition: Cloud Run → Request count → filter status >= 500"
echo "   4. Set threshold: > 5 in 5 minutes"
echo "   5. Add notification channel: Email"
echo ""

# ─────────────────────────────────────────────────────────────────
# Phase 4: Secret Manager (~$1/month)
# ─────────────────────────────────────────────────────────────────
echo "🔐 Phase 4: Setting up Secret Manager..."

# Check if secret exists
if gcloud secrets describe gemini-key --project=$PROJECT_ID 2>/dev/null; then
    echo "✅ Secret 'gemini-key' already exists"
else
    echo "Creating secret 'gemini-key'..."
    echo "⚠️  Please enter your Gemini API key when prompted:"
    # Create secret (will prompt for value)
    # Uncomment to run:
    # echo -n "YOUR_API_KEY" | gcloud secrets create gemini-key --data-file=- --project=$PROJECT_ID
    echo "⏸️  Skipped - uncomment the line above and add your key"
fi

# Grant Cloud Run access to secrets
echo "Granting Cloud Run access to secrets..."
# Get service account
SA_EMAIL="203658178245-compute@developer.gserviceaccount.com"
# Uncomment to run:
# gcloud secrets add-iam-policy-binding gemini-key \
#     --member="serviceAccount:$SA_EMAIL" \
#     --role="roles/secretmanager.secretAccessor" \
#     --project=$PROJECT_ID
echo "⏸️  Skipped - uncomment when ready"

# ─────────────────────────────────────────────────────────────────
# Phase 5: Cloud Armor (~$5-15/month) - COMMENTED OUT
# ─────────────────────────────────────────────────────────────────
echo ""
echo "🛡️ Phase 5: Cloud Armor (SKIPPED - รอมีงบ)"
echo ""

# Uncomment below when ready to enable Cloud Armor:
# 
# # Create security policy
# gcloud compute security-policies create mozart-security \
#     --description="Mozart DDoS protection" \
#     --project=$PROJECT_ID
#
# # Add rate limiting rule (block if > 100 requests/min from same IP)
# gcloud compute security-policies rules create 1000 \
#     --security-policy=mozart-security \
#     --action=rate-based-ban \
#     --rate-limit-threshold-count=100 \
#     --rate-limit-threshold-interval-sec=60 \
#     --ban-duration-sec=600 \
#     --conform-action=allow \
#     --exceed-action=deny-403 \
#     --project=$PROJECT_ID
#
# echo "✅ Cloud Armor enabled"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Setup complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Set up Alerting in GCP Console (link above)"
echo "  2. Uncomment Secret Manager commands and add your API key"
echo "  3. When you have budget, uncomment Cloud Armor section"
