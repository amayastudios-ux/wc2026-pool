#!/usr/bin/env python3
"""
FIFA World Cup 2026 — Pool Tracker Data Updater
Fetches live results from API-Football and writes data.json.
Run daily via GitHub Actions.
"""
import json, os, sys, requests
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY    = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST   = "v3.football.api-sports.io"
LEAGUE_ID  = 1       # FIFA World Cup
SEASON     = 2026
DATA_FILE  = "data.json"

# ── Canonical name map (API name → our key) ─────────────────────────────────
TEAM_NAME_MAP = {
    # Group A
    "Mexico":                 "Mexico",
    "South Korea":            "Korea Republic",
    "Korea Republic":         "Korea Republic",
    "Republic of Korea":      "Korea Republic",
    "Czech Republic":         "Czechia",
    "Czechia":                "Czechia",
    "South Africa":           "South Africa",
    # Group B
    "Canada":                 "Canada",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Bosnia & Herzegovina":   "Bosnia & Herzegovina",
    "Qatar":                  "Qatar",
    "Switzerland":            "Switzerland",
    # Group C
    "Brazil":                 "Brazil",
    "Morocco":                "Morocco",
    "Haiti":                  "Haiti",
    "Scotland":               "Scotland",
    # Group D
    "United States":          "USA",
    "USA":                    "USA",
    "Paraguay":               "Paraguay",
    "Australia":              "Australia",
    "Turkey":                 "Türkiye",
    "Türkiye":                "Türkiye",
    # Group E
    "Germany":                "Germany",
    "Curacao":                "Curaçao",
    "Curaçao":                "Curaçao",
    "Ivory Coast":            "Côte d'Ivoire",
    "Cote d'Ivoire":          "Côte d'Ivoire",
    "Côte d'Ivoire":          "Côte d'Ivoire",
    "Ecuador":                "Ecuador",
    # Group F
    "Netherlands":            "Netherlands",
    "Japan":                  "Japan",
    "Sweden":                 "Sweden",
    "Tunisia":                "Tunisia",
    # Group G
    "Belgium":                "Belgium",
    "Egypt":                  "Egypt",
    "Iran":                   "Iran",
    "New Zealand":            "New Zealand",
    # Group H
    "Spain":                  "Spain",
    "Cape Verde":             "Cabo Verde",
    "Cabo Verde":             "Cabo Verde",
    "Saudi Arabia":           "Saudi Arabia",
    "Uruguay":                "Uruguay",
    # Group I
    "France":                 "France",
    "Senegal":                "Senegal",
    "Iraq":                   "Iraq",
    "Norway":                 "Norway",
    # Group J
    "Argentina":              "Argentina",
    "Algeria":                "Algeria",
    "Austria":                "Austria",
    "Jordan":                 "Jordan",
    # Group K
    "Portugal":               "Portugal",
    "DR Congo":               "Congo DR",
    "Congo DR":               "Congo DR",
    "Democratic Republic of the Congo": "Congo DR",
    "Uzbekistan":             "Uzbekistan",
    "Colombia":               "Colombia",
    # Group L
    "England":                "England",
    "Croatia":                "Croatia",
    "Ghana":                  "Ghana",
    "Panama":                 "Panama",
}

# ── Round → pool pts ────────────────────────────────────────────────────────
ROUND_POINTS = {
    "group stage":    0,
    "round of 32":    1,
    "round of 16":    2,
    "quarter-finals": 3,
    "semi-finals":    4,
    "runner-up":      5,   # synthetic: losing finalist
    "champion":       6,   # synthetic: winner
}

