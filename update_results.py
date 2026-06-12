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
    "Turkey": "Turkiye", "Turkiye": "Turkiye",
    "Germany": "Germany", "Curacao": "Curcao",
    "Ivory Coast": "Cote d'Ivoire", "Cote d'Ivoire": "Cote d'Ivoire",
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

# Fix unicode names that may differ
TEAM_NAME_MAP["Ürkiye"] = "Türkiye"
TEAM_NAME_MAP["Türkiye"] = "Türkiye"
TEAM_NAME_MAP["Turkey"] = "Türkiye"
TEAM_NAME_MAP["Curacao"] = "Curaçao"
TEAM_NAME_MAP["Curaçao"] = "Curaçao"
TEAM_NAME_MAP["Ivory Coast"] = "Côte d'Ivoire"
TEAM_NAME_MAP["Cote d'Ivoire"] = "Côte d'Ivoire"
TEAM_NAME_MAP["Côte d'Ivoire"] = "Côte d'Ivoire"
# Fix placeholder strings above
TEAM_NAME_MAP["Turkiye"] = "Türkiye"
TEAM_NAME_MAP["Curcao"] = "Curaçao"
TEAM_NAME_MAP["Cote d'Ivoire"] = "Côte d'Ivoire"

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
    "Türkiye":         {"group":"D","flag":"\U0001f1f9\U0001f1f7"},
    "Germany":              {"group":"E","flag":"\U0001f1e9\U0001f1ea"},
    "Curaçao":         {"group":"E","flag":"\U0001f1e8\U0001f1fc"},
    "Côte d'Ivoire":   {"group":"E","flag":"\U0001f1e8\U0001f1ee"},
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


def normalise(name):
    return TEAM_NAME_MAP.get(name, name)


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


def build_teams_from_results(results):
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
        home  = r["home"]
        away  = r["away"]
        hs    = r["homeScore"]
        as_   = r["awayScore"]
        slug  = r.get("slug", "group-stage")
        rnd_l = r["round"].lower()

        if slug == "group-stage":
            continue

        rnd_key = None
        for k in ROUND_POINTS:
            if k in rnd_l:
                rnd_key = k
                break
        if rnd_key is None:
            continue

        home_won = hs > as_
        away_won = as_ > hs
        if home_won:
            winner, loser = home, away
        elif away_won:
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


def determine_stage_matchday(results):
    slugs = [r.get("slug", "group-stage") for r in results]
    knockout_slugs = [s for s in slugs if s != "group-stage"]

    if "final" in knockout_slugs:
        return "Final", 3
    if "semifinals" in knockout_slugs:
        return "Semi-finals", 3
    if "quarterfinals" in knockout_slugs:
        return "Quarter-finals", 3
    if "round-of-16" in knockout_slugs:
        return "Round of 16", 3
    if "round-of-32" in knockout_slugs:
        return "Round of 32", 3

    games_played = {}
    for r in results:
        if r.get("slug") == "group-stage":
            games_played[r["home"]] = games_played.get(r["home"], 0) + 1
            games_played[r["away"]] = games_played.get(r["away"], 0) + 1

    md = max(games_played.values(), default=0)
    return "Group Stage", max(md, 1)


def load_existing():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    print(f"Starting update...")

    existing = load_existing()

    print("  Fetching ESPN results...")
    espn_results = fetch_all_espn_results()
    print(f"  ESPN completed matches: {len(espn_results)}")

    if not espn_results:
        print("  No ESPN data — preserving existing data.json.")
        return

    teams           = build_teams_from_results(espn_results)
    stage, matchday = determine_stage_matchday(espn_results)

    if existing:
        for name, ex_t in existing.get("teams", {}).items():
            if name in teams and teams[name]["pts"] == 0 and ex_t.get("pts", 0) > 0:
                teams[name]["pts"]          = ex_t["pts"]
                teams[name]["status"]       = ex_t["status"]
                teams[name]["roundReached"] = ex_t.get("roundReached")

    elim_count   = sum(1 for t in teams.values() if t["status"] == "eliminated")
    recent_clean = [{k: v for k, v in r.items() if k != "slug"} for r in espn_results[-20:]]

    out = {
        "meta": {
            "lastUpdated":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stage":           stage,
            "matchday":        matchday,
            "eliminatedCount": elim_count,
            "recentResults":   recent_clean,
        },
        "teams": teams,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"  Stage: {stage} / MD{matchday} / Eliminated: {elim_count}")
    print(f"  Recent results: {len(recent_clean)}")
    for r in recent_clean:
        print(f"    {r['home']} {r['homeScore']}-{r['awayScore']} {r['away']}")
    print("  data.json updated.")


if __name__ == "__main__":
    main()
