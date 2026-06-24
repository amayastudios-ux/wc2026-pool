#!/usr/bin/env python3
"""
FIFA World Cup 2026 - Pool Tracker Data Updater
Primary source: ESPN public scoreboard + standings APIs (no key needed)
Fallback: API-Football v3 (requires API_FOOTBALL_KEY secret)
Run every 3 hours via GitHub Actions.
"""
import json, os, sys, requests
from datetime import datetime, timezone, timedelta

API_KEY   = os.environ.get("API_FOOTBALL_KEY", "")
DATA_FILE = "data.json"
TOURNEY_START = datetime(2026, 6, 11, tzinfo=timezone.utc)

TEAM_NAME_MAP = {
    "Mexico": "Mexico", "South Korea": "Korea Republic",
    "Korea Republic": "Korea Republic", "Republic of Korea": "Korea Republic",
    "Czech Republic": "Czechia", "Czechia": "Czechia",
    "South Africa": "South Africa", "Canada": "Canada",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Bosnia & Herzegovina": "Bosnia & Herzegovina",
    "Bosnia-Herzegovina": "Bosnia & Herzegovina",
    "Qatar": "Qatar", "Switzerland": "Switzerland",
    "Brazil": "Brazil", "Morocco": "Morocco", "Haiti": "Haiti",
    "Scotland": "Scotland", "United States": "USA", "USA": "USA",
    "Paraguay": "Paraguay", "Australia": "Australia",
    "Turkey": "Turkiye", "Turkiye": "Turkiye",
    "Germany": "Germany", "Curacao": "Curacao",
    "Ivory Coast": "Ivory Coast", "Cote d'Ivoire": "Ivory Coast",
    "Ecuador": "Ecuador", "Netherlands": "Netherlands",
    "Japan": "Japan", "Sweden": "Sweden", "Tunisia": "Tunisia",
    "Belgium": "Belgium", "Egypt": "Egypt", "Iran": "Iran",
    "New Zealand": "New Zealand", "Spain": "Spain",
    "Cape Verde": "Cabo Verde", "Cabo Verde": "Cabo Verde",
    "Saudi Arabia": "Saudi Arabia", "Uruguay": "Uruguay",
    "France": "France", "Senegal": "Senegal", "Iraq": "Iraq",
    "Norway": "Norway", "Argentina": "Argentina", "Algeria": "Algeria",
    "Austria": "Austria", "Jordan": "Jordan", "Portugal": "Portugal",
    "DR Congo": "Congo DR", "Congo DR": "Congo DR",
    "Democratic Republic of the Congo": "Congo DR",
    "Uzbekistan": "Uzbekistan", "Colombia": "Colombia",
    "England": "England", "Croatia": "Croatia", "Ghana": "Ghana",
    "Panama": "Panama",
}

SLUG_TO_ROUND = {
    "group-stage":   "Group Stage",
    "round-of-32":   "Round of 32",
    "round-of-16":   "Round of 16",
    "quarterfinals": "Quarter-finals",
    "semifinals":    "Semi-finals",
    "third-place":   "3rd Place Match",
    "final":         "Final",
}

ROUND_POINTS = {
    "group stage": 0, "round of 32": 1, "round of 16": 2,
    "quarter-finals": 3, "semi-finals": 4, "runner-up": 5, "champion": 6,
}

