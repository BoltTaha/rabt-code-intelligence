#!/bin/bash
# Safe benchmark runner with rate limiting for Gemini Free Tier
# This script runs benchmarks in batches to respect API limits

set -e  # Exit on error

echo "🔬 Safe Benchmark Runner for Gemini Free Tier"
echo "=============================================="
echo ""
echo "⚠️  Gemini Free Tier Limits (CONSERVATIVE):"
echo "   • Varies by model (2-15 RPM typical)"
echo "   • Check your limits: https://aistudio.google.com/rate-limit"
echo "   • Our delay: 15 seconds between calls (safe for 5 RPM)"
echo "   • Total time: ~5-10 minutes for full suite"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "   Create .env with GEMINI_API_KEY=your_key_here"
    exit 1
fi

# Source environment
source .env

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY not set in .env"
    exit 1
fi

echo "✅ API key found"
echo ""

# Function to run with rate limiting
run_with_limit() {
    local name=$1
    local command=$2
    local estimated_calls=$3
    
    echo "📊 Running: $name"
    echo "   Estimated API calls: $estimated_calls"
    echo "   Estimated time: $((estimated_calls * 5 / 60)) minutes"
    echo ""
    
    read -p "   Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        eval $command
        echo ""
        echo "✅ $name completed"
        echo "⏳ Cooling down for 10 seconds..."
        sleep 10
    else
        echo "⏭️  Skipped $name"
    fi
    echo ""
}

# 1. Ablation Study (NO API CALLS - Safe!)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  ABLATION STUDY (No API calls)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
run_with_limit \
    "Ablation Study" \
    "python evaluation/ablation_study.py" \
    "0"

# 2. Sample Repo Baseline (2 API calls)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  SAMPLE REPO BASELINE (2 API calls)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
run_with_limit \
    "Sample Repo: 'Where is userData modified?'" \
    "python evaluation/baseline_comparison.py examples/sample_repo 'Where is userData modified?'" \
    "2"

# 3. Requests Repo Baseline (2 API calls)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  REQUESTS REPO BASELINE (2 API calls)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
run_with_limit \
    "Requests Repo: 'Who calls request?'" \
    "python evaluation/baseline_comparison.py examples/requests_repo 'Who calls request?'" \
    "2"

# 4. Multi-Repo Benchmark (OPTIONAL - Many API calls!)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  MULTI-REPO BENCHMARK (12-24 API calls)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  WARNING: This will make 12-24 API calls"
echo "   Estimated time: 5-10 minutes"
echo "   Only run if you have quota available!"
echo ""
read -p "Run multi-repo benchmark? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python evaluation/multi_repo_benchmark.py
else
    echo "⏭️  Skipped multi-repo benchmark"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Benchmark Suite Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Results saved to:"
echo "   • evaluation/ablation_results.json"
echo "   • evaluation/baseline_comparison_*.txt"
echo "   • evaluation/multi_repo_results.json"
echo ""
echo "📊 Next steps:"
echo "   1. Review results: cat evaluation/ablation_results.json"
echo "   2. Update paper with new data"
echo "   3. Run visualization scripts"
echo ""
