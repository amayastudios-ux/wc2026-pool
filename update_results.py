#!/usr/bin/env python3
"""
FIFA World Cup 2026 — Pool Tracker Data Updater
Primary source: ESPN public scoreboard API (no key needed)
Fallback: API-Football v3 (requires API_FOOTBALL_KEY secret)
Run every 3 hours via GitHub Actions.
"""
import json, os, sys, requests
from datetime import datetime, timezone, timedelta

API_KEY   = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST  = "v3.football.api-sports.io"
LEAGUE_ID = 1
SEASON    = 2026
DATA_FILE = "data.json"
TOURNEY_START = datetime(2026, 6, 11, tzinfo=timezone.utc)

TEAM_NAME_MAP = {
    "Mexico": "Mexico", "South Korea": "Korea Republic",
    "Korea Republic": "Korea Republic", "Republic of Korea": "Korea Republic",
    "Czech Republic": "Czechia", "Czechia": "Czechia",
    "South Africa": "South Africa", "Canada": "Canada",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Bosnia & Herzegovina": "Bosnia & Herzegovina",
    "Qatar": "Qatar", "Switzerland": "Switzerland",
    "Brazil": "Brazil", "Morocco": "Morocco", "Haiti": "Haiti",
    "Scotland": "Scotland", "United States": "USA", "USA": "USA",
    "Paraguay": "Paraguay", "Australia": "Australia",
    "Turkey": "Türkiye", "Turkiye": "Türkiye",
    "Germany": "Germany", "Curacao": "Curaçao",
    "Ivory Coast": "Côte d'Ivoire", "Cote d'Ivoire": "Côte d'Ivoire",
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
    # Unicode variants
    "Ürkiye": "Türkiye", "Türkiye": "Türkiye",
    "Curaçao": "Curaçao", "Côte d'Ivoire": "Côte d'Ivoire",
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

TEAM_TEMPLATE = {
    "Mexico":               {"group":"A","flag":"\U0001f1f2\U0001f1fd"},
    "South Africa":         {"group":"A","flag":"\U0001f1ff\U0001f1e6"},
    "Korea Republic":       {"group":"A","flag":"\U0001f1f0\U0001f1f7"},
    "Czechia":              {"group":"A","flag":"\U0001f1e8\U0001f1ff"},
    "Canada":               {"group":"B","flag":"\U0001f1e8\U0001f1e6"},
    "Bosnia & Herzegovina": {"group":"B","flag":"\U0001f1e7\U0001f1e6"},
    "Qatar":                {"group":"B","flag":"\U0001f1f6\U0001f1e6"},
    "Switzerland":          {"group":"B","flag":"\U0001f1e8\U0001f1ed"},
    "Brazil":               {"group":"C","flag":"\U0001f1e7\U0001f1f7"},
    "Morocco":              {"group":"C","flag":"\U0001f1f2\U0001f1e6"},
    "Haiti":                {"group":"C","flag":"\U0001f1ed\U0001f1f9"},
    "Scotland":             {"group":"C","flag":"\U0001f3f4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f"},
    "USA":                  {"group":"D","flag":"\U0001f1fa\U0001f1f8"},
    "Paraguay":             {"group":"D","flag":"\U0001f1f5\U0001f1fe"},
    "Australia":            {"group":"D","flag":"\U0001f1e6\U0001f1fa"},
    "Türkiye":              {"group":"D","flag":"\U0001f1f9\U0001f1f7"},
    "Germany":              {"group":"E","flag":"\U0001f1e9\U0001f1ea"},
    "Curaçao":              {"group":"E","flag":"\U0001f1e8\U0001f1fc"},
    "Côte d'Ivoire":        {"group":"E","flag":"\U0001f1e8\U0001f1ee"},
    "Ecuador":              {"group":"E","flag":"\U0001f1ea\U0001f1e8"},
    "Netherlands":          {"group":"F","flag":"\U0001f1f3\U0001f1f1"},
    "Japan":                {"group":"F","flag":"\U0001f1ef\U0001f1f5"},
    "Sweden":               {"group":"F","flag":"\U0001f1f8\U0001f1ea"},
    "Tunisia":              {"group":"F","flag":"\U0001f1f9\U0001f1f3"},
    "Belgium":              {"group":"G","flag":"\U0001f1e7\U0001f1ea"},
    "Egypt":                {"group":"G","flag":"\U0001f1ea\U0001f1ec"},
    "Iran":                 {"group":"G","flag":"\U0001f1ee\U0001f1f7"},
    "New Zealand":          {"group":"G","flag":"\U0001f1f3\U0001f1ff"},
    "Spain":                {"group":"H","flag":"\U0001f1ea\U0001f1f8"},
    "Cabo Verde":           {"group":"H","flag":"\U0001f1e8\U0001f1fb"},
    "Saudi Arabia":         {"group":"H","flag":"\U0001f1f8\U0001f1e6"},
    "Uruguay":              {"group":"H","flag":"\U0001f1fa\U0001f1fe"},
    "France":               {"group":"I","flag":"\U0001f1eb\U0001f1f7"},
    "Senegal":              {"group":"I","flag":"\U0001f1f8\U0001f1f3"},
    "Iraq":                 {"group":"I","flag":"\U0001f1ee\U0001f1f6"},
    "Norway":               {"group":"I","flag":"\U0001f1f3\U0001f1f4"},
    "Argentina":            {"group":"J","flag":"\U0001f1e6\U0001f1f7"},
    "Algeria":              {"group":"J","flag":"\U0001f1e9\U0001f1ff"},
    "Austria":              {"group":"J","flag":"\U0001f1e6\U0001f1f9"},
    "Jordan":               {"group":"J","flag":"\U0001f1ef\U0001f1f4"},
    "Portugal":             {"group":"K","flag":"\U0001f1f5\U0001f1f9"},
    "Congo DR":             {"group":"K","flag":"\U0001f1e8\U0001f1e9"},
    "Uzbekistan":           {"group":"K","flag":"\U0001f1fa\U0001f1ff"},
    "Colombia":             {"group":"K","flag":"\U0001f1e8\U0001f1f4"},
    "England":              {"group":"L","flag":"\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f"},
    "Croatia":              {"group":"L","flag":"\U0001f1ed\U0001f1f7"},
    "Ghana":                {"group":"L","flag":"\U0001f1ec\U0001f1ed"},
    "Panama":               {"group":"L","flag":"\U0001f1f5\U0001f1e6"},
}

# Teams manually confirmed eliminated (e.g., by pool admin) — always preserved
HARDCODED_ELIMINATED = {"Haiti", "Türkiye", "Tunisia"}


def normalise(name):
    return TEAM_NAME_MAP.get(name, name)


# ── ESPN fetch ────────────────────────────────────────────────────────────────

def fetch_espn_date(date_str):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date_str}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code != 200:
            print(f"  ESPN {date_str}: HTTP {resp.status_code}")
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
            status = comp.get("status", {}).get("type", {}).get("detail", "")
            if status != "FT":
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
                "home":      home_name,
                "away":      away_name,
                "homeScore": home_score,
                "awayScore": away_score,
                "round":     rnd_label,
                "slug":      slug,
            })
        day += timedelta(days=1)

    return results