# Groups lookup (ASCII keys only, no special chars)
TEAM_GROUP = {
    "Mexico": "A", "South Africa": "A", "Korea Republic": "A", "Czechia": "A",
    "Canada": "B", "Bosnia & Herzegovina": "B", "Qatar": "B", "Switzerland": "B",
    "Brazil": "C", "Morocco": "C", "Haiti": "C", "Scotland": "C",
    "USA": "D", "Paraguay": "D", "Australia": "D", "Turkiye": "D",
    "Germany": "E", "Curacao": "E", "Ivory Coast": "E", "Ecuador": "E",
    "Netherlands": "F", "Japan": "F", "Sweden": "F", "Tunisia": "F",
    "Belgium": "G", "Egypt": "G", "Iran": "G", "New Zealand": "G",
    "Spain": "H", "Cabo Verde": "H", "Saudi Arabia": "H", "Uruguay": "H",
    "France": "I", "Senegal": "I", "Iraq": "I", "Norway": "I",
    "Argentina": "J", "Algeria": "J", "Austria": "J", "Jordan": "J",
    "Portugal": "K", "Congo DR": "K", "Uzbekistan": "K", "Colombia": "K",
    "England": "L", "Croatia": "L", "Ghana": "L", "Panama": "L",
}

# Flag emoji map (stored as unicode escapes to avoid encoding issues)
TEAM_FLAG = {
    "Mexico": "\U0001f1f2\U0001f1fd",
    "South Africa": "\U0001f1ff\U0001f1e6",
    "Korea Republic": "\U0001f1f0\U0001f1f7",
    "Czechia": "\U0001f1e8\U0001f1ff",
    "Canada": "\U0001f1e8\U0001f1e6",
    "Bosnia & Herzegovina": "\U0001f1e7\U0001f1e6",
    "Qatar": "\U0001f1f6\U0001f1e6",
    "Switzerland": "\U0001f1e8\U0001f1ed",
    "Brazil": "\U0001f1e7\U0001f1f7",
    "Morocco": "\U0001f1f2\U0001f1e6",
    "Haiti": "\U0001f1ed\U0001f1f9",
    "Scotland": "\U0001f3f4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "USA": "\U0001f1fa\U0001f1f8",
    "Paraguay": "\U0001f1f5\U0001f1fe",
    "Australia": "\U0001f1e6\U0001f1fa",
    "Turkiye": "\U0001f1f9\U0001f1f7",
    "Germany": "\U0001f1e9\U0001f1ea",
    "Curacao": "\U0001f1e8\U0001f1fc",
    "Ivory Coast": "\U0001f1e8\U0001f1ee",
    "Ecuador": "\U0001f1ea\U0001f1e8",
    "Netherlands": "\U0001f1f3\U0001f1f1",
    "Japan": "\U0001f1ef\U0001f1f5",
    "Sweden": "\U0001f1f8\U0001f1ea",
    "Tunisia": "\U0001f1f9\U0001f1f3",
    "Belgium": "\U0001f1e7\U0001f1ea",
    "Egypt": "\U0001f1ea\U0001f1ec",
    "Iran": "\U0001f1ee\U0001f1f7",
    "New Zealand": "\U0001f1f3\U0001f1ff",
    "Spain": "\U0001f1ea\U0001f1f8",
    "Cabo Verde": "\U0001f1e8\U0001f1fb",
    "Saudi Arabia": "\U0001f1f8\U0001f1e6",
    "Uruguay": "\U0001f1fa\U0001f1fe",
    "France": "\U0001f1eb\U0001f1f7",
    "Senegal": "\U0001f1f8\U0001f1f3",
    "Iraq": "\U0001f1ee\U0001f1f6",
    "Norway": "\U0001f1f3\U0001f1f4",
    "Argentina": "\U0001f1e6\U0001f1f7",
    "Algeria": "\U0001f1e9\U0001f1ff",
    "Austria": "\U0001f1e6\U0001f1f9",
    "Jordan": "\U0001f1ef\U0001f1f4",
    "Portugal": "\U0001f1f5\U0001f1f9",
    "Congo DR": "\U0001f1e8\U0001f1e9",
    "Uzbekistan": "\U0001f1fa\U0001f1ff",
    "Colombia": "\U0001f1e8\U0001f1f4",
    "England": "\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "Croatia": "\U0001f1ed\U0001f1f7",
    "Ghana": "\U0001f1ec\U0001f1ed",
    "Panama": "\U0001f1f5\U0001f1e6",
}

