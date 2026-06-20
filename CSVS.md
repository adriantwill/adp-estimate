# nflverse CSVs

These are the nflverse datasets that are already useful for this project, or could be useful for WR/QB/team-environment features.

Prefer loading through `nflreadpy` instead of manually downloading CSVs. CSV URLs are listed so the data source is clear.

Base URL pattern:

```text
https://github.com/nflverse/nflverse-data/releases/download/{release_tag}/{file_name}
```

## Core For This Project

### Play By Play

Release tag:

```text
pbp
```

CSV files:

```text
play_by_play_YEAR.csv
play_by_play_YEAR.csv.gz
```

`nflreadpy` loader:

```text
load_pbp()
```

Use for:

```text
pass_rate
neutral_pass_rate
plays_per_game
pace
red_zone_rate
red_zone_pass_rate
first_down_pass_rate
pass_oe
EPA/play
success_rate
dropback EPA
rush EPA
red zone trips/game
QB/team game environment
coach tendency if joined to schedules
```

Most important team-environment source.

### Player Summary Stats

Release tag:

```text
stats_player
```

CSV files:

```text
stats_player_reg_YEAR.csv
stats_player_reg_YEAR.csv.gz
stats_player_week_YEAR.csv
stats_player_week_YEAR.csv.gz
```

`nflreadpy` loader:

```text
load_player_stats()
```

Use for:

```text
targets
receptions
receiving_yards
receiving_tds
air_yards
target_share
air_yards_share
wopr
fantasy_points
fantasy_points_ppr
QB passing stats
RB/TE/WR team target split
target concentration
vacated targets
vacated air yards
```

Main replacement for many raw receiving/passing finish stats.

### Team Summary Stats

Release tag:

```text
stats_team
```

CSV files:

```text
stats_team_reg_YEAR.csv
stats_team_reg_YEAR.csv.gz
stats_team_week_YEAR.csv
stats_team_week_YEAR.csv.gz
```

`nflreadpy` loader:

```text
load_team_stats()
```

Use for:

```text
team passing volume
team rushing volume
team touchdowns
team yards
team fantasy/scoring environment checks
quick team-level baselines
```

Use PBP for more precise environment stats. Use team stats for simpler season summaries.

### Schedules / Games

Release tag:

```text
schedules
```

CSV files:

```text
games.csv
games.csv.gz
```

`nflreadpy` loader:

```text
load_schedules()
```

Use for:

```text
home_team
away_team
home_coach
away_coach
roof
surface
temp
wind
total_line
spread_line
game location
game dates
```

Main source for head coach, weather, betting totals, implied totals, and scoring context.

### Rosters

Release tag:

```text
rosters
```

CSV files:

```text
roster_YEAR.csv
roster_YEAR.csv.gz
```

`nflreadpy` loader:

```text
load_rosters()
```

Use for:

```text
player IDs
team
position
age
height
weight
years experience
status
college
rookie/non-rookie flags
team/player matching
```

Useful for stable joins and player-level context.

### Depth Charts

Release tag:

```text
depth_charts
```

CSV files:

```text
depth_charts_YEAR.csv
depth_charts_YEAR.csv.gz
```

`nflreadpy` loader:

```text
load_depth_charts()
```

Use for:

```text
listed starter role
depth team
depth position
WR room competition
QB starter context
role continuity
offseason opportunity changes
```

Do not use this as target share by itself. Target share comes from targets / team targets.

### Snap Counts

Release tag:

```text
snap_counts
```

CSV files:

```text
snap_counts_YEAR.csv
snap_counts_YEAR.csv.gz
```

`nflreadpy` loader:

```text
load_snap_counts()
```

Use for:

```text
offensive snaps
snap share
route/snap opportunity proxy
role growth
injury/benching context
pts_per_snap checks
```

Useful if replacing `ptsPerSnap` style features from fantasy finish files.

### Draft Picks

Release tag:

```text
draft_picks
```

CSV files:

```text
draft_picks.csv
draft_picks.csv.gz
```