# ── Group standings ───────────────────────────────────────────────────────────

def compute_group_standings(results):
    """Build group standings from all completed group stage results."""
    gdata = {}
    for r in results:
        if r.get("slug", "group-stage") != "group-stage":
            continue
        home, away = r["home"], r["away"]
        hs, as_ = r["homeScore"], r["awayScore"]
        grp = (TEAM_TEMPLATE.get(home) or {}).get("group") or \
              (TEAM_TEMPLATE.get(away) or {}).get("group")
        if not grp:
            continue
        if grp not in gdata:
            gdata[grp] = {}
        for t in [home, away]:
            if t not in gdata[grp]:
                gdata[grp][t] = {"pts":0,"gd":0,"gf":0,"ga":0,"played":0,"w":0,"d":0,"l":0}
        s = gdata[grp]
        s[home]["gf"] += hs; s[home]["ga"] += as_
        s[home]["gd"] += hs - as_; s[home]["played"] += 1
        s[away]["gf"] += as_; s[away]["ga"] += hs
        s[away]["gd"] += as_ - hs; s[away]["played"] += 1
        if hs > as_:
            s[home]["pts"] += 3; s[home]["w"] += 1; s[away]["l"] += 1
        elif as_ > hs:
            s[away]["pts"] += 3; s[away]["w"] += 1; s[home]["l"] += 1
        else:
            s[home]["pts"] += 1; s[home]["d"] += 1
            s[away]["pts"] += 1; s[away]["d"] += 1

    standings = {}
    for grp in sorted(gdata.keys()):
        ranked = sorted(gdata[grp].items(),
                        key=lambda x: (-x[1]["pts"], -x[1]["gd"], -x[1]["gf"]))
        standings[grp] = [{"team": n, **st} for n, st in ranked]
    return standings