# Canonical display names (with special chars) - internal key -> display name
DISPLAY_NAME = {
    "Turkiye": "Türkiye",
    "Curacao": "Curaçao",
    "Ivory Coast": "Côte d'Ivoire",
}

# Teams confirmed eliminated by admin -- always preserved
HARDCODED_ELIMINATED = {"Haiti", "Türkiye", "Tunisia"}


def normalise(name):
    """Normalise ESPN team name to internal key."""
    return TEAM_NAME_MAP.get(name, name)


def display(internal):
    """Convert internal key to display name (handles special chars)."""
    return DISPLAY_NAME.get(internal, internal)


# -- ESPN fetch ----------------------------------------------------------------

def fetch_espn_date(date_str):
    url = (f"https://site.api.espn.com/apis/site/v2/sports/soccer"
           f"/fifa.world/scoreboard?dates={date_str}")
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code != 200:
            return []
        return resp.json().get("events", [])
    except Exception as ex:
        print(f"  ESPN {date_str}: {ex}")
        return []


def fetch_all_espn_results():
    now  = datetime.now(timezone.utc)
    day  = TOURNEY_START
    seen = set()
    results = []

    while day.date() <= now.date():
        date_str = day.strftime("%Y%m%d")
        events   = fetch_espn_date(date_str)
        for e in events:
            comp   = e.get("competitions", [{}])[0]
            status = comp.get("status", {}).get("type", {})
            if status.get("state") != "post":
                continue
            competitors = comp.get("competitors", [])
            home_c = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away_c = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not home_c or not away_c:
                continue
            home_name  = normalise(home_c["team"]["displayName"])
            away_name  = normalise(away_c["team"]["displayName"])
            home_score = int(home_c.get("score", 0) or 0)
            away_score = int(away_c.get("score", 0) or 0)
            slug       = e.get("season", {}).get("slug", "group-stage")
            rnd_label  = SLUG_TO_ROUND.get(slug, "Group Stage")
            key = f"{home_name}|{away_name}|{date_str}"
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "home":      display(home_name),
                "away":      display(away_name),
                "homeScore": home_score,
                "awayScore": away_score,
                "round":     rnd_label,
                "slug":      slug,
                "_home_key": home_name,
                "_away_key": away_name,
            })
        day += timedelta(days=1)

    return results


# -- Group standings -----------------------------------------------------------

def fetch_espn_standings():
    """Fetch group standings from ESPN standings API (primary)."""
    url = "https://site.api.espn.com/apis/v2/sports/soccer/fifa.world/standings"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code != 200:
            print(f"  ESPN standings API: HTTP {resp.status_code}")
            return {}
        data = resp.json()
    except Exception as ex:
        print(f"  ESPN standings API: {ex}")
        return {}

    standings = {}
    for child in data.get("children", []):
        grp_name = child.get("name", "")
        if not grp_name.startswith("Group "):
            continue
        grp = grp_name.split(" ", 1)[1]
        entries = child.get("standings", {}).get("entries", [])
        ranked = []
        for e in entries:
            internal  = normalise(e["team"]["displayName"])
            team_disp = display(internal)
            stats = {s["name"]: s.get("value", 0) or 0 for s in e.get("stats", [])}
            ranked.append({
                "team":      team_disp,
                "pts":       int(stats.get("points", 0)),
                "gd":        int(stats.get("pointDifferential", 0)),
                "gf":        int(stats.get("pointsFor", 0)),
                "ga":        int(stats.get("pointsAgainst", 0)),
                "played":    int(stats.get("gamesPlayed", 0)),
                "w":         int(stats.get("wins", 0)),
                "d":         int(stats.get("ties", 0)),
                "l":         int(stats.get("losses", 0)),
                "_rank":     int(stats.get("rank", 99)),
                "_key":      internal,
                "_advanced": int(stats.get("advanced", 0)),
                "_elim":     int(stats.get("eliminated", 0)),
            })
        ranked.sort(key=lambda x: x["_rank"])
        for t in ranked:
            del t["_rank"]
        standings[grp] = ranked

    return standings


