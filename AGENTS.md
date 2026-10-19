# Development & Agent Maintenance Guide for `term-stock-table`

## 🎯 Architecture Philosophy

`term-stock-table` is designed as a standalone, ultra-reliable terminal financial workstation. It follows these key architectural principles:

1. **Dual Execution Runtime**:
   - **TUI Mode (`Textual`)**: Interactive full-screen workstation with reactive modals and keybindings.
   - **CLI Snapshot / Watch Mode (`Rich`)**: Pure scriptable pipeline for tmux, i3bar, and stdout.
2. **Zero Hard Crash Tolerance**:
   - Network failure or malformed API responses must cleanly degrade to local geometric simulation without crashing.
3. **Privacy & Camouflage**:
   - Boss mode must execute synchronously and instantly without perceptible latency.

---

## 🧪 Testing & Quality Gates

Run the test suite with coverage:

```bash
pytest tests/ -v --cov=term_stock_table
```

All new features or indicator enhancements must satisfy:
- 100% test passing rate.
- Proper handling of empty data series, edge cases, and ticker formats.
- Palette consistency across CN (Red up, Green down) and US (Green up, Red down).

---

## 🎨 Asset & Showcase Maintenance

When updating features, regenerate the corresponding feature GIFs:

```bash
python3 tests/generate_feature_gifs.py
```

Target GIF files:
- `assets/demo.gif`
- `assets/features/watchlist_overview.gif`
- `assets/features/bollinger_and_indicators.gif`
- `assets/features/stock_detail_view.gif`
- `assets/features/investment_notes.gif`
- `assets/features/boss_mode_stealth.gif`
- `assets/features/watchlist_management.gif`

---

## 🚀 Publishing Checklist

1. Verify package metadata in `pyproject.toml`.
2. Confirm author information is `brwchen <brwchen@users.noreply.github.com>`.
3. Build distribution archives:
   ```bash
   python3 -m build
   ```
4. Check package with twine:
   ```bash
   twine check dist/*
   ```
5. Ensure git commit history contains no sensitive corporate info or internal references.