# ── Qualifier determination ───────────────────────────────────────────────────

def determine_qualifiers(standings):
    """
    Returns qualifiers dict with:
      winners        — group winners (played 3 games)
      runnersup      — group runners-up (played 3 games)
      third_qualified — best 8 of 12 third-place teams (only when all 12 done)
      third_eliminated — bottom 4 third-place teams
      math_eliminated — teams mathematically out before MD3
    """
    winners, runnersup, thirds = [], [], []
    math_elim = []

    for grp, ranked in standings.items():
        flag = lambda n: TEAM_TEMPLATE.get(n, {}).get("flag", "🏳")

        # 1st place
        if len(ranked) >= 1 and ranked[0]["played"] == 3:
            winners.append({"team": ranked[0]["team"], "group": grp,
                             "flag": flag(ranked[0]["team"]),
                             "pts": ranked[0]["pts"], "gd": ranked[0]["gd"], "gf": ranked[0]["gf"]})

        # 2nd place
        if len(ranked) >= 2 and ranked[1]["played"] == 3:
            runnersup.append({"team": ranked[1]["team"], "group": grp,
                               "flag": flag(ranked[1]["team"]),
                               "pts": ranked[1]["pts"], "gd": ranked[1]["gd"], "gf": ranked[1]["gf"]})

        # 3rd place
        if len(ranked) >= 3 and ranked[2]["played"] == 3:
            thirds.append({"team": ranked[2]["team"], "group": grp,
                           "flag": flag(ranked[2]["team"]),
                           "pts": ranked[2]["pts"], "gd": ranked[2]["gd"], "gf": ranked[2]["gf"]})

        # Mathematical eliminations (4th place that can't reach 3rd)
        if len(ranked) >= 4:
            third_min_pts = ranked[2]["pts"]  # current 3rd-place pts
            for i in range(3, len(ranked)):
                t = ranked[i]
                remaining = 3 - t["played"]
                max_possible = t["pts"] + remaining * 3
                if max_possible < third_min_pts:
                    math_elim.append(t["team"])

    # Third-place ranking — only when all 12 groups have finished MD3
    third_qualified, third_eliminated = [], []
    if len(thirds) == 12:
        ranked_thirds = sorted(thirds, key=lambda x: (-x["pts"], -x["gd"], -x["gf"]))
        third_qualified = ranked_thirds[:8]
        third_eliminated = ranked_thirds[8:]

    return {
        "winners":           winners,
        "runnersup":         runnersup,
        "third_qualified":   third_qualified,
        "third_eliminated":  third_eliminated,
        "math_eliminated":   math_elim,
        "r32_count":         len(winners) + len(runnersup) + len(third_qualified),
    }


# ── Team status builder ───────────────────────────────────────────────────────