def compute_group_standings(results):
    """Fallback: compute standings from scoreboard results."""
    gdata = {}
    for r in results:
        if r.get("slug", "group-stage") != "group-stage":
            continue
        hk, ak = r.get("_home_key", r["home"]), r.get("_away_key", r["away"])
        hs, as_ = r["homeScore"], r["awayScore"]
        grp = TEAM_GROUP.get(hk) or TEAM_GROUP.get(ak)
        if not grp:
            continue
        if grp not in gdata:
            gdata[grp] = {}
        for k, disp in [(hk, r["home"]), (ak, r["away"])]:
            if k not in gdata[grp]:
                gdata[grp][k] = {"team": disp, "pts": 0, "gd": 0, "gf": 0,
                                  "ga": 0, "played": 0, "w": 0, "d": 0, "l": 0, "_key": k}
        s = gdata[grp]
        s[hk]["gf"] += hs; s[hk]["ga"] += as_
        s[hk]["gd"] += hs - as_; s[hk]["played"] += 1
        s[ak]["gf"] += as_; s[ak]["ga"] += hs
        s[ak]["gd"] += as_ - hs; s[ak]["played"] += 1
        if hs > as_:
            s[hk]["pts"] += 3; s[hk]["w"] += 1; s[ak]["l"] += 1
        elif as_ > hs:
            s[ak]["pts"] += 3; s[ak]["w"] += 1; s[hk]["l"] += 1
        else:
            s[hk]["pts"] += 1; s[hk]["d"] += 1
            s[ak]["pts"] += 1; s[ak]["d"] += 1

    standings = {}
    for grp in sorted(gdata.keys()):
        ranked = sorted(gdata[grp].values(),
                        key=lambda x: (-x["pts"], -x["gd"], -x["gf"]))
        standings[grp] = ranked
    return standings


# -- Qualifier determination --------------------------------------------------

def determine_qualifiers(standings):
    winners, runnersup, thirds, math_elim = [], [], [], []

    for grp, ranked in standings.items():
        get_key = lambda t: t.get("_key", t["team"])
        get_flag = lambda t: TEAM_FLAG.get(get_key(t), "")

        # confirmed = played all 3 games OR ESPN flagged as mathematically advanced
        def confirmed(t):
            return t["played"] == 3 or t.get("_advanced", 0) == 1

        if len(ranked) >= 1 and confirmed(ranked[0]):
            t = ranked[0]
            winners.append({"team": t["team"], "group": grp, "flag": get_flag(t),
                             "pts": t["pts"], "gd": t["gd"], "gf": t["gf"]})

        if len(ranked) >= 2 and confirmed(ranked[1]):
            t = ranked[1]
            runnersup.append({"team": t["team"], "group": grp, "flag": get_flag(t),
                               "pts": t["pts"], "gd": t["gd"], "gf": t["gf"]})

        if len(ranked) >= 3 and ranked[2]["played"] == 3:
            t = ranked[2]
            thirds.append({"team": t["team"], "group": grp, "flag": get_flag(t),
                           "pts": t["pts"], "gd": t["gd"], "gf": t["gf"]})

        # Mathematical elimination before MD3
        if len(ranked) >= 4:
            third_pts = ranked[2]["pts"]
            for i in range(3, len(ranked)):
                t = ranked[i]
                remaining = 3 - t["played"]
                if t["pts"] + remaining * 3 < third_pts:
                    math_elim.append(get_key(t))

    third_qualified, third_eliminated = [], []
    if len(thirds) == 12:
        ranked_thirds = sorted(thirds,
                               key=lambda x: (-x["pts"], -x["gd"], -x["gf"]))
        third_qualified  = ranked_thirds[:8]
        third_eliminated = ranked_thirds[8:]

    return {
        "winners":          winners,
        "runnersup":        runnersup,
        "third_qualified":  third_qualified,
        "third_eliminated": third_eliminated,
        "math_eliminated":  math_elim,
        "r32_count":        len(winners) + len(runnersup) + len(third_qualified),
    }


