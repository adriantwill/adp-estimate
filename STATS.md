# Environment Stats

Derived team environment stats to build from nflverse and FTN data.

## From nflverse PBP

Source:

```text
https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_YEAR.csv.gz
```

### Pass Rate

```text
pass_rate = pass_attempt / (pass_attempt + rush_attempt)
```

Use offensive plays only. Exclude kneels, spikes, special teams, and deleted plays if present.

### Neutral Pass Rate

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

### Plays Per Game

```text
plays_per_game = offensive plays / games
```

Use plays where `play_type` is `pass` or `run`.

### Pace

Two useful versions:

```text
pace = offensive plays / minutes of possession
```

or:

```text
pace = average seconds between offensive plays
```

Lower seconds-per-play means faster pace.

### Red Zone Rate

```text
red_zone_rate = plays with yardline_100 <= 20 / total offensive plays
```

### Red Zone Pass Rate

```text
red_zone_pass_rate = pass attempts inside 20 / offensive plays inside 20
```

Filter:

```text
yardline_100 <= 20
play_type in ["pass", "run"]
```

### First Down Pass Rate

```text
first_down_pass_rate = first-down pass attempts / first-down offensive plays
```

Filter:

```text
down == 1
play_type in ["pass", "run"]
```

### Pass Over Expected

```text
pass_oe = average pass_oe
```

Use nflverse PBP column `pass_oe`.

### Scoring Environment

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

### RBSDM-Style Team Efficiency

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

## From stats_player

Source:

```text
https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_YEAR.csv
```

### Target Concentration

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

## From schedules/games.csv

Source:

```text
https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv
```

### Head Coach Tendency

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

### Weather / Scoring Context

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

## From FTN Charting

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
