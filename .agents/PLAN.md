# Fantasy Football ADP Value Prediction Plan

## Goal
Build ML model to identify value picks for 2026 fantasy (Half-PPR) - players likely to outperform their ADP.

## Your Questions Answered

### 1. Handling Player/Team Changes (WR getting new QB, etc.)
**Recommended approach: Context-independent stats + situation flags**

- **Use "sticky" metrics** that travel with the player:
  - WR: Yards per route run, separation, contested catch rate, target share %
  - RB: Yards after contact, missed tackles forced, snap share
  - QB: Accuracy %, BTT rate, pressure-to-sack rate (things that are QB skill, not team)
  - TE: Similar to WR metrics

- **Create situation-change features:**
  - `new_qb_flag` - binary if team's QB changed
  - `new_team_flag` - player changed teams
  - `qb_upgrade_score` - rate the new QB vs old (using PFF grades or similar)
  - `coaching_change_flag` - new OC/HC

- **Team context features (separate from player):**
  - Prior year team pass attempts, rush attempts
  - Team offensive line grade
  - New team's pass/rush tendencies

This lets the model learn: "WRs with X stats moving to better QB situations historically outperform ADP"

### 2. Is 5 Years of ADP Data Enough?
**Borderline but workable with the right approach:**

- ~250 players/year × 5 years = ~1250 data points
- After filtering to relevant players (say top 150 ADP): ~750 points
- **Mitigations:**
  - Use simpler models (Ridge regression, Random Forest with limited depth)
  - Feature selection - keep only 10-15 most predictive features
  - Cross-validation will be critical (leave-one-year-out)
  - Consider position-specific models (fewer features needed per position)

- **Data augmentation options:**
  - Weight recent years more heavily
  - If you can get pre-2020 finish data (even without ADP), can expand target variable

### 3. How to Evaluate ADP: Season Finish vs Next Year's ADP
**For value rankings: Use Points Above Expected (PAE) relative to draft slot**

Why not raw points: As you noted, QBs score more than WRs but aren't more valuable

**Recommended target variable:**
```
Value Score = (Actual Half-PPR PPG Rank) - (ADP Rank)
```
Negative = outperformed ADP (good pick), Positive = busted

**Alternative approaches:**
- VBD (Value Based Drafting): Points above replacement-level player at position
- Position-adjusted: Compare finish rank within position vs ADP rank within position
- Z-score: How many std devs above/below expected for that draft slot

**Don't use next year's ADP** - that just measures hype, not actual value delivered

### 4. Should You Account for Position Value?
**Let the data handle it, but help it along:**

- Train **one unified model** with `position` as a categorical feature
- The model will learn position-specific patterns naturally
- Your target variable (PPG rank vs ADP rank) already normalizes across positions

- **Additional position-aware features:**
  - `position_scarcity` - how deep is the position that year
  - `adp_vs_position_adp` - how player's ADP compares to others at position

---

## Implementation Plan

### Phase 1: Data Collection & Cleaning
Files to create/organize:
- [ ] Collect historical stats CSVs (rushing, receiving, passing) for 2019-2024 seasons
- [ ] Collect final fantasy point totals (Half-PPR) for each year
- [ ] Standardize player ID matching across sources (name variations, traded players)
- [ ] Create team context data (coaching changes, QB changes by year)

### Phase 2: Feature Engineering
Create `features.py`:
- [ ] Player performance features (position-specific sticky metrics)
- [ ] Situation change flags (new team, new QB, etc.)
- [ ] Team context features
- [ ] Historical ADP features (prior year ADP, ADP trend)
- [ ] Age/experience features

### Phase 3: Target Variable Construction
- [ ] Calculate Half-PPR PPG for each player-year
- [ ] Calculate PPG rank vs ADP rank differential
- [ ] Handle missing data (injured players, rookies)

### Phase 4: Model Development
- [ ] Start with Ridge Regression (interpretable baseline)
- [ ] Try Random Forest (handles non-linear relationships)
- [ ] Leave-one-year-out cross-validation
- [ ] Feature importance analysis

### Phase 5: 2026 Predictions
- [ ] Gather 2025 season stats
- [ ] Apply situation change features for 2026
- [ ] Generate value rankings
- [ ] Flag high-confidence value picks

---

## Key Files Structure
```
adp-estimate/
├── data/
│   ├── raw/           # Original CSVs (ADP, stats)
│   ├── processed/     # Cleaned, merged data
│   └── features/      # Engineered features
├── src/
│   ├── data_prep.py   # Loading, cleaning, merging
│   ├── features.py    # Feature engineering
│   ├── model.py       # Model training/eval
│   └── predict.py     # 2026 predictions
├── notebooks/
│   └── exploration.ipynb
└── outputs/
    └── 2026_rankings.csv
```

## Rookie Handling (College Stats Model)
Since rookies have no NFL track record, build separate pipeline:

**Data sources for college:**
- PFF College grades (if accessible)
- Sports Reference college stats
- NFL Combine metrics (40 time, vertical, etc.)
- Draft capital (round, pick number)

**Rookie-specific features:**
- College dominator rating (% of team production)
- Breakout age (when they first produced)
- Draft capital score
- College yards per route run / yards after contact
- Combine athletic scores

**Approach:**
- Train separate rookie model on historical rookie ADP vs rookie-year finish
- Smaller dataset but simpler problem (just predicting Year 1)
- Merge rookie predictions with vet predictions for final rankings

---

## Risks & Mitigations
- **Small dataset**: Use regularization, simple models, careful CV
- **Year-to-year variance**: Football is random; focus on directional accuracy not precision
- **Situation changes**: Some will be unknowable until August; build model to accept partial info
- **Rookie model**: Even smaller dataset; consider ensemble with analyst consensus