# ── Team data template ───────────────────────────────────────────────────────
TEAM_TEMPLATE = {
    "Mexico":                 {"group":"A","flag":"🇲🇽"},
    "South Africa":           {"group":"A","flag":"🇿🇦"},
    "Korea Republic":         {"group":"A","flag":"🇰🇷"},
    "Czechia":                {"group":"A","flag":"🇨🇿"},
    "Canada":                 {"group":"B","flag":"🇨🇦"},
    "Bosnia & Herzegovina":   {"group":"B","flag":"🇧🇦"},
    "Qatar":                  {"group":"B","flag":"🇶🇦"},
    "Switzerland":            {"group":"B","flag":"🇨🇭"},
    "Brazil":                 {"group":"C","flag":"🇧🇷"},
    "Morocco":                {"group":"C","flag":"🇲🇦"},
    "Haiti":                  {"group":"C","flag":"🇭🇹"},
    "Scotland":               {"group":"C","flag":"🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    "USA":                    {"group":"D","flag":"🇺🇸"},
    "Paraguay":               {"group":"D","flag":"🇵🇾"},
    "Australia":              {"group":"D","flag":"🇦🇺"},
    "Türkiye":                {"group":"D","flag":"🇹🇷"},
    "Germany":                {"group":"E","flag":"🇩🇪"},
    "Curaçao":                {"group":"E","flag":"🇨🇼"},
    "Côte d'Ivoire":          {"group":"E","flag":"🇨🇮"},
    "Ecuador":                {"group":"E","flag":"🇪🇨"},
    "Netherlands":            {"group":"F","flag":"🇳🇱"},
    "Japan":                  {"group":"F","flag":"🇯🇵"},
    "Sweden":                 {"group":"F","flag":"🇸🇪"},
    "Tunisia":                {"group":"F","flag":"🇹🇳"},
    "Belgium":                {"group":"G","flag":"🇧🇪"},
    "Egypt":                  {"group":"G","flag":"🇪🇬"},
    "Iran":                   {"group":"G","flag":"🇮🇷"},
    "New Zealand":            {"group":"G","flag":"🇳🇿"},
    "Spain":                  {"group":"H","flag":"🇪🇸"},
    "Cabo Verde":             {"group":"H","flag":"🇨🇻"},
    "Saudi Arabia":           {"group":"H","flag":"🇸🇦"},
    "Uruguay":                {"group":"H","flag":"🇺🇾"},
    "France":                 {"group":"I","flag":"🇫🇷"},
    "Senegal":                {"group":"I","flag":"🇸🇳"},
    "Iraq":                   {"group":"I","flag":"🇮🇶"},
    "Norway":                 {"group":"I","flag":"🇳🇴"},
    "Argentina":              {"group":"J","flag":"🇦🇷"},
    "Algeria":                {"group":"J","flag":"🇩🇿"},
    "Austria":                {"group":"J","flag":"🇦🇹"},
    "Jordan":                 {"group":"J","flag":"🇯🇴"},
    "Portugal":               {"group":"K","flag":"🇵🇹"},
    "Congo DR":               {"group":"K","flag":"🇨🇩"},
    "Uzbekistan":             {"group":"K","flag":"🇺🇿"},
    "Colombia":               {"group":"K","flag":"🇨🇴"},
    "England":                {"group":"L","flag":"🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "Croatia":                {"group":"L","flag":"🇭🇷"},
    "Ghana":                  {"group":"L","flag":"🇬🇭"},
    "Panama":                 {"group":"L","flag":"🇵🇦"},
}


def api(endpoint, params=None):
    """Call API-Football and return parsed JSON."""
    if not API_KEY:
        print("⚠️  No API key — skipping live fetch.")
        return None
    url  = f"https://{API_HOST}/{endpoint}"
    hdrs = {"x-apisports-key": API_KEY}
    resp = requests.get(url, headers=hdrs, params=params or {}, timeout=20)
    if resp.status_code != 200:
        print(f"API error {resp.status_code}: {resp.text[:200]}")
        return None
    return resp.json()


def normalise(name):
    """Map API team name to our canonical key."""
    return TEAM_NAME_MAP.get(name, name)


def determine_stage(fixtures):
    """
    Walk all fixtures to find the highest completed round.
    Returns (stage_str, matchday_int).
    """
    round_order = [
        "group stage", "round of 32", "round of 16",
        "quarter-finals", "semi-finals", "3rd place match", "final",
    ]
    stage_seen  = {}  # round_lower → any finished?
    matchday    = 1

    for f in fixtures:
        rnd    = f.get("league", {}).get("round", "").lower()
        status = f.get("fixture", {}).get("status", {}).get("short", "")
        done   = status in ("FT", "AET", "PEN")

        if "group stage" in rnd:
            # try to parse matchday e.g. "Group Stage - 2"
            parts = rnd.split("-")
            if len(parts) > 1:
                try:
                    md = int(parts[-1].strip())
                    if done:
                        matchday = max(matchday, md)
                except ValueError:
                    pass
            if done:
                stage_seen["group stage"] = True
        else:
            for r in round_order:
                if r in rnd and done:
                    stage_seen[r] = True

    # Highest completed non-group round wins
    knockout_done = [r for r in round_order[1:] if stage_seen.get(r)]
    if knockout_done:
        last = knockout_done[-1]
        if last == "final":
            return "Final", matchday
        return last.title(), matchday
    if stage_seen.get("group stage"):
        return "Group Stage", matchday
    return "Group Stage", 1


def process_fixtures(fixtures):
    """
    Build team result dict:
      { canonical_name: {status, pts, roundReached, group, flag} }
    Also collect recent results for the schedule overlay.
    """
    teams = {}
    for t, meta in TEAM_TEMPLATE.items():
        teams[t] = {
            "group":        meta["group"],
            "flag":         meta["flag"],
            "status":       "active",
            "pts":          0,
            "roundReached": None,
        }

    recent_results = []  # list of {home, away, homeScore, awayScore, round}

    for f in fixtures:
        status = f.get("fixture", {}).get("status", {}).get("short", "")
        if status not in ("FT", "AET", "PEN"):
            continue  # not finished

        rnd_raw  = f.get("league", {}).get("round", "")
        rnd_low  = rnd_raw.lower()
        home_api = f.get("teams", {}).get("home", {}).get("name", "")
        away_api = f.get("teams", {}).get("away", {}).get("name", "")
        home_g   = f.get("goals", {}).get("home", 0) or 0
        away_g   = f.get("goals", {}).get("away", 0) or 0
        home_won = f.get("teams", {}).get("home", {}).get("winner", False)
        away_won = f.get("teams", {}).get("away", {}).get("winner", False)

        home = normalise(home_api)
        away = normalise(away_api)

        # Track recent results for schedule overlay
        recent_results.append({
            "home":      home,
            "away":      away,
            "homeScore": home_g,
            "awayScore": away_g,
            "round":     rnd_raw,
        })

        if "group stage" in rnd_low:
            continue  # group stage: elimination determined from standings

        # Knockout rounds
        rnd_key = None
        for k in ROUND_POINTS:
            if k in rnd_low:
                rnd_key = k
                break
        if rnd_key is None:
            continue

        # Loser is eliminated with pts for this round
        if home_won and home in teams:
            if away in teams and teams[away]["pts"] == 0:
                teams[away]["pts"]          = ROUND_POINTS[rnd_key]
                teams[away]["status"]       = "eliminated"
                teams[away]["roundReached"] = rnd_raw
        elif away_won and away in teams:
            if home in teams and teams[home]["pts"] == 0:
                teams[home]["pts"]          = ROUND_POINTS[rnd_key]
                teams[home]["status"]       = "eliminated"
                teams[home]["roundReached"] = rnd_raw

        # Final: give champion/runner-up pts
        if "final" in rnd_low and "3rd" not in rnd_low:
            winner = home if home_won else away
            loser  = away if home_won else home
            if winner in teams:
                teams[winner]["pts"]          = ROUND_POINTS["champion"]
                teams[winner]["status"]       = "champion"
                teams[winner]["roundReached"] = "Champion"
            if loser in teams:
                teams[loser]["pts"]           = ROUND_POINTS["runner-up"]
                teams[loser]["status"]        = "eliminated"
                teams[loser]["roundReached"]  = "Runner-up"

    return teams, recent_results


def process_standings(standings_data, teams):
    """
    Use group standings to eliminate 4th-place teams after group stage.
    Mark 3rd-place teams with status='third' (may qualify as best third-place).
    """
    if not standings_data:
        return

    for grp_standings in standings_data:
        # grp_standings is a list of team standing rows, sorted rank 1–4
        sorted_rows = sorted(grp_standings, key=lambda x: x.get("rank", 99))
        for row in sorted_rows:
            name_api = row.get("team", {}).get("name", "")
            name     = normalise(name_api)
            rank     = row.get("rank", 0)
            played   = row.get("all", {}).get("played", 0)

            if played < 3:
                continue  # group not finished yet
            if name not in teams:
                continue
            if teams[name]["status"] != "active":
                continue  # already processed in knockout

            if rank == 1 or rank == 2:
                teams[name]["status"] = "active"
                teams[name]["pts"]    = 1   # Group stage advancement pt
            elif rank == 3:
                teams[name]["status"] = "third"
                teams[name]["pts"]    = 0
            else:  # rank 4: eliminated
                teams[name]["status"] = "eliminated"
                teams[name]["pts"]    = 0
                teams[name]["roundReached"] = "Group Stage"


def load_existing():
    """Load existing data.json so we don't overwrite knockout pts on API fail."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting update…")

    existing = load_existing()

    # ── Fetch fixtures ──────────────────────────────────────────────────────
    fix_data = api("fixtures", {"league": LEAGUE_ID, "season": SEASON})
    if not fix_data:
        print("No fixture data — preserving existing data.json.")
        return

    fixtures = fix_data.get("response", [])
    print(f"  Fixtures fetched: {len(fixtures)}")

    # ── Fetch standings ─────────────────────────────────────────────────────
    stand_data = api("standings", {"league": LEAGUE_ID, "season": SEASON})
    standings  = []
    if stand_data:
        resp = stand_data.get("response", [])
        if resp:
            standings = resp[0].get("league", {}).get("standings", [])
            print(f"  Standings groups: {len(standings)}")

    # ── Process data ────────────────────────────────────────────────────────
    stage, matchday         = determine_stage(fixtures)
    teams, recent_results   = process_fixtures(fixtures)
    process_standings(standings, teams)

    # Preserve existing pts/status if API returned nothing new
    if existing:
        for name, ex_t in existing.get("teams", {}).items():
            if name in teams and teams[name]["pts"] == 0 and ex_t.get("pts", 0) > 0:
                teams[name]["pts"]          = ex_t["pts"]
                teams[name]["status"]       = ex_t["status"]
                teams[name]["roundReached"] = ex_t.get("roundReached")

    elim_count = sum(1 for t in teams.values() if t["status"] == "eliminated")

    out = {
        "meta": {
            "lastUpdated":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stage":         stage,
            "matchday":      matchday,
            "eliminatedCount": elim_count,
            "recentResults": recent_results[-20:],  # last 20 finished matches
        },
        "teams": teams,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"  Stage: {stage} · MD{matchday} · Eliminated: {elim_count}")
    print(f"  ✅ {DATA_FILE} updated.")


if __name__ == "__main__":
    main()
