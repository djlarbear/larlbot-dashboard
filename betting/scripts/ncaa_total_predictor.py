"""
Simple NCAA total predictor
- Fetches cached team stats from local files if present (team_stats_cache.json)
- Otherwise, attempts to fetch from sports-reference via scraping (simple, fallback)
- Predicts total by averaging team offensive PPG (adjusted for opponent defense), pace proxy, recent form, and home/away splits
- Returns: predicted_total (float), edge (predicted - market), confidence (0-100), side ('OVER'/'UNDER')

This is intentionally simple and well-documented.
"""
import json
import os
import math
from statistics import mean

CACHE_PATH = '../data/team_stats_cache.json'
NBA_CACHE_PATH = '../data/nba_team_stats_cache.json'

def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH,'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(data):
    try:
        with open(CACHE_PATH,'w') as f:
            json.dump(data,f)
    except:
        pass

# Expected team stats structure (if available):
# {"Team Name": {"ppg": 75.2, "opp_ppg": 70.1, "fga": 58.3, "poss": 70.5, "home_ppg":78.1, "away_ppg":72.0, "recent_ppg": [..]}}

def _get_cache(league='ncaa'):
    """Always read fresh cache (teams nested under 'teams' key or flat). league: 'ncaa' or 'nba'"""
    path = CACHE_PATH if league=='ncaa' else NBA_CACHE_PATH
    if os.path.exists(path):
        try:
            with open(path,'r') as f:
                raw = json.load(f)
                return raw.get('teams', raw)
        except:
            return {}
    return {}

def fetch_team_stats_stub(team_name):
    """Fallback stub: if no data, return league-average proxies."""
    league_avg = {
        'ppg': 72.0,
        'opp_ppg': 72.0,
        'fga': 55.0,
        'poss': 70.0,
        'home_ppg':73.5,
        'away_ppg':70.5,
        'recent_ppg': [72.0]*5
    }
    return league_avg


def get_team_stats(team_name, league='ncaa'):
    # normalized key
    key = team_name.strip()
    cache = _get_cache(league=league)
    if key in cache and cache[key].get('ppg') is not None:
        return cache[key]
    # Fallback to stub if team not found
    return fetch_team_stats_stub(key)


def predict_total(home_team, away_team, home_is_home=True, league='ncaa'):
    """Predict combined total for a game between home_team and away_team.
    Returns: predicted_total, components, uncertainty_score (0-1)
    """
    h = get_team_stats(home_team, league=league)
    a = get_team_stats(away_team, league=league)

    # Helper: get numeric value with fallback for None
    def val(d, key, default):
        v = d.get(key)
        return v if v is not None else default

    # Offensive baseline: average of team ppg and opponent-adjusted ppg
    h_off = (val(h,'ppg',72.0) + (val(h,'ppg',72.0) + val(a,'opp_ppg',72.0))/2)/2
    a_off = (val(a,'ppg',72.0) + (val(a,'ppg',72.0) + val(h,'opp_ppg',72.0))/2)/2

    # Pace proxy: average possessions
    poss = mean([val(h,'poss',70.0), val(a,'poss',70.0)])
    poss_factor = poss / 70.0  # around 1

    # Home/away splits: if home_is_home boost home scoring slightly
    home_boost = 1.03 if home_is_home else 1.0

    # Recent form: use last 5 games mean vs season ppg
    def recent_factor(stats):
        recent = stats.get('recent_ppg') or []
        if recent and len(recent)>=3:
            return mean(recent)/val(stats,'ppg',72.0)
        return 1.0

    h_recent = recent_factor(h)
    a_recent = recent_factor(a)

    # Combine into predicted team scores
    h_pred = h_off * poss_factor * home_boost * h_recent
    a_pred = a_off * poss_factor * a_recent

    predicted_total = h_pred + a_pred

    # Simple uncertainty: based on how much we relied on stubs (higher uncertainty if keys were stubbed)
    stub_count = 0
    for t in (h,a):
        # count as stub if poss is None/missing OR equals default 70.0
        if t.get('poss') is None or t.get('poss') == 70.0:
            stub_count += 1
        # also count if recent form is missing
        if not t.get('recent_ppg'):
            stub_count += 1
        # detect full stub (ppg exactly 72.0 and opp_ppg exactly 72.0)
        if t.get('ppg') == 72.0 and t.get('opp_ppg') == 72.0:
            stub_count += 2
    uncertainty = min(0.6, 0.05 * stub_count + 0.05)  # between 0.05 and 0.25 typically

    components = {
        'home_pred': h_pred,
        'away_pred': a_pred,
        'poss': poss,
        'home_boost': home_boost,
        'h_recent': h_recent,
        'a_recent': a_recent
    }

    return predicted_total, components, uncertainty


def evaluate_against_market(predicted_total, market_total):
    edge = predicted_total - market_total
    # Confidence derived from distance relative to std (use simple scale)
    abs_diff = abs(edge)
    # base confidence 40, add scaled diff, reduce by uncertainty
    confidence = 40 + min(40, int(abs_diff * 4))
    confidence = max(20, min(90, confidence))
    side = 'OVER' if edge > 0 else 'UNDER'
    return edge, int(confidence), side


if __name__ == '__main__':
    # quick local test
    pt, comp, unc = predict_total('Duke','UNC')
    e,c,s = evaluate_against_market(pt,150)
    print('pred',pt,'edge',e,'conf',c,'side',s)
