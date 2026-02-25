# 🚦 Rate Limiting Guide for Gemini Free Tier

## ✅ Updated Configuration

All benchmark scripts now include **proper rate limiting** for Gemini free tier:

### Current Settings:
- **15 seconds** between API calls
- **4 requests per minute** (safely under 5 RPM limit)
- Automatic delays with progress indicators

## 🔍 Check Your Actual Limits

Visit: https://aistudio.google.com/rate-limit

Typical free tier limits:
- 📉 **2 RPM**: Very restricted (30s delay recommended)
- 📊 **5 RPM**: Common free tier (our 15s delay is safe)
- 📈 **15 RPM**: Higher free tier (5s delay sufficient)

## 📝 Updated Scripts

### 1. **safe_benchmark_runner.sh** ✅
Interactive runner with rate limiting
```bash
bash evaluation/safe_benchmark_runner.sh
```
- Ablation study: 0 API calls (safe!)
- Sample repo: 2 API calls (~30 seconds)
- Requests repo: 2 API calls (~30 seconds)
- Multi-repo: 12-24 API calls (~5-10 minutes)

### 2. **baseline_comparison.py** ✅
Now includes 15s delay between calls
```bash
python evaluation/baseline_comparison.py examples/sample_repo "Where is userData modified?"
```
Time: ~30 seconds per query (2 API calls)

### 3. **multi_repo_benchmark.py** ✅
Automatic rate limiting built-in
```bash
python evaluation/multi_repo_benchmark.py
```
Estimated time: 5-10 minutes for full benchmark

### 4. **ablation_study.py** ✅
**No API calls!** Safe to run anytime
```bash
python evaluation/ablation_study.py
```
Only builds graphs, no Gemini API usage

## 🎯 Recommended Workflow

### Day 1: No API Calls
```bash
# Clone repos (no API)
bash evaluation/clone_test_repos.sh

# Run ablation study (no API)
python evaluation/ablation_study.py

# Review results
cat evaluation/ablation_results.json
```

### Day 2: Sample Repo Testing (4 API calls)
```bash
# Morning: 2 API calls
python evaluation/baseline_comparison.py examples/sample_repo "Where is userData modified?"

# Afternoon: 2 API calls
python evaluation/baseline_comparison.py examples/sample_repo "Who calls save_user?"
```

### Day 3: Requests Repo Testing (4 API calls)
```bash
# Morning: 2 API calls
python evaluation/baseline_comparison.py examples/requests_repo "Who calls request?"

# Afternoon: 2 API calls
python evaluation/baseline_comparison.py examples/requests_repo "What does Session depend on?"
```

### Day 4+: Multi-Repo (if needed)
Only if you have high quota available!

## 💡 Tips to Avoid Rate Limits

1. **Check your tier first**: https://aistudio.google.com/rate-limit
2. **Start with ablation study**: No API calls needed!
3. **Run benchmarks in batches**: 2-4 queries per day
4. **Use the safe runner**: It has built-in delays
5. **Monitor your usage**: Dashboard shows remaining quota

## 🔧 Customize Delay

If your limit is different, adjust in scripts:

```python
# For 2 RPM (very restricted)
rate_limit_delay = 30.0  # 30 seconds

# For 10 RPM (higher tier)
rate_limit_delay = 6.0   # 6 seconds

# For 15 RPM (highest free tier)
rate_limit_delay = 4.0   # 4 seconds
```

## ✅ What Works Without API Calls

Perfect for daily development:
- ✅ Build graphs (parser + graph builder)
- ✅ Run ablation study (graph comparisons)
- ✅ Visualize graphs (visualize_graph.py)
- ✅ Test intent parsing (regex mode)
- ✅ Extract subgraphs
- ✅ Update documentation

## ⚠️ What Requires API Calls

Use sparingly:
- ❌ Full baseline comparisons
- ❌ LLM-based intent routing (optional)
- ❌ Answer generation with Gemini
- ❌ Multi-repo benchmarks

## 📊 Quota Planning

Free tier daily limit: **1,500 requests/day**

Our benchmark usage:
- Ablation study: 0 calls
- Sample repo (1 query): 2 calls
- Requests repo (1 query): 2 calls
- Multi-repo full (12 queries): 24 calls

Total for full evaluation: **~30 API calls** (2% of daily quota)

## 🚀 Ready to Start?

```bash
# Step 1: Check your limits
python evaluation/check_rate_limits.py

# Step 2: Run safe benchmark (interactive)
bash evaluation/safe_benchmark_runner.sh

# Step 3: Review results
ls -la evaluation/*.json
```

All scripts now respect rate limits! 🎉
