#!/usr/bin/env python3
"""
Fetch NCAA men's college basketball team stats from ESPN public API and cache to team_stats_cache.json
Run: python3 ncaa_team_stats_fetcher.py
"""
import requests, time, json, sys
from datetime import datetime

BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball'
TEAM_LIST_URL = BASE + '/teams?limit=1000'
OUT = 'team_stats_cache.json'

session = requests.Session()

def safe_get(url, params=None):
    try:
        r = session.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f'ERROR fetching {url}: {e}', file=sys.stderr)
        return None


def parse_team_stats(team_obj):
    # Try to extract useful stats from ESPN team object
    stats = {}
    try:
        team = team_obj.get('team') or {}
        display_name = team.get('displayName') or team.get('name')
        if not display_name:
            return None, None
        # Normalize name to format like "Duke Blue Devils" which ESPN usually provides
        name = display_name
        # Some useful top-level fields
        record = team_obj.get('record') or {}
        wins = losses = None
        if record:
            # record may be dict or list
            if isinstance(record, dict):
                summary = record.get('items') or record.get('summary')
                # try parsing wins-losses from summary
            if isinstance(record, list) and record:
                try:
                    wl = record[0].get('summary','')
                    if wl and '-' in wl:
                        w,l = wl.split('-')[:2]
                        wins = int(w)
                        losses = int(l)
                except:
                    pass
        # Stats may appear under team_obj['team']['statistics'] or team_obj['team']['stats']
        source_stats = team.get('team') or {}
        # ESPN often provides a 'statistics' list at top-level of team_obj
        stat_items = team_obj.get('statistics') or team.get('statistics') or team.get('stats')
        if not stat_items and isinstance(team_obj.get('team'), dict):
            stat_items = team_obj['team'].get('statistics')
        # Create mapping
        stat_map = {}
        if isinstance(stat_items, list):
            for s in stat_items:
                k = s.get('name') or s.get('displayName')
                v = s.get('value')
                if k:
                    stat_map[k.lower()] = v
        # Try common keys
        def pick(*keys):
            for k in keys:
                if k in stat_map and stat_map[k] not in (None,''):
                    return stat_map[k]
            return None
        ppg = pick('points per game','ppg','avg points')
        opp_ppg = pick('points allowed per game','opp ppg','opp points per game','opp ppg:')
        fga = pick('field goal attempts per game','fga')
        poss = pick('possessions','pace','possessions per game')
        mov = pick('mov','margin of victory','margin')
        # recent game info isn't in this endpoint; skip
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
        return name, stats
    except Exception as e:
        print('parse error', e, file=sys.stderr)
        return None, None


def main():
    data = safe_get(TEAM_LIST_URL)
    if not data:
        print('Failed to fetch team list', file=sys.stderr); return
    teams = data.get('sports',[])
    team_entries = []
    for s in teams:
        for conf in s.get('leagues',[]) if isinstance(s.get('leagues'), list) else []:
            pass
    # different shape: teams often at data['teams'] or data['sports'][0]['leagues'][0]['teams']
    tlist = []
    try:
        tlist = data.get('teams') or []
        if not tlist:
            # try nested
            for sp in data.get('sports',[]):
                for lg in sp.get('leagues',[]):
                    tlist = lg.get('teams') or tlist
    except:
        tlist = []
    if not tlist:
        print('No teams found in response', file=sys.stderr); return

    out = {'last_updated': datetime.utcnow().isoformat(), 'teams': {}, 'meta': {'source': 'espn', 'fetched': len(tlist)}}
    failures = []
    count = 0
    for t in tlist:
        # each t may be an object with 'team' key and 'id'
        team = t.get('team') if isinstance(t, dict) and 'team' in t else t
        team_id = team.get('id') if isinstance(team, dict) else None
        if not team_id:
            # try 'uid'
            team_id = t.get('id')
        team_url = f"{BASE}/teams/{team_id}" if team_id else None
        # First, fetch the team's statistics endpoint which has real numbers
        stats_url = f"{BASE}/teams/{team_id}/statistics" if team_id else None
        schedule_url = f"{BASE}/teams/{team_id}/schedule" if team_id else None
        stats_json = safe_get(stats_url) if stats_url else None
        details = safe_get(team_url) if team_url else t
        # parse name
        name = None
        try:
            if isinstance(details, dict):
                team_obj = details.get('team') or details
                name = team_obj.get('displayName') or team_obj.get('name') or team_obj.get('location') and team_obj.get('location') + ' ' + team_obj.get('name')
        except:
            name = None
        # parse stats from statistics endpoint (prefer this)
        stats = None
        if stats_json:
            try:
                # statistics endpoint often contains 'groups' or 'statistics' with splits
                # we'll search the JSON for entries whose name includes 'points' or 'ppg' or 'points per game'
                def find_value(obj, keywords):
                    if isinstance(obj, dict):
                        for k,v in obj.items():
                            if isinstance(v, (dict,list)):
                                res = find_value(v, keywords)
                                if res is not None:
                                    return res
                            else:
                                # skip
                                pass
                        # look for specific fields
                        name = obj.get('name') or obj.get('displayName') if isinstance(obj, dict) else None
                        if isinstance(name, str) and any(kw in name.lower() for kw in keywords):
                            # try to read a numeric value
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
                ppg = find_value(stats_json, ['points per game','ppg','points per game (ppg)','points'])
                opp_ppg = find_value(stats_json, ['points allowed per game','opp ppg','points allowed','opp points'])
                fga = find_value(stats_json, ['field goal attempts','fga'])
                poss = find_value(stats_json, ['possessions','pace'])
                mov = find_value(stats_json, ['margin of victory','mov','margin'])
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
                    'wins': None,
                    'losses': None,
                }
            except Exception as e:
                print('Error parsing statistics endpoint for', team_id, e, file=sys.stderr)
                stats = None
        # fallback: try parsing from team details
        if not stats:
            name, stats = parse_team_stats(details or t)
        # Now fetch schedule to compute recent_ppg and recent_margin
        recent = None
        if schedule_url:
            sched = safe_get(schedule_url)
            if sched and isinstance(sched, dict):
                # find events/games
                events = sched.get('events') or sched.get('games') or []
                # take most recent completed games (where status type completed)
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
                        # some events have 'status.type.state' == 'post'
                        if not completed:
                            # try checking if scores exist
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
                                    # find other team to compute margin
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
                    # take last 5 (most recent first)
                    last = recent_scores[:5]
                    # build lists of scores and margins (int values)
                    recent_ppg_list = [int(r['score']) for r in last]
                    recent_margin_list = [int(r['score'] - (r['opp_score'] if r['opp_score'] is not None else 0)) for r in last]
                    stats['recent_ppg'] = recent_ppg_list
                    stats['recent_margin'] = recent_margin_list
        if not name:
            failures.append({'team': team, 'reason': 'no name'})
            continue
        out['teams'][name] = stats
        count += 1
        # rate limit
        time.sleep(0.14)
    # write cache
    with open(OUT,'w') as f:
        json.dump(out, f, indent=2)
    # summary
    ok = count
    failed = len(failures)
    print(f'Fetched {ok} teams, failures: {failed}')
    if failed:
        print('Failures:', failures)

if __name__=='__main__':
    main()