def build_teams_from_results(results):
    """Build base teams dict from TEAM_TEMPLATE; knockout results update pts/status."""
    teams = {}
    for t, meta in TEAM_TEMPLATE.items():
        teams[t] = {
            "group":        meta["group"],
            "flag":         meta["flag"],
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
            continue  # draws don't happen in knockouts (extra time/pens)

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
    """Apply group-stage elimination logic on top of base teams dict."""
    # 4th-place teams after MD3 → eliminated (Group Stage)
    for grp, ranked in standings.items():
        if len(ranked) >= 4 and ranked[3]["played"] == 3:
            name = ranked[3]["team"]
            if name in teams and teams[name]["status"] == "active":
                teams[name]["status"]       = "eliminated"
                teams[name]["roundReached"] = "Group Stage"

    # Bottom 4 third-place teams after all MD3 done → eliminated
    for t in qualifiers.get("third_eliminated", []):
        name = t["team"]
        if name in teams and teams[name]["status"] == "active":
            teams[name]["status"]       = "eliminated"
            teams[name]["roundReached"] = "Group Stage"

    # Mathematically eliminated during group stage
    for name in qualifiers.get("math_eliminated", []):
        if name in teams and teams[name]["status"] == "active":
            teams[name]["status"]       = "eliminated"
            teams[name]["roundReached"] = "Group Stage"

    # Always apply hardcoded eliminations
    for name in HARDCODED_ELIMINATED:
        if name in teams:
            teams[name]["status"]       = "eliminated"
            teams[name]["roundReached"] = teams[name].get("roundReached") or "Group Stage"

    return teams


# ── Stage / matchday detection ────────────────────────────────────────────────

def determine_stage_matchday(results):
    slugs = [r.get("slug", "group-stage") for r in results]
    knockout_slugs = [s for s in slugs if s != "group-stage"]

    if "final"         in knockout_slugs: return "Final",         3
    if "semifinals"    in knockout_slugs: return "Semi-finals",   3
    if "quarterfinals" in knockout_slugs: return "Quarter-finals",3
    if "round-of-16"   in knockout_slugs: return "Round of 16",   3
    if "round-of-32"   in knockout_slugs: return "Round of 32",   3

    games_played = {}
    for r in results:
        if r.get("slug") == "group-stage":
            games_played[r["home"]] = games_played.get(r["home"], 0) + 1
            games_played[r["away"]] = games_played.get(r["away"], 0) + 1

    md = max(games_played.values(), default=0)
    return "Group Stage", max(md, 1)


# ── Persistence ───────────────────────────────────────────────────────────────

def load_existing():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Starting update...")

    existing = load_existing()

    print("  Fetching ESPN results...")
    espn_results = fetch_all_espn_results()
    print(f"  ESPN completed matches: {len(espn_results)}")

    if not espn_results:
        print("  No ESPN data — preserving existing data.json.")
        return

    # Build base team statuses (from knockout results only)
    teams = build_teams_from_results(espn_results)

    # Preserve existing pts / status for teams that have advanced in knockouts
    if existing:
        for name, ex_t in existing.get("teams", {}).items():
            if name in teams:
                # Preserve knockout-round progress (pts > 0 means they won a knockout match)
                if ex_t.get("pts", 0) > 0 and teams[name]["pts"] == 0:
                    teams[name]["pts"]          = ex_t["pts"]
                    teams[name]["status"]       = ex_t["status"]
                    teams[name]["roundReached"] = ex_t.get("roundReached")

    # Compute group standings
    standings = compute_group_standings(espn_results)

    # Determine qualifiers and eliminated teams
    qualifiers = determine_qualifiers(standings)

    # Apply group-stage eliminations
    teams = apply_group_eliminations(teams, standings, qualifiers)

    stage, matchday = determine_stage_matchday(espn_results)
    elim_count   = sum(1 for t in teams.values() if t["status"] == "eliminated")
    recent_clean = [{k: v for k, v in r.items() if k != "slug"} for r in espn_results]

    out = {
        "meta": {
            "lastUpdated":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stage":           stage,
            "matchday":        matchday,
            "eliminatedCount": elim_count,
            "recentResults":   recent_clean,
        },
        "standings":  standings,
        "qualifiers": qualifiers,
        "teams":      teams,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"  Stage: {stage} / MD{matchday} / Eliminated: {elim_count} / R32 qualified: {qualifiers['r32_count']}")
    winners_names   = [q["team"] for q in qualifiers["winners"]]
    runnersup_names = [q["team"] for q in qualifiers["runnersup"]]
    third_names     = [q["team"] for q in qualifiers["third_qualified"]]
    print(f"  Group winners ({len(winners_names)}): {', '.join(winners_names)}")
    print(f"  Runners-up   ({len(runnersup_names)}): {', '.join(runnersup_names)}")
    print(f"  Best 3rd     ({len(third_names)}): {', '.join(third_names)}")
    print("  data.json updated.")


if __name__ == "__main__":
    main()
