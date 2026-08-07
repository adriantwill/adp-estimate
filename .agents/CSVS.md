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

## Derived Environment Stats

Derived team environment stats to build from nflverse and FTN data.

### From nflverse PBP

Source:

```text
https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_YEAR.csv.gz
```

#### Pass Rate

```text
pass_rate = pass_attempt / (pass_attempt + rush_attempt)
```

Use offensive plays only. Exclude kneels, spikes, special teams, and deleted plays if present.

#### Neutral Pass Rate

```text
neutral_pass_rate = pass attempts / offensive plays
```

Filter to neutral situations:

```text
qtr <= 3
abs(score_differential) <= 8
down in [1, 2]
play_type in ["pass", "run"]
```

#### Plays Per Game

```text
plays_per_game = offensive plays / games
```

Use plays where `play_type` is `pass` or `run`.

#### Pace

Two useful versions:

```text
pace = offensive plays / minutes of possession
```

or:

```text
pace = average seconds between offensive plays
```

Lower seconds-per-play means faster pace.

#### Red Zone Rate

```text
red_zone_rate = plays with yardline_100 <= 20 / total offensive plays
```

#### Red Zone Pass Rate

```text
red_zone_pass_rate = pass attempts inside 20 / offensive plays inside 20
```

Filter:

```text
yardline_100 <= 20
play_type in ["pass", "run"]
```

#### First Down Pass Rate

```text
first_down_pass_rate = first-down pass attempts / first-down offensive plays
```

Filter:

```text
down == 1
play_type in ["pass", "run"]
```

#### Pass Over Expected

```text
pass_oe = average pass_oe
```

Use nflverse PBP column `pass_oe`.

#### Scoring Environment

Useful pieces:

```text
points_per_game
offensive_epa_per_play
touchdown_rate
red_zone_trips_per_game
```

Possible formulas:

```text
points_per_game = total team points / games
offensive_epa_per_play = sum(epa) / offensive plays
touchdown_rate = offensive touchdowns / offensive plays
red_zone_trips_per_game = drives with any play yardline_100 <= 20 / games
```

#### RBSDM-Style Team Efficiency

These replace the `rbstm_offense/rbstm_YEAR.csv` files if deriving directly from nflverse PBP.

```text
epa_per_play = mean(epa)
success_rate = mean(success)
dropback_epa = mean(epa where qb_dropback == 1)
rush_epa = mean(epa where rush_attempt == 1)
dropback_success_rate = mean(success where qb_dropback == 1)
rush_success_rate = mean(success where rush_attempt == 1)
```

Recommended filters:

```text
season_type == "REG"
play_type in ["pass", "run"]
posteam is not null
play_deleted != 1
qb_kneel != 1
qb_spike != 1
```

Column mapping to current RBSDM files:

```text
EPA/play     -> epa_per_play
Success Rate -> success_rate
Dropback EPA -> dropback_epa
Rush EPA     -> rush_epa
Dropback SR  -> dropback_success_rate
Rush SR      -> rush_success_rate
```

### From stats_player

Source:

```text
https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_YEAR.csv
```

#### Target Concentration

Useful pieces:

```text
top_1_wr_target_share
top_2_wr_target_share
top_3_wr_target_share
wr_target_share
te_target_share
wopr_concentration
```

Possible formulas:

```text
top_1_wr_target_share = max WR target_share on team
top_2_wr_target_share = sum top 2 WR target_share on team
top_3_wr_target_share = sum top 3 WR target_share on team
wr_target_share = sum WR target_share on team
te_target_share = sum TE target_share on team
wopr_concentration = sum top 2 WOPR on team
```

Useful columns:

```text
recent_team
position
targets
target_share
air_yards_share
wopr
```

### From schedules/games.csv

Source:

```text
https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv
```

#### Head Coach Tendency

Group PBP-derived stats by `home_coach` and `away_coach`.

Useful coach-level stats:

```text
coach_neutral_pass_rate
coach_pass_oe
coach_plays_per_game
coach_red_zone_pass_rate
coach_first_down_pass_rate
```

For each game, assign the correct coach:

```text
if posteam == home_team: coach = home_coach
if posteam == away_team: coach = away_coach
```

#### Weather / Scoring Context

Useful columns:

```text
roof
surface
temp
wind
total_line
spread_line
```

Useful derived stats:

```text
indoor_game = roof in ["dome", "closed"]
bad_weather = wind >= 15 or temp <= 32
implied_team_total = game_total / 2 +/- spread adjustment
```

### From FTN Charting

Source:

```text
https://github.com/nflverse/nflverse-data/releases/download/ftn_charting/ftn_charting_YEAR.csv
```

Useful team scheme rates:

```text
motion_rate = mean(is_motion)
play_action_rate = mean(is_play_action)
screen_rate = mean(is_screen_pass)
rpo_rate = mean(is_rpo)
no_huddle_rate = mean(is_no_huddle)
trick_play_rate = mean(is_trick_play)
qb_out_of_pocket_rate = mean(is_qb_out_of_pocket)
```

Useful structure stats:

```text
avg_offense_backfield = average n_offense_backfield
avg_defense_box = average n_defense_box faced
```

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