# -- Team status builder ------------------------------------------------------

def build_teams(results):
    """Build base teams dict from known teams; knockout results update status."""
    teams = {}
    for internal, grp in TEAM_GROUP.items():
        disp = display(internal)
        teams[disp] = {
            "group":        grp,
            "flag":         TEAM_FLAG.get(internal, ""),
            "status":       "active",
            "pts":          0,
            "roundReached": None,
        }

    for r in results:
        home, away = r["home"], r["away"]
        hs, as_    = r["homeScore"], r["awayScore"]
        slug       = r.get("slug", "group-stage")
        rnd_l      = r["round"].lower()

        if slug == "group-stage":
            continue

        rnd_key = None
        for k in ROUND_POINTS:
            if k in rnd_l:
                rnd_key = k
                break
        if rnd_key is None:
            continue

        if hs > as_:
            winner, loser = home, away
        elif as_ > hs:
            winner, loser = away, home
        else:
            continue

        if "final" in rnd_l and "3rd" not in rnd_l and "place" not in rnd_l:
            if winner in teams:
                teams[winner]["pts"]          = ROUND_POINTS["champion"]
                teams[winner]["status"]       = "champion"
                teams[winner]["roundReached"] = "Champion"
            if loser in teams:
                teams[loser]["pts"]           = ROUND_POINTS["runner-up"]
                teams[loser]["status"]        = "eliminated"
                teams[loser]["roundReached"]  = "Runner-up"
        else:
            if loser in teams and teams[loser]["pts"] == 0:
                teams[loser]["pts"]          = ROUND_POINTS[rnd_key]
                teams[loser]["status"]       = "eliminated"
                teams[loser]["roundReached"] = r["round"]

    return teams


def apply_group_eliminations(teams, standings, qualifiers):
    # 4th-place teams after MD3
    for grp, ranked in standings.items():
        if len(ranked) >= 4 and ranked[3]["played"] == 3:
            name = ranked[3]["team"]
            if name in teams and teams[name]["status"] == "active":
                teams[name]["status"]       = "eliminated"
                teams[name]["roundReached"] = "Group Stage"

    # Bottom 4 third-place teams
    for t in qualifiers.get("third_eliminated", []):
        name = t["team"]
        if name in teams and teams[name]["status"] == "active":
            teams[name]["status"]       = "eliminated"
            teams[name]["roundReached"] = "Group Stage"

    # Mathematically eliminated
    for key in qualifiers.get("math_eliminated", []):
        name = display(key)
        if name in teams and teams[name]["status"] == "active":
            teams[name]["status"]       = "eliminated"
            teams[name]["roundReached"] = "Group Stage"

    # ESPN-flagged mathematically eliminated (group stage)
    for grp, ranked in standings.items():
        for t in ranked:
            if t.get("_elim", 0) == 1:
                name = t["team"]
                if name in teams and teams[name]["status"] == "active":
                    teams[name]["status"]       = "eliminated"
                    teams[name]["roundReached"] = "Group Stage"

    # Hardcoded admin-confirmed eliminations
    for name in HARDCODED_ELIMINATED:
        if name in teams:
            teams[name]["status"]       = "eliminated"
            teams[name]["roundReached"] = (teams[name].get("roundReached")
                                           or "Group Stage")

    return teams


# -- Stage / matchday detection -----------------------------------------------

