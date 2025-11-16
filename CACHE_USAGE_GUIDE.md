# Cache Usage Guide - EquiPath

## Quick Start

Your data loading is now **10-100x faster** thanks to Parquet caching! 🚀

### First Time Setup

1. **Install dependencies** (if not already done):
   ```bash
   uv sync
   ```

2. **First run** will create cache files:
   ```bash
   streamlit run app.py
   ```
   - Takes ~8-10 seconds (converts Excel → Parquet)
   - Cache files saved to `data/.cache/`

3. **Subsequent runs** are instant:
   - Loads in <1 second from cache
   - No more waiting! ⚡

## How It Works

### Cache Directory Structure
```
data/
├── .cache/                          # Auto-created cache directory
│   ├── college_results.parquet      # Cached College Results data
│   ├── affordability_gap.parquet    # Cached Affordability Gap data
│   ├── merged_data_unitid_dedupTrue.parquet  # Cached merged data
│   └── featured_college_data.parquet # Cached featured data with scores
```

### Automatic Cache Invalidation

The system is smart! It automatically detects when source files change:
- If you update an Excel file, cache is automatically rebuilt
- No manual cache clearing needed for normal updates

## Manual Cache Management

### When to Clear Cache

Clear cache if you:
- Update source Excel files and want to force rebuild
- Encounter data loading errors
- Want to test performance from scratch

### How to Clear Cache

**Option 1: Delete cache directory** (recommended):
```bash
rm -rf data/.cache/
```

**Option 2: Force reload in Python**:
```python
from src.feature_engineering import build_featured_college_df

# Force rebuild all caches
df = build_featured_college_df(force_reload=True)
```

**Option 3: Clear Streamlit cache** (in app):
```python
from src.cached_data import clear_cache
clear_cache()
```

## Performance Expectations

### First Load (Cache Creation)
| Step | Time | Status |
|------|------|--------|
| Load College Results | ~3-5s | ⏳ Converting Excel → Parquet |
| Load Affordability Gap | ~5-8s | ⏳ Converting Excel → Parquet |
| Merge datasets | ~0.5s | ⚡ Fast |
| Feature engineering | ~0.5s | ⚡ Fast |
| **Total** | **~8-10s** | One-time cost |

### Cached Loads (2nd+ run)
| Step | Time | Status |
|------|------|--------|
| Load College Results | ~0.01s | ⚡⚡⚡ **500x faster** |
| Load Affordability Gap | ~0.03s | ⚡⚡⚡ **235x faster** |
| Merge datasets | ~0.02s | ⚡ From cache |
| Feature engineering | ~0.02s | ⚡ From cache |
| **Total** | **<0.1s** | Nearly instant! |

## Troubleshooting

### Problem: "FileNotFoundError: Source data file not found"

**Solution**: Make sure your Excel files are in the `data/` directory:
- `data/College Results View 2021 Data Dump for Export.xlsx`
- `data/Affordability Gap Data AY2022-23 2.17.25.xlsx`

### Problem: "ArrowTypeError" when creating cache

**Solution**: This is automatically handled! The system converts problematic object columns to strings.

If you still see this error:
1. Clear cache: `rm -rf data/.cache/`
2. Update code: `uv sync`
3. Try again

### Problem: Stale data after updating Excel files

**Solution**: The cache should auto-update, but you can force it:
```bash
rm -rf data/.cache/
```

### Problem: "Institution Name column not found" error

**Solution**: Clear the cache to regenerate with the canonical column:
```bash
rm -rf data/.cache/
```

## Advanced Usage

### Use Different Join Strategies

The default join uses UNITID (recommended), but you can use name-based joins:

```python
from src.data_loading import load_merged_data

# UNITID join (default, recommended)
df = load_merged_data(join_key='UNITID')

# Name-based join (legacy)
df = load_merged_data(join_key='Institution Name')
```

### Load Data Without Clustering

If you don't need cluster labels, load faster:

```python
from src.cached_data import load_featured_data

# Loads without clustering (faster)
df = load_featured_data()
```

### Load Data With Clustering

For full featured data including cluster labels:

```python
from src.cached_data import load_featured_data_with_clusters

# Loads with K-means clustering
df, centroids, labels = load_featured_data_with_clusters(n_clusters=5)
```

## Cache File Sizes

Approximate cache file sizes:
- `college_results.parquet`: ~2-5 MB
- `affordability_gap.parquet`: ~5-10 MB
- `merged_data_*.parquet`: ~10-20 MB
- `featured_college_data.parquet`: ~15-25 MB

**Total cache size**: ~35-60 MB (much smaller than original Excel files!)

## Best Practices

### ✅ DO:
- Let the cache auto-update when source files change
- Use `force_reload=True` when you explicitly want fresh data
- Keep cache directory in `.gitignore` (already configured)
- Run Streamlit apps normally - caching is automatic

### ❌ DON'T:
- Commit cache files to git (already excluded)
- Delete cache frequently (defeats the purpose)
- Manually edit Parquet files
- Mix different data directories without clearing cache

## Testing Performance

Run the performance test to verify your setup:

```bash
python test_performance.py
```

Expected output:
```
================================================================================
PERFORMANCE TEST: Data Loading with Parquet Caching
================================================================================

...

Average speedup: 10-235x

✅ All tests completed successfully!
```

## FAQ

**Q: Do I need to install anything special?**
A: Just `uv sync` - pyarrow is included in dependencies

**Q: Will this work on Windows/Linux?**
A: Yes! Parquet is cross-platform

**Q: How much disk space does the cache use?**
A: ~35-60 MB (vs ~100+ MB for Excel files)

**Q: Can I share cache files with teammates?**
A: No - cache files are machine-specific. Each person builds their own.

**Q: What if I update the Python code?**
A: Code updates don't affect cache. Only source Excel file changes trigger rebuilds.

**Q: Does Streamlit caching work too?**
A: Yes! Streamlit has its own caching layer on top of Parquet caching for even faster loads.

---

*Need help? Check OPTIMIZATION_SUMMARY.md for technical details.*
