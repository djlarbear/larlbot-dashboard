"""
Simple NCAA spread predictor
- Loads cached team stats (team_stats_cache.json) when available
- Uses team offensive/defensive PPG, margin of victory proxy, home court advantage
- Returns predicted_margin (home - away), edge (predicted_margin - market_spread), confidence (0-100), recommendation ('HOME'/'AWAY')
"""
import json
import os
from statistics import mean

CACHE_PATH = 'team_stats_cache.json'
NBA_CACHE_PATH = 'nba_team_stats_cache.json'

def load_cache(path):
    if os.path.exists(path):
        try:
            with open(path,'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _get_cache(league='ncaa'):
    path = CACHE_PATH if league=='ncaa' else NBA_CACHE_PATH
    raw = load_cache(path)
    return raw.get('teams', raw)

def get_team(team_name, league='ncaa'):
    cache = _get_cache(league=league)
    entry = cache.get(team_name.strip(), {})
    if entry.get('ppg') is not None:
        return entry
    # defaults differ slightly for NBA (higher scoring, lower HCA)
    if league=='nba':
        return {'ppg':110.0,'opp_ppg':110.0,'mov':0.0,'home_ppg':111.5,'away_ppg':108.5,'recent_margin':[0,0,0,0,0]}
    return {'ppg':72.0,'opp_ppg':72.0,'mov':0.0,'home_ppg':73.5,'away_ppg':70.5,'recent_margin':[0,0,0,0,0]}

def predict_spread(home_team, away_team, home_is_home=True, injuries=None, league='ncaa'):
    h = get_team(home_team, league=league)
    a = get_team(away_team, league=league)

    # Helper for None values
    def val(d, key, default):
        v = d.get(key)
        return v if v is not None else default

    # baseline margin = (home_off - away_def) + (home_def - away_off) / 2
    home_off = val(h,'ppg',72.0)
    home_def = val(h,'opp_ppg',72.0)
    away_off = val(a,'ppg',72.0)
    away_def = val(a,'opp_ppg',72.0)

    baseline = (home_off - away_def + (home_off - away_off) + (away_def - home_def))/3

    # recent form: mean of recent_margin
    recent_h = mean(val(h,'recent_margin',[0]) or [0])
    recent_a = mean(val(a,'recent_margin',[0]) or [0])
    recent_adj = (recent_h - recent_a) * 0.3

    # home court advantage: smaller for NBA
    hca = (3.5 if league=='ncaa' else 2.5) if home_is_home else 0.0

    predicted_margin = baseline + recent_adj + hca

    # injury adjustment (simple): if injuries list includes starter, swing by 3 points
    inj_adj = 0
    if injuries:
        inj_adj = -3 if injuries.get('home_missing_starters') else 0
        inj_adj += 3 if injuries.get('away_missing_starters') else 0
    predicted_margin += inj_adj

    # uncertainty based on data completeness
    completeness = 0
    for t in (h,a):
        if t.get('ppg',72.0)==72.0:
            completeness +=1
    uncertainty = min(0.6, 0.1*completeness + 0.05)

    # edge: predicted_margin - market_spread (market_spread is home - away implied by line: negative if home favored)
    # We'll return predicted_margin where positive means HOME by that many points

    # confidence scaling: larger margin -> higher confidence, reduced by uncertainty
    base_conf = 45 + min(30, int(abs(predicted_margin)*3))
    conf = int(max(20, min(92, base_conf * (1 - uncertainty))))

    side = 'HOME' if predicted_margin > 0 else 'AWAY'

    return predicted_margin, conf, side, {'baseline':baseline,'recent_adj':recent_adj,'hca':hca,'inj_adj':inj_adj}

if __name__ == '__main__':
    print(predict_spread('Duke','UNC'))
