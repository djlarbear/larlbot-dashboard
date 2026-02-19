#!/usr/bin/env python3
"""
Fetch NBA team stats from ESPN and save to nba_team_stats_cache.json
"""
import requests, time, json, sys
from datetime import datetime

BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
TEAM_LIST_URL = BASE + '/teams?limit=50'
OUT = 'nba_team_stats_cache.json'

session = requests.Session()

def safe_get(url, params=None):
    try:
        r = session.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f'ERROR fetching {url}: {e}', file=sys.stderr)
        return None


def find_value(obj, keywords):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, (dict,list)):
                res = find_value(v, keywords)
                if res is not None:
                    return res
        name = obj.get('name') or obj.get('displayName') if isinstance(obj, dict) else None
        if isinstance(name, str) and any(kw in name.lower() for kw in keywords):
            val = obj.get('value') or obj.get('displayValue') or obj.get('avg') or obj.get('average')
            if val is not None and val != '':
                try:
                    return float(str(val).replace(',',''))
                except:
                    return val
    elif isinstance(obj, list):
        for it in obj:
            res = find_value(it, keywords)
            if res is not None:
                return res
    return None


def main():
    data = safe_get(TEAM_LIST_URL)
    if not data:
        print('Failed to fetch NBA team list', file=sys.stderr); return
    tlist = data.get('teams') or []
    # nested shape
    if not tlist:
        for sp in data.get('sports',[]):
            for lg in sp.get('leagues',[]):
                tlist = lg.get('teams') or tlist
    if not tlist:
        print('No NBA teams found', file=sys.stderr); return

    out = {'last_updated': datetime.utcnow().isoformat(), 'teams': {}, 'meta': {'source': 'espn_nba', 'fetched': len(tlist)}}
    count = 0
    failures = []
    for t in tlist:
        team = t.get('team') if isinstance(t, dict) and 'team' in t else t
        team_id = team.get('id') if isinstance(team, dict) else None
        if not team_id:
            team_id = t.get('id')
        team_url = f"{BASE}/teams/{team_id}" if team_id else None
        stats_url = f"{BASE}/teams/{team_id}/statistics" if team_id else None
        schedule_url = f"{BASE}/teams/{team_id}/schedule" if team_id else None
        details = safe_get(team_url) if team_url else t
        stats_json = safe_get(stats_url) if stats_url else None
        name = None
        try:
            if isinstance(details, dict):
                team_obj = details.get('team') or details
                name = team_obj.get('displayName') or team_obj.get('name') or (team_obj.get('location') and team_obj.get('location') + ' ' + team_obj.get('name'))
        except:
            name = None
        stats = None
        if stats_json:
            try:
                ppg = find_value(stats_json, ['points per game','ppg','avg points','avgpoints','avg points for','avgpointsfor'])
                opp_ppg = find_value(stats_json, ['points allowed per game','opp ppg','points against','avg points against'])
                fga = find_value(stats_json, ['field goal attempts','fga'])
                poss = find_value(stats_json, ['possessions','pace'])
                mov = find_value(stats_json, ['differential','net rating','differential per game','differential'])
                # wins/losses often under 'record' or 'team'->'record'
                wins = None
                losses = None
                rec = stats_json.get('record') if isinstance(stats_json, dict) else None
                if not rec and isinstance(details, dict):
                    rec = details.get('record')
                if isinstance(rec, dict):
                    try:
                        summary = rec.get('items') or rec.get('summary')
                        if isinstance(summary, list) and summary:
                            wl = summary[0].get('summary','')
                            if wl and '-' in wl:
                                w,l = wl.split('-')[:2]
                                wins = int(w); losses = int(l)
                    except:
                        pass
                stats = {
                    'ppg': float(ppg) if ppg not in (None,'') else None,
                    'opp_ppg': float(opp_ppg) if opp_ppg not in (None,'') else None,
                    'poss': float(poss) if poss not in (None,'') else None,
                    'fga': float(fga) if fga not in (None,'') else None,
                    'home_ppg': None,
                    'away_ppg': None,
                    'recent_ppg': None,
                    'recent_margin': None,
                    'mov': float(mov) if mov not in (None,'') else None,
                    'wins': wins,
                    'losses': losses,
                }
            except Exception as e:
                print('Error parsing NBA statistics for', team_id, e, file=sys.stderr)
                stats = None
        if not stats:
            # fallback: try pulling some fields from details
            stats = {'ppg': None, 'opp_ppg': None, 'poss': None, 'fga': None, 'home_ppg': None, 'away_ppg': None, 'recent_ppg': None, 'recent_margin': None, 'mov': None, 'wins': None, 'losses': None}
        # schedule
        if schedule_url:
            sched = safe_get(schedule_url)
            if sched and isinstance(sched, dict):
                events = sched.get('events') or sched.get('games') or []
                recent_scores = []
                for ev in events:
                    try:
                        status = ev.get('status') or {}
                        completed = False
                        if isinstance(status, dict):
                            ttype = status.get('type') or {}
                            if isinstance(ttype, dict):
                                if ttype.get('completed'):
                                    completed = True
                                if ttype.get('name','').lower() in ('final','completed'):
                                    completed = True
                        if not completed:
                            if ev.get('status',{}).get('type',{}).get('state') in ('post','final'):
                                completed = True
                        if not completed:
                            continue
                        competitions = ev.get('competitions') or []
                        for comp in competitions:
                            for competitor in comp.get('competitors',[]):
                                tid = competitor.get('team',{}).get('id')
                                if str(tid) == str(team_id):
                                    score = competitor.get('score')
                                    opp = None
                                    for c2 in comp.get('competitors',[]):
                                        if c2 is competitor: continue
                                        opp = c2
                                    if score is None: continue
                                    opp_score = opp.get('score') if opp else None
                                    try:
                                        recent_scores.append({'score': float(score), 'opp_score': float(opp_score) if opp_score is not None else None})
                                    except:
                                        pass
                    except Exception:
                        continue
                if recent_scores:
                    last = recent_scores[:5]
                    recent_ppg_list = [int(r['score']) for r in last]
                    recent_margin_list = [int(r['score'] - (r['opp_score'] if r['opp_score'] is not None else 0)) for r in last]
                    stats['recent_ppg'] = recent_ppg_list
                    stats['recent_margin'] = recent_margin_list
        if not name:
            failures.append({'team': team, 'reason': 'no name'})
            continue
        out['teams'][name] = stats
        count += 1
        time.sleep(0.14)

    with open(OUT,'w') as f:
        json.dump(out, f, indent=2)
    print(f'Fetched {count} NBA teams, failures: {len(failures)}')
    if failures:
        print('Failures:', failures)

if __name__=='__main__':
    main()