def determine_stage_matchday(results, standings):
    slugs = [r.get("slug", "group-stage") for r in results]
    knockout_slugs = [s for s in slugs if s != "group-stage"]

    if "final"         in knockout_slugs: return "Final",          3
    if "semifinals"    in knockout_slugs: return "Semi-finals",    3
    if "quarterfinals" in knockout_slugs: return "Quarter-finals", 3
    if "round-of-16"   in knockout_slugs: return "Round of 16",    3
    if "round-of-32"   in knockout_slugs: return "Round of 32",    3

    if standings:
        max_played = max(
            (t["played"] for grp in standings.values() for t in grp),
            default=0
        )
        # MD3 window is Jun 24-27; floor matchday at 3 if we're in that window
        # and at least MD2 is done (max_played >= 2)
        today = datetime.now(timezone.utc).date()
        md3_start = datetime(2026, 6, 24, tzinfo=timezone.utc).date()
        md3_end   = datetime(2026, 6, 27, tzinfo=timezone.utc).date()
        if md3_start <= today <= md3_end and max_played >= 2:
            max_played = max(max_played, 3)
        return "Group Stage", max(max_played, 1)

    games = {}
    for r in results:
        if r.get("slug") == "group-stage":
            games[r["home"]] = games.get(r["home"], 0) + 1
            games[r["away"]] = games.get(r["away"], 0) + 1
    return "Group Stage", max(games.values(), default=1)


# -- Persistence --------------------------------------------------------------

def load_existing():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# -- Main ---------------------------------------------------------------------

def main():
    print("Starting update...")
    existing = load_existing()

    print("  Fetching ESPN scoreboard results...")
    espn_results = fetch_all_espn_results()
    print(f"  ESPN completed matches: {len(espn_results)}")

    if not espn_results and not existing:
        print("  No data available -- skipping.")
        return

    # Build base team dict (knockout results update status)
    teams = build_teams(espn_results or [])

    # Preserve existing knockout-round progress
    if existing:
        for name, ex_t in existing.get("teams", {}).items():
            if name in teams and ex_t.get("pts", 0) > 0 and teams[name]["pts"] == 0:
                teams[name]["pts"]          = ex_t["pts"]
                teams[name]["status"]       = ex_t["status"]
                teams[name]["roundReached"] = ex_t.get("roundReached")

    # Group standings -- ESPN API first, scoreboard fallback
    print("  Fetching ESPN group standings...")
    standings = fetch_espn_standings()
    if standings:
        print(f"  ESPN standings API: {len(standings)} groups loaded")
    else:
        print("  ESPN standings API unavailable -- computing from results...")
        standings = compute_group_standings(espn_results or [])
        print(f"  Computed standings: {len(standings)} groups")

    qualifiers = determine_qualifiers(standings)
    teams = apply_group_eliminations(teams, standings, qualifiers)

    # Strip internal _key fields from standings before writing
    clean_standings = {}
    for grp, ranked in standings.items():
        clean_standings[grp] = [{k: v for k, v in t.items() if not k.startswith("_")}
                                 for t in ranked]

    stage, matchday = determine_stage_matchday(espn_results or [], standings)
    elim_count   = sum(1 for t in teams.values() if t["status"] == "eliminated")
    recent_clean = [{k: v for k, v in r.items() if not k.startswith("_")}
                    for r in (espn_results or [])]

    out = {
        "meta": {
            "lastUpdated":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stage":           stage,
            "matchday":        matchday,
            "eliminatedCount": elim_count,
            "recentResults":   recent_clean,
        },
        "standings":  clean_standings,
        "qualifiers": qualifiers,
        "teams":      teams,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"  Stage: {stage} / MD{matchday} / Eliminated: {elim_count} / R32 qualified: {qualifiers['r32_count']}")
    print(f"  Group winners  ({len(qualifiers['winners'])}): "
          + ", ".join(q["team"] for q in qualifiers["winners"]))
    print(f"  Runners-up     ({len(qualifiers['runnersup'])}): "
          + ", ".join(q["team"] for q in qualifiers["runnersup"]))
    print(f"  Best 3rd       ({len(qualifiers['third_qualified'])}): "
          + ", ".join(q["team"] for q in qualifiers["third_qualified"]))
    print("  data.json updated.")


if __name__ == "__main__":
    main()
