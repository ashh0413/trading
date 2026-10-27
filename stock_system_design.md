# Stock Signal System — Design Spec

## Overview

A daily stock screening tool that scores 213 Indian stocks and surfaces actionable BUY/HOLD/AVOID signals. Clean, calm interface. No clutter.

---

## Design Language

### Aesthetic Direction
Apple — functional minimalism. Think Stocks app meets Weather app. Data is the hero, not decoration.

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--bg-primary` | `#000000` | Main background |
| `--bg-secondary` | `#1C1C1E` | Cards, sections |
| `--bg-tertiary` | `#2C2C2E` | Hover states, borders |
| `--text-primary` | `#FFFFFF` | Headlines, scores |
| `--text-secondary` | `#8E8E93` | Labels, metadata |
| `--text-tertiary` | `#636366` | Disabled, hints |
| `--accent-green` | `#30D158` | BUY signals, bullish |
| `--accent-red` | `#FF453A` | AVOID signals, bearish |
| `--accent-yellow` | `#FFD60A` | HOLD signals, neutral |
| `--accent-blue` | `#0A84FF` | Links, interactive |

### Typography

- **Display** — SF Pro Display Bold 34pt (scores, hero numbers)
- **Headline** — SF Pro Display Semibold 22pt (section titles)
- **Body** — SF Pro Text Regular 17pt (stock names, labels)
- **Caption** — SF Pro Text Regular 13pt (metadata, timestamps)
- **Mono** — SF Mono Medium 15pt (RSI values, percentages)

### Spacing System

```
--space-xs: 4px
--space-sm: 8px
--space-md: 16px
--space-lg: 24px
--space-xl: 40px
--space-2xl: 64px
```

### Motion

- Fade in: 300ms ease-out
- Card hover: 150ms ease
- Score reveal: staggered 50ms per item
- Pull to refresh: spring physics

---

## App Structure

### Screen 1 — Dashboard (Home)

```
┌─────────��───────────────────────────┐
│  Stock Signals          Yesterday ▼ │
│                                     │
│  ┌─────────┐ ┌─────────┐           │
│  │   7     │ │   5     │           │
│  │  BUY    │ │  HOLD   │           │
│  └─────────┘ └─────────┘           │
│  ┌─────────┐                       │
│  │   3     │                       │
│  │ AVOID   │                       │
│  └─────────┘                       │
│                                     │
│  ── TOP BUY ──────────────────────  │
│                                     │
│  LUPIN            82 / 100         │
│  Pharma · RSI 21 · MACD ↑          │
│  ════════��══════░░░░░░░░ 82%       │
│                                     │
│  AMBUJACEM         78 / 100        │
│  Cement · RSI 10 · Vol Spike       │
│  ═══════════════░░░░░░░░ 78%       │
��                                     │
│  FORTIS             75 / 100       │
│  Pharma · RSI 11 · Bull Div        │
│  ═══════════════░░░░░░░ 75%        │
│                                     │
│  ── SECTOR STRENGTH ─────────────  │
│                                     ���
│  Cement    ████████████░░  78%      │
│  Pharma    ██████████░░░░  65%      │
│  FMCG      ████████░░░░░░  52%      │
│                                     │
└─────────────────────────────────────┘
```

### Screen 2 — Stock Detail (Tap any stock)

```
┌─────────────────────────────────────┐
│  ← Back                             │
│                                     │
│  LUPIN                              │
│  Pharmaceutical                     │
│                                     │
│           82                        │
│         / 100                       │
│                                     │
│  ████████████░░░░░░░░░░░░░░ 82%    ��
│                                     │
│  ── INDICATORS ──────────────────── │
│                                     │
│  RSI (DAY)     21.7    ↘ Bear Div  │
│  RSI (WEEK)     8.5    ↘ Bear Div  │
│  RSI (MONTH)   53.3                │
│  RSI (1HR)     42.1                │
│                                     │
│  MACD          CROSSED UP           │
│  Volume        1.8x average        │
│  SMA 50        Above ✔             │
│  SMA 200       Below ✘             │
│                                     │
│  ── SIGNAL ──────────────────────── │
│                                     │
│  🟢 BUY                              │
│  Oversold + Bullish Divergence      │
│                                     │
│  Last updated: Today, 9:30 AM      │
│                                     │
└─────────────────────────────────────┘
```

---

## Architecture

```
┌──────────────────────────────────────────────┐
│                  DATA LAYER                  │
│                                              │
│  scanner_v2.py                               │
│  ├── yfinance → RSI, MACD, Volume, SMA       │
│  ├── Divergence detection                    │
│  └── Output: scanner_results.json           │
│                                              │
│  scorer.py                                   │
│  ├── Read scanner_results.json               │
│  ├── Score each stock (0-100)               │
│  └── Output: scored_stocks.json              │
│                                              │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│               PRESENTATION LAYER             │
│                                              │
│  report.py  (CLI)        dashboard.html      │
│  ├── ASCII report        ├── Dark mode        │
│  ├── Top 10 BUY          ├── Animated scores │
│  ├── AVOID list          ├── Tap details     │
│  └── Sector summary     └── Auto-refresh     │
│                                              │
│  export_telegram.py  (optional)               │
│  └── Send daily digest to Telegram           │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Scoring Model

| Indicator | Weight | Signal |
|---|---|---|
| RSI (oversold <30) | 25% | +20 if oversold |
| RSI (overbought >70) | 25% | -20 if overbought |
| MACD Crossover | 20% | +15 if bullish cross |
| Volume Spike | 15% | +10 if >1.5x avg |
| SMA 50 vs Price | 15% | +10 if price > SMA50 |
| SMA 200 vs Price | 15% | +10 if price > SMA200 |
| Bullish Divergence | +10/bear | Extra points |
| Bearish Divergence | -10/bear | Deduct points |

**Total score 0-100**

| Score | Signal | Color |
|---|---|---|
| 70-100 | BUY | Green |
| 40-69 | HOLD | Yellow |
| 0-39 | AVOID | Red |

---

## Key Principles

1. **Data is the interface** — no charts unless they add signal
2. **One number tells the story** — the score (0-100)
3. **Scan daily, deliver once** — morning report, no noise
4. **Dark mode only** — easier on eyes, feels premium
5. **No accounts, no sync** — local files, no cloud lock-in

---

## File Outputs

```
D:\MOVED FROM C\Python\venvs\py311\Scripts\
├── scanner_v2.py         # Data fetch
├── scorer.py             # Scoring engine
├── report.py             # CLI report generator
├── dashboard.html         # Web view
├── scanner_results.json   # Raw RSI data
└── scored_stocks.json     # Final ranked list
```
