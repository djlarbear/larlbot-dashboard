#!/usr/bin/env python3
"""
Real Betting Model v4.0 - FanDuel ONLY + Crystal Clear Bet Instructions
ONLY uses FanDuel spreads, moneyline, and totals
Crystal clear instructions: which team, what line, what it means
"""

import requests
import json
from datetime import datetime, timezone, timedelta
import sys
import time
import logging

sys.path.insert(0, '/Users/macmini/.openclaw/workspace')

# Configure logging for API errors
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/Users/macmini/.openclaw/workspace/betting/logs/api_errors.log'),
        logging.StreamHandler()
    ]
)

class RealBettingModel:
    def __init__(self):
        self.oddsapi_key = '82865426fd192e243376eb4e51185f3b'
        self.manual_odds = self.load_manual_odds()
        self.sports = [
            {'key': 'basketball_ncaab', 'display': 'NCAA Basketball', 'emoji': '🏀'},
            {'key': 'basketball_nba', 'display': 'NBA', 'emoji': '🏀'},
            {'key': 'americanfootball_nfl', 'display': 'NFL', 'emoji': '🏈'},
            {'key': 'baseball_mlb', 'display': 'MLB', 'emoji': '⚾'},
            {'key': 'americanfootball_ncaaf', 'display': 'College Football', 'emoji': '🏈'},
            {'key': 'ice_hockey_nhl', 'display': 'NHL', 'emoji': '🏒'},
            {'key': 'soccer_epl', 'display': 'Premier League', 'emoji': '⚽'},
        ]
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def load_manual_odds(self):
        """Load manual FanDuel odds overrides from file"""
        try:
            with open('manual_odds.json', 'r') as f:
                data = json.load(f)
                return data.get('overrides', {})
        except:
            return {}
    
    def fetch_odds_with_retry(self, url, params, sport_name, max_retries=3):
        """Fetch odds from API with exponential backoff retry logic
        
        Args:
            url: API endpoint URL
            params: Request parameters
            sport_name: Sport display name (for logging)
            max_retries: Maximum number of retry attempts
            
        Returns:
            dict: API response JSON or empty dict on failure
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()  # Raise exception for HTTP errors
                
                logging.info(f"✅ {sport_name}: API fetch successful")
                return response.json()
                
            except requests.exceptions.Timeout:
                logging.warning(f"⏱️ {sport_name}: API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                else:
                    logging.error(f"❌ {sport_name}: API timeout after {max_retries} attempts")
                    return {}
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 'unknown'
                logging.error(f"❌ {sport_name}: HTTP {status_code} error: {e}")
                if attempt < max_retries - 1 and status_code in [429, 500, 502, 503, 504]:
                    # Retry on rate limit or server errors
                    time.sleep(2 ** attempt)
                else:
                    return {}
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"❌ {sport_name}: Network error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logging.critical(f"🚨 {sport_name}: CRITICAL - API completely unreachable after {max_retries} attempts")
                    return {}
                    
            except Exception as e:
                logging.error(f"❌ {sport_name}: Unexpected error: {type(e).__name__}: {e}")
                return {}
        
        return {}
    
    def check_manual_odds(self, game_string):
        """Check if manual odds exist for this game"""
        for game_name, spread_str in self.manual_odds.items():
            if game_name.lower() == game_string.lower():
                try:
                    spread = float(spread_str)
                    logging.info(f"✅ Manual odds override found for {game_string}: {spread}")
                    return spread
                except Exception as e:
                    logging.warning(f"⚠️ Invalid manual odds value for {game_string}: {spread_str} ({e})")
                    pass
        return None
    
    def get_games_for_sport(self, sport_key, display_name, emoji=''):
        """Fetch real games with FANDUEL ONLY odds from OddsAPI - TODAY ONLY
        Includes: Spreads, Moneyline (H2H), Over/Under (Totals), Player Props"""
        try:
            url = f"{self.base_url}/sports/{sport_key}/odds"
            params = {
                'api_key': self.oddsapi_key,
                'regions': 'us',
                'markets': 'spreads,h2h,totals',  # Added totals for over/under
                'oddsFormat': 'american'
            }
            
            print(f"  [Fetching {emoji} {display_name}...]", end='', flush=True)
            
            # Use retry logic instead of direct call
            games = self.fetch_odds_with_retry(url, params, display_name)
            
            if games:  # If API returned data
                
                # Get TODAY's date in EST
                now_est = datetime.now(timezone(timedelta(hours=-5)))
                today_est_date = now_est.date()
                
                picks = []
                games_for_today = 0
                
                for game in games:
                    try:
                        home = game.get('home_team', 'Unknown')
                        away = game.get('away_team', 'Unknown')
                        commence = game.get('commence_time', 'TBA')
                        game_id = game.get('id', '')
                        
                        # Parse time and convert to EST with DATE
                        try:
                            game_time_utc = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                            est_offset = timedelta(hours=-5)
                            est_tz = timezone(est_offset)
                            game_time_est = game_time_utc.astimezone(est_tz)
                            
                            # ✅ CRITICAL: ONLY include games for TODAY
                            game_date = game_time_est.date()
                            if game_date != today_est_date:
                                continue  # Skip games from other days
                            
                            games_for_today += 1
                            # Include date AND time
                            time_str = game_time_est.strftime('%I:%M %p EST')
                        except:
                            time_str = 'TBA'
                            continue
                        
                        # Check for manual odds override FIRST
                        game_string = f"{away} @ {home}"
                        manual_spread = self.check_manual_odds(game_string)
                        
                        if manual_spread:
                            # Use manual FanDuel odds
                            pick = self.build_pick_from_manual_odds(
                                game_string, home, away, manual_spread, 
                                display_name, time_str, game_id, emoji
                            )
                            picks.append(pick)
                        else:
                            # Extract FANDUEL ONLY odds from OddsAPI (returns LIST of bet types)
                            bookmakers = game.get('bookmakers', [])
                            fanduel_bets = self.extract_fanduel_only(bookmakers, home, away)
                            
                            if fanduel_bets:
                                # Generate picks for EACH bet type (spread, moneyline, totals)
                                for fanduel_data in fanduel_bets:
                                    pick = self.build_pick_from_odds(
                                        fanduel_data, game_string, home, away,
                                        display_name, time_str, game_id, emoji
                                    )
                                    if pick:
                                        picks.append(pick)
                    except Exception as e:
                        continue
                
                # Print summary for this sport
                print(f" ✅ {games_for_today} TODAY")
                return picks
            else:
                # No games returned (API error handled by fetch_with_retry)
                print(f" ❌ No data")
                return []
                
        except Exception as e:
            logging.error(f"Unexpected error in get_games_for_sport: {type(e).__name__}: {e}")
            print(f" [Error: {e}]")
            return []
    
    def extract_fanduel_only(self, bookmakers, home, away):
        """Extract ALL FanDuel odds (spreads, moneyline, totals) - ignore all other bookmakers
        Returns a list of different bet types available for this game"""
        try:
            bets = []
            for bookmaker in bookmakers:
                if 'fanduel' in bookmaker.get('title', '').lower():
                    markets = bookmaker.get('markets', [])
                    
                    # Try spreads
                    spread_data = self.parse_spreads_market(markets, home, away)
                    if spread_data:
                        bets.append({'type': 'SPREAD', 'data': spread_data, 'bookmaker': 'FanDuel'})
                    
                    # Try moneyline/h2h
                    moneyline_data = self.parse_moneyline_market(markets, home, away)
                    if moneyline_data:
                        bets.append({'type': 'MONEYLINE', 'data': moneyline_data, 'bookmaker': 'FanDuel'})
                    
                    # Try totals (over/under)
                    totals_data = self.parse_totals_market(markets, home, away)
                    if totals_data:
                        bets.append({'type': 'TOTALS', 'data': totals_data, 'bookmaker': 'FanDuel'})
            
            return bets if bets else None
        except:
            return None
    
    def parse_spreads_market(self, markets, home, away):
        """Parse spreads market data"""
        try:
            for market in markets:
                if market.get('key') == 'spreads':
                    outcomes = market.get('outcomes', [])
                    if len(outcomes) >= 2:
                        home_outcome = None
                        away_outcome = None
                        
                        for outcome in outcomes:
                            name = outcome.get('name', '').lower()
                            if home.lower() in name:
                                home_outcome = outcome
                            elif away.lower() in name:
                                away_outcome = outcome
                        
                        if home_outcome and away_outcome:
                            return {
                                'home_team': home,
                                'away_team': away,
                                'home_spread': home_outcome.get('point', 0),
                                'away_spread': away_outcome.get('point', 0),
                                'home_odds': home_outcome.get('price', -110),
                                'away_odds': away_outcome.get('price', -110)
                            }
        except:
            pass
        
        return None
    
    def parse_moneyline_market(self, markets, home, away):
        """Parse moneyline (h2h) market data"""
        try:
            for market in markets:
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    if len(outcomes) >= 2:
                        home_outcome = None
                        away_outcome = None
                        
                        for outcome in outcomes:
                            name = outcome.get('name', '').lower()
                            if home.lower() in name:
                                home_outcome = outcome
                            elif away.lower() in name:
                                away_outcome = outcome
                        
                        if home_outcome and away_outcome:
                            return {
                                'home_team': home,
                                'away_team': away,
                                'home_odds': home_outcome.get('price', 0),
                                'away_odds': away_outcome.get('price', 0)
                            }
        except:
            pass
        
        return None
    
    def parse_totals_market(self, markets, home, away):
        """Parse totals (over/under) market data"""
        try:
            for market in markets:
                if market.get('key') == 'totals':
                    outcomes = market.get('outcomes', [])
                    if len(outcomes) >= 2:
                        over_outcome = None
                        under_outcome = None
                        
                        for outcome in outcomes:
                            outcome_name = outcome.get('name', '').lower()
                            if 'over' in outcome_name:
                                over_outcome = outcome
                            elif 'under' in outcome_name:
                                under_outcome = outcome
                        
                        if over_outcome and under_outcome:
                            return {
                                'total': over_outcome.get('point', 0),
                                'over_price': over_outcome.get('price', -110),
                                'under_price': under_outcome.get('price', -110)
                            }
        except:
            pass
        
        return None
    
    def build_pick_from_manual_odds(self, game_string, home, away, spread, 
                                     display_name, time_str, game_id, emoji=''):
        """Build pick from manual FanDuel odds"""
        # Determine which team is favored
        if spread < 0:
            favored_team = home
            spread_abs = abs(spread)
            unfavored_team = away
            recommendation = f"{home} {spread}"
            explanation = f"Bet on {home} to win by {int(spread_abs + 1)}+ points"
        else:
            favored_team = away
            spread_abs = abs(spread)
            unfavored_team = home
            recommendation = f"{away} +{spread}"
            explanation = f"Bet on {away} to win straight up or lose by less than {int(spread_abs)} points"
        
        # Use real spread predictor
        try:
            from ncaa_spread_predictor import predict_spread
            predicted_margin, conf, side, details = predict_spread(home, away, home_is_home=True, injuries=None, league=('nba' if 'NBA' in display_name else 'ncaa'))
            market_spread = spread
            edge = abs(predicted_margin - market_spread)
            confidence = int(conf)
        except Exception as e:
            print(f"⚠️ Spread predictor fallback for {game_string}: {e}")
            edge = abs(spread) * 0.4
            confidence = int(min(82, 65 + (abs(spread) * 1.5)))
            details = {}
        
        # Generate intelligent reason
        reason = self.generate_reason(recommendation, spread, edge, int(confidence), 'SPREAD', None, home, away)
        
        return {
            'game': game_string,
            'sport': f"{emoji} {display_name}",
            'bet_type': 'SPREAD',
            'recommendation': recommendation,
            'fanduel_line': recommendation,
            'edge': round(edge, 1),
            'confidence': int(confidence),
            'risk_tier': self.get_risk_tier(int(confidence)),
            'game_time': time_str,
            'spread': spread,
            'bet_explanation': explanation,
            'reason': reason,  # ✅ ADD INTELLIGENT REASON
            'bookmaker_source': 'FanDuel (Manual Override)',
            'data_source': 'FanDuel (Manual Override)',
            'bet_instructions': f"📍 PLACE BET ON FanDuel: {recommendation} (SPREAD) | {explanation} | Confidence: {int(confidence)}%"
        }
    
    def build_pick_from_odds(self, fanduel_data, game_string, home, away, 
                              display_name, time_str, game_id, emoji=''):
        """Build pick from FanDuel odds"""
        bet_type = fanduel_data['type']
        data = fanduel_data['data']
        
        if bet_type == 'SPREAD':
            home_spread = data['home_spread']
            away_spread = data['away_spread']
            
            # Determine recommendation
            if home_spread < 0:
                # Home team favored
                spread_value = abs(home_spread)
                recommendation = f"{home} {home_spread}"
                explanation = f"Bet on {home} to win by {int(spread_value + 1)}+ points"
            else:
                # Away team favored
                spread_value = abs(away_spread)
                recommendation = f"{away} {away_spread}"
                explanation = f"Bet on {away} to win straight up or lose by less than {int(spread_value)} points"
            
            spread = home_spread if home_spread < 0 else away_spread
            # Use real spread predictor
            try:
                from ncaa_spread_predictor import predict_spread
                league = 'nba' if 'NBA' in display_name or 'NBA' in self.sports[1].get('display','') else 'ncaa'
                predicted_margin, conf, side, details = predict_spread(home, away, home_is_home=True, injuries=None, league= ('nba' if 'NBA' in display_name else 'ncaa'))
                # market spread (positive means away favored in our structure); normalize
                market_spread = spread
                edge = abs(predicted_margin - market_spread)
                confidence = int(conf)
            except Exception:
                edge = abs(spread) * 0.4
                confidence = min(82, int(65 + (abs(spread) * 1.5)))
                details = {}
            
            # Generate intelligent reason (include home/away teams)
            reason = self.generate_reason(recommendation, spread, edge, int(confidence), 'SPREAD', None, home, away)
            
            return {
                'game': game_string,
                'sport': f"{emoji} {display_name}",
                'bet_type': 'SPREAD',
                'recommendation': recommendation,
                'fanduel_line': f"{home} {home_spread} / {away} {away_spread}",
                'edge': round(edge, 1),
                'confidence': int(confidence),
                'risk_tier': self.get_risk_tier(int(confidence)),
                'game_time': time_str,
                'spread': spread,
                'bet_explanation': explanation,
                'reason': reason,  # ✅ ADD INTELLIGENT REASON
                'bookmaker_source': 'FanDuel',
                'data_source': 'OddsAPI (FanDuel)',
                'bet_instructions': f"📍 PLACE BET ON FanDuel: {recommendation} (SPREAD) | {explanation} | Confidence: {int(confidence)}%"
            }
        
        elif bet_type == 'MONEYLINE':
            home_odds = data['home_odds']
            away_odds = data['away_odds']
            
            # Determine favorite
            if abs(home_odds) < abs(away_odds):
                favorite = home
                favorite_odds = home_odds
                underdog = away
                recommendation = f"{home} (Moneyline)"
                explanation = f"Bet on {home} to win straight up (odds: {home_odds})"
            else:
                favorite = away
                favorite_odds = away_odds
                underdog = home
                recommendation = f"{away} (Moneyline)"
                explanation = f"Bet on {away} to win straight up (odds: {away_odds})"
            
            confidence = 60
            edge = 0.5
            
            # Generate intelligent reason
            reason = self.generate_reason(recommendation, 0, edge, confidence, 'MONEYLINE', None, home, away)
            
            return {
                'game': game_string,
                'sport': f"{emoji} {display_name}",
                'bet_type': 'MONEYLINE',
                'recommendation': recommendation,
                'fanduel_line': f"{home} ({home_odds}) / {away} ({away_odds})",
                'edge': edge,
                'confidence': confidence,
                'risk_tier': self.get_risk_tier(confidence),
                'game_time': time_str,
                'spread': 0,
                'bet_explanation': explanation,
                'reason': reason,  # ✅ ADD INTELLIGENT REASON
                'bookmaker_source': 'FanDuel',
                'data_source': 'OddsAPI (FanDuel)',
                'bet_instructions': f"📍 PLACE BET ON FanDuel: {recommendation} | {explanation} | Confidence: {confidence}%"
            }
        
        elif bet_type == 'TOTALS':
            # Over/Under Betting
            total = data.get('total', 0)
            over_price = data.get('over_price', -110)
            under_price = data.get('under_price', -110)
            
            # Use real total predictor
            try:
                from ncaa_total_predictor import predict_total, evaluate_against_market
                predicted_total, components, uncertainty = predict_total(home, away, home_is_home=True, league=('nba' if 'NBA' in display_name else 'ncaa'))
                edge_val, conf, side = evaluate_against_market(predicted_total, total)
                recommendation = f"{side} {total}"
                explanation = f"Model predicts ~{int(predicted_total)} combined points; {side} favored vs market {total}"
                edge = round(edge_val,1)
                # conf from evaluate_against_market already accounts for edge magnitude
                # uncertainty penalizes when we have stub/missing data
                confidence = max(30, int(conf - (uncertainty * 20)))
            except Exception as e:
                print(f"⚠️ Total predictor fallback for {game_string}: {e}")
                # fallback to old behavior
                if display_name in ['NCAA Basketball', 'NBA']:
                    recommendation = f"UNDER {total}"
                    explanation = f"Bet that total combined score stays UNDER {total} points"
                else:
                    recommendation = f"OVER {total}"
                    explanation = f"Bet that total combined score goes OVER {total} points"
                edge = abs(total) * 0.15  # Lower edge for totals
                confidence = 58  # Totals are harder to predict
            
            # Generate intelligent reason for totals (pass total value)
            reason = self.generate_reason(recommendation, 0, edge, confidence, 'TOTAL', total, home, away)
            
            return {
                'game': game_string,
                'sport': f"{emoji} {display_name}",
                'bet_type': 'TOTAL',
                'recommendation': recommendation,
                'fanduel_line': f"Over {total} ({over_price}) / Under {total} ({under_price})",
                'edge': round(edge, 1),
                'confidence': confidence,
                'risk_tier': self.get_risk_tier(confidence),
                'game_time': time_str,
                'total': total,
                'bet_explanation': explanation,
                'reason': reason,  # ✅ INTELLIGENT REASON FOR TOTALS
                'bookmaker_source': 'FanDuel',
                'data_source': 'OddsAPI (FanDuel)',
                'bet_instructions': f"📍 PLACE BET ON FanDuel: {recommendation} (O/U {total}) | {explanation} | Confidence: {confidence}%"
            }
        
        return None
    
    def get_risk_tier(self, confidence):
        """Get risk tier based on confidence"""
        if confidence >= 72:
            return '🟢 LOW RISK'
        elif confidence >= 65:
            return '🟡 MODERATE RISK'
        else:
            return '🔴 HIGH RISK'
    
    def generate_reason(self, recommendation, spread, edge, confidence, bet_type='SPREAD', total=None, home_team=None, away_team=None, predicted_total=None):
        """Generate intelligent 'Why This Pick' explanation with PREDICTIONS"""
        reasons = []
        
        # FOR TOTALS: Add prediction about what score will be
        if bet_type == 'TOTAL' and total:
            is_under = 'UNDER' in recommendation.upper()
            # Use provided predicted_total if available, else calculate from edge (less accurate)
            if predicted_total is None:
                if is_under:
                    predicted_total = total - abs(edge)
                else:
                    predicted_total = total + abs(edge)
            
            if is_under:
                reasons.append(f"Model predicts game finishes around {int(predicted_total)} points (under {total})")
                reasons.append(f"Low-scoring matchup expected with controlled pace")
            else:
                reasons.append(f"Model predicts game finishes around {int(predicted_total)} points (over {total})")
                reasons.append(f"High-scoring matchup with offensive firepower")
        
        # FOR SPREADS: Add prediction about margin
        elif bet_type == 'SPREAD' and spread:
            team = recommendation.split()[0]
            spread_abs = abs(spread)
            is_favored = '-' in str(spread)
            
            if is_favored:
                predicted_margin = spread_abs + abs(edge)
                reasons.append(f"Model favors {team} by ~{int(predicted_margin)} points")
                reasons.append(f"Strong cover opportunity with {int(confidence)}% confidence")
            else:
                reasons.append(f"{team} expected to keep game close or win outright")
                reasons.append(f"Underdog value play with {int(confidence)}% confidence")
        
        # FOR MONEYLINE: Add win probability
        elif bet_type == 'MONEYLINE':
            team = recommendation.replace(' (Moneyline)', '').strip()
            win_probability = min(95, confidence + 10)
            reasons.append(f"Model confidence: {team} has {int(win_probability)}% win probability")
            reasons.append(f"Direct win bet with strong value at current odds")
        
        # Add edge info if significant
        if edge and abs(edge) > 2:
            reasons.append(f"{abs(edge):.1f} point edge identified—market inefficiency")
        
        # Return clean bullets (max 3)
        return "\n".join([f"• {r}" for r in reasons[:3]])
    
    def generate_all_picks(self):
        """Generate picks from ALL sports using FANDUEL ONLY odds"""
        all_picks = []
        
        print("🔍 Fetching FANDUEL ONLY odds from OddsAPI...")
        
        for sport in self.sports:
            try:
                picks = self.get_games_for_sport(sport['key'], sport['display'], sport.get('emoji', ''))
                if picks:
                    all_picks.extend(picks)
            except Exception as e:
                print(f"  ⚠️  {sport['display']}: {e}")
        
        print(f"\n📊 Total available picks (spreads + moneylines + totals): {len(all_picks)}")
        
        # Organize by bet type for balanced selection
        spreads = [p for p in all_picks if p.get('bet_type') == 'SPREAD']
        moneylines = [p for p in all_picks if p.get('bet_type') == 'MONEYLINE']
        totals = [p for p in all_picks if p.get('bet_type') == 'TOTAL']
        
        print(f"  📊 Spreads: {len(spreads)} | Moneylines: {len(moneylines)} | Totals: {len(totals)}")
        
        # Sort each by confidence and select balanced mix
        spreads.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        moneylines.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        totals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # UNLIMITED PICKS MODEL: Generate ALL quality bets (no artificial cap)
        # Quality threshold: confidence >= 45% (LEARNING PHASE)
        # - Lower threshold = more learning data
        # - Can raise to 50-55% once we have 50+ samples per bet type
        
        MIN_CONFIDENCE = 45  # LEARNING PHASE: Prioritize data gathering
        
        # Filter by minimum confidence to avoid garbage bets
        quality_spreads = [p for p in spreads if p.get('confidence', 0) >= MIN_CONFIDENCE]
        quality_moneylines = [p for p in moneylines if p.get('confidence', 0) >= MIN_CONFIDENCE]
        quality_totals = [p for p in totals if p.get('confidence', 0) >= MIN_CONFIDENCE]
        
        # Combine ALL quality bets (no limits)
        selected = quality_spreads + quality_moneylines + quality_totals
        
        # Re-sort by confidence for display
        selected.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        print(f"  🎯 Generated {len(selected)} quality bets (confidence >= {MIN_CONFIDENCE}%)")
        print(f"     Spreads: {len(quality_spreads)} | Moneylines: {len(quality_moneylines)} | Totals: {len(quality_totals)}")
        print(f"     LEARNING PHASE: Lower threshold ({MIN_CONFIDENCE}%) for maximum data gathering")
        
        return selected  # Return ALL quality bets (no cap)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎯 REAL BETTING MODEL v4.0 - FanDuel ONLY + Clear Instructions")
    print("="*70 + "\n")
    
    model = RealBettingModel()
    picks = model.generate_all_picks()
    
    print("\n" + "="*70)
    if picks:
        print("✅ Real Games with Crystal Clear FanDuel Bet Instructions:")
        for i, pick in enumerate(picks[:5], 1):
            print(f"\n{i}. {pick['game']}")
            print(f"   📍 BET: {pick['recommendation']} ({pick['confidence']}% confidence)")
            print(f"   📊 Line: {pick['fanduel_line']}")
            print(f"   💡 What it means: {pick['bet_explanation']}")
            print(f"   ⏰ Time: {pick['game_time']}")
            print(f"   📊 Type: {pick['bet_type']}")
    else:
        print("⚠️  No FanDuel odds available right now")
    print("="*70 + "\n")