`nflreadpy` loader:

```text
load_draft_picks()
```

Use for:

```text
draft year
draft round
draft pick
draft capital
rookie contract window
years_since_draft
prospect pedigree
```

This can replace or validate local `draft_picks.csv`.

## Useful Optional Add-Ons

### FTN Charting

Release tag:

```text
ftn_charting
```

CSV files:

```text
ftn_charting_YEAR.csv
```

`nflreadpy` loader:

```text
load_ftn_charting()
```

Use for:

```text
motion_rate
play_action_rate
screen_rate
rpo_rate
no_huddle_rate
trick_play_rate
QB out-of-pocket rate
offensive backfield structure
defensive box counts faced
```

Best source for offensive scheme tendencies that PBP does not describe cleanly.

### Next Gen Stats

Release tag:

```text
nextgen_stats
```

CSV files:

```text
ngs_YEAR_passing.csv.gz
ngs_YEAR_receiving.csv.gz
ngs_YEAR_rushing.csv.gz
ngs_passing.csv.gz
ngs_receiving.csv.gz
ngs_rushing.csv.gz
```

`nflreadpy` loader:

```text
load_nextgen_stats()
```

Use for:

```text
QB aggressiveness
time to throw
completion probability
CPOE
air yards context
receiver separation-style efficiency
YAC context
```

Useful for QB quality and WR efficiency, but probably secondary to ADP, PFF, and team environment.

### Injuries

Release tag:

```text
injuries
```

CSV files:

```text
injuries_YEAR.csv
injuries_YEAR.csv.gz
```

`nflreadpy` loader:

```text
load_injuries()
```

Use for:

```text
missed-time context
injury designation
weekly availability
teammate injury effects
QB/WR continuity issues
```

Could help explain bad prior-year stats or opportunity changes.

### Players

Release tag:

```text
players
```

CSV files:

```text
players.csv
players.csv.gz
```

`nflreadpy` loader:

```text
load_players()
```

Use for:

```text
stable player IDs
name matching
birth date
position
college
physical profile
```

Good join table.

### Combine

Release tag:

```text
combine
```

CSV files:

```text
combine.csv
combine.csv.gz
```

`nflreadpy` loader:

```text
load_combine()
```

Use for:

```text
speed
explosion
size
athletic profile
prospect context
```

Mostly useful for rookies and young WR breakout subsets.

### Officials

Release tag:

```text
officials
```

CSV files:

```text
officials.csv
officials.csv.gz
```

`nflreadpy` loader:

```text
load_officials()
```

Use for:

```text
referee context
penalty environment
game-level controls
```

Probably low priority for this project.

## Lower Priority / Situational

### Weekly Rosters

`nflreadpy` loader:

```text
load_rosters_weekly()
```

Use for:

```text
weekly team changes
active roster status
practice squad / roster movement context
```

Useful if modeling weekly outcomes. Lower priority for season-long ADP vs finish.

### Participation

`nflreadpy` loader:

```text
load_participation()
```

Use for:

```text
personnel groupings
player participation
formation/personnel context
route participation proxies
```

Useful if you want better role/scheme detail than snap counts.

### Contracts

`nflreadpy` loader:

```text
load_contracts()
```

Use for:

```text
team investment
guaranteed money
contract year
free-agent addition strength
```

Could help with personnel-change features, but not core.

### Trades

`nflreadpy` loader:

```text
load_trades()
```

Use for:

```text
team/player movement
offseason environment changes
vacated targets context
new WR/QB additions
```

Helpful for manual environment review. Lower priority for first model pass.

## Priority Order

Start here:

```text
1. pbp
2. stats_player
3. schedules
4. rosters
5. depth_charts
6. snap_counts
7. draft_picks
8. ftn_charting
9. nextgen_stats
10. injuries
```

For the current WR fantasy project, highest-value feature groups are:

```text
ADP
prior player usage
prior player efficiency
team dropback efficiency
team pass volume/tendency
QB quality/continuity
target competition
depth chart role
draft capital / age curve
```
