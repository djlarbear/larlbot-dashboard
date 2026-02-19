#!/usr/bin/env python3
"""
Adaptive Weight Updater v1.1
Adds Bayesian smoothing to stabilize weights for small sample sizes.
"""

import json
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s'
)
logger = logging.getLogger(__name__)

class AdaptiveWeightUpdater:
    def __init__(self, alpha=2.0, beta=2.0, min_sample_size=10):
        # Bayesian prior parameters (Beta distribution)
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.min_sample_size = int(min_sample_size)

        self.learning_file = 'learning_insights.json'
        self.weights_file = 'adaptive_weights.json'
        
    def calculate_weights(self):
        """Calculate new weights based on learning insights with Bayesian smoothing"""
        # Load learning insights
        try:
            with open(self.learning_file) as f:
                insights = json.load(f)
        except FileNotFoundError:
            logger.error("No learning_insights.json found")
            return None
        
        by_bet_type = insights.get('by_bet_type', {})
        overall_wr = insights.get('overall_win_rate', 50) / 100.0
        
        logger.info(f"Overall win rate: {insights.get('overall_win_rate')}%")
        logger.info("\nCalculating adaptive weights (Bayesian-smoothed)...\n")
        
        weights = {}
        
        for bet_type, stats in by_bet_type.items():
            raw_wr = stats.get('win_rate', 50) / 100.0
            count = int(stats.get('total', 0))
            # Reconstruct integer wins where possible for smoothing
            wins = int(round(raw_wr * count))

            # Log raw values
            logger.debug(f"{bet_type} raw: wins={wins}, total={count}, raw_wr={raw_wr:.3f}")

            # If not enough samples, skip updating and keep neutral weight
            if count < self.min_sample_size:
                logger.info(f"{bet_type}: sample_count={count} < min_sample_size={self.min_sample_size}; skipping weight update (keep neutral)")
                weights[bet_type] = {
                    'weight': 1.0,
                    'win_rate': round(raw_wr * 100, 1),
                    'sample_count': count,
                    'adjustment': 0.0,
                    'stability_factor': 0.0,
                    'confidence_level': 'INSUFFICIENT',
                    'smoothing': {
                        'raw_win_rate': round(raw_wr * 100, 2),
                        'smoothed_win_rate': None,
                        'alpha': self.alpha,
                        'beta': self.beta
                    }
                }
                continue

            # Bayesian smoothing: Beta(alpha, beta) prior
            smoothed_wr = (wins + self.alpha) / (count + self.alpha + self.beta)

            # Calculate adjustment relative to overall (use smoothed win rate)
            adjustment = (smoothed_wr - overall_wr) * 2.0

            # Stability factor scaling (conservative ramping)
            if count < 20:
                stability_factor = 0.0
                confidence_level = 'LIMITED'
            elif count < 30:
                stability_factor = (count - 20) / 10.0
                confidence_level = 'LIMITED'
            else:
                stability_factor = 1.0
                confidence_level = 'HIGH'

            weight = 1.0 + (adjustment * stability_factor)
            # Bounds
            weight = max(0.3, min(2.0, weight))

            weights[bet_type] = {
                'weight': round(weight, 2),
                'win_rate': round(smoothed_wr * 100, 2),
                'sample_count': count,
                'adjustment': round(adjustment, 3),
                'stability_factor': round(stability_factor, 2),
                'confidence_level': confidence_level,
                'smoothing': {
                    'raw_win_rate': round(raw_wr * 100, 2),
                    'smoothed_win_rate': round(smoothed_wr * 100, 2),
                    'alpha': self.alpha,
                    'beta': self.beta
                }
            }

            # Log the smoothing effect for transparency
            logger.info(f"{bet_type}:")
            logger.info(f"  Raw win rate: {raw_wr*100:.1f}% (wins={wins}, n={count})")
            logger.info(f"  Smoothed win rate: {smoothed_wr*100:.2f}% using Beta({self.alpha},{self.beta})")
            logger.info(f"  Adjustment (post-smoothing): {adjustment:.3f}")
            logger.info(f"  Stability: {stability_factor:.2f} -> weight: {weight:.2f}\n")
        
        return weights
    
    def validate_weights(self, weights):
        """Validate weight data types and ranges to prevent runtime errors
        
        Args:
            weights: Dictionary of bet type weights
            
        Returns:
            dict: Validated and corrected weights
        """
        validated = {}
        
        for bet_type, data in weights.items():
            try:
                # Validate weight value
                weight = data.get('weight', 1.0)
                if not isinstance(weight, (int, float)):
                    logger.warning(f"⚠️ {bet_type}: Invalid weight type {type(weight)}, using 1.0")
                    weight = 1.0
                
                # Clamp weight to valid range [0.3, 2.0]
                if weight < 0.3 or weight > 2.0:
                    logger.warning(f"⚠️ {bet_type}: Weight {weight} out of bounds [0.3, 2.0], clamping")
                    weight = max(0.3, min(2.0, weight))
                
                # Validate sample count
                sample_count = data.get('sample_count', 0)
                if not isinstance(sample_count, int) or sample_count < 0:
                    logger.error(f"❌ {bet_type}: Invalid sample count {sample_count}, setting to 0")
                    sample_count = 0
                
                # Validate win rate
                win_rate = data.get('win_rate', 0.0)
                if not isinstance(win_rate, (int, float)) or win_rate < 0 or win_rate > 100:
                    logger.warning(f"⚠️ {bet_type}: Invalid win rate {win_rate}, setting to 0")
                    win_rate = 0.0
                
                # Validate stability factor
                stability_factor = data.get('stability_factor', 0.0)
                if not isinstance(stability_factor, (int, float)) or stability_factor < 0 or stability_factor > 1:
                    logger.warning(f"⚠️ {bet_type}: Invalid stability {stability_factor}, clamping to [0, 1]")
                    stability_factor = max(0.0, min(1.0, stability_factor))
                
                # Rebuild validated data
                validated[bet_type] = {
                    'weight': round(float(weight), 2),
                    'win_rate': round(float(win_rate), 2),
                    'sample_count': int(sample_count),
                    'adjustment': data.get('adjustment', 0.0),
                    'stability_factor': round(float(stability_factor), 2),
                    'confidence_level': data.get('confidence_level', 'UNKNOWN')
                }
                
            except Exception as e:
                logger.error(f"❌ {bet_type}: Validation error {e}, using defaults")
                validated[bet_type] = {
                    'weight': 1.0,
                    'win_rate': 0.0,
                    'sample_count': 0,
                    'adjustment': 0.0,
                    'stability_factor': 0.0,
                    'confidence_level': 'INVALID'
                }
        
        return validated
    
    def save_weights(self, weights):
        """Save weights to file with validation"""
        # Validate before saving
        validated_weights = self.validate_weights(weights)
        
        data = {
            'generated_at': datetime.now().isoformat(),
            'source': 'learning_insights.json',
            'weights': validated_weights,
            'instructions': 'Use these weights in bet_ranker.py when calculating LARLScore'
        }
        
        with open(self.weights_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"\n✅ Weights validated and saved to {self.weights_file}")
    
    def apply_confidence_calibration(self):
        """Apply confidence calibration from learning insights"""
        try:
            with open(self.learning_file) as f:
                insights = json.load(f)
        except FileNotFoundError:
            return None
        
        by_confidence = insights.get('by_confidence', {})
        
        logger.info("=" * 60)
        logger.info("CONFIDENCE CALIBRATION ADJUSTMENTS")
        logger.info("=" * 60 + "\n")
        
        calibration = {}
        
        for conf_range, stats in by_confidence.items():
            actual_wr = stats.get('win_rate', 50) / 100.0
            
            # Extract midpoint of confidence range
            if conf_range == '90-100%':
                target_conf = 95
            elif conf_range == '80-89%':
                target_conf = 85
            elif conf_range == '70-79%':
                target_conf = 75
            elif conf_range == '60-69%':
                target_conf = 65
            elif conf_range == '50-59%':
                target_conf = 55
            else:
                continue
            
            # Calibration adjustment
            expected_wr = target_conf / 100.0
            adjustment = actual_wr - expected_wr
            
            # Reduce confidence by the adjustment gap
            new_conf = target_conf + (adjustment * 100)
            new_conf = max(50, min(100, new_conf))
            
            calibration[conf_range] = {
                'original_confidence': target_conf,
                'actual_win_rate': round(actual_wr * 100, 1),
                'expected_win_rate': round(expected_wr * 100, 1),
                'adjustment': round(adjustment * 100, 1),
                'recommended_confidence': round(new_conf, 0)
            }
            
            logger.info(f"{conf_range}:")
            logger.info(f"  Actual: {stats.get('win_rate'):.1f}%")
            logger.info(f"  Expected: {target_conf}%")
            logger.info(f"  Adjustment: {adjustment*100:.1f}%")
            logger.info(f"  → Recommend reducing to: {new_conf:.0f}%\n")
        
        # Save calibration
        with open('confidence_calibration.json', 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'calibration': calibration,
                'instructions': 'Apply these adjustments when generating picks'
            }, f, indent=2)
        
        logger.info(f"✅ Calibration saved to confidence_calibration.json\n")
        
        return calibration

if __name__ == '__main__':
    updater = AdaptiveWeightUpdater()
    
    logger.info("=" * 60)
    logger.info("🧠 ADAPTIVE WEIGHT CALCULATOR")
    logger.info("=" * 60 + "\n")
    
    weights = updater.calculate_weights()
    if weights:
        updater.save_weights(weights)
        updater.apply_confidence_calibration()
        
        logger.info("=" * 60)
        logger.info("READY FOR PICK GENERATION")
        logger.info("=" * 60)
