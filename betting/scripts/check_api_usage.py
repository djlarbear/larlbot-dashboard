#!/usr/bin/env python3
"""
Quick check of OddsAPI usage
"""

from oddsapi_rate_limiter import OddsAPIRateLimiter
import sys

limiter = OddsAPIRateLimiter()

# Print status
limiter.print_status()

# Get status dict for scripting
status = limiter.get_status()

# Exit with warning code if usage high
if status['usage_percentage'] > 80:
    print("\n🚨 ACTION REQUIRED: Reduce API usage!")
    sys.exit(2)
elif status['usage_percentage'] > 50:
    print("\n⚠️  Monitor usage closely")
    sys.exit(1)
else:
    print("\n✅ Usage is healthy")
    sys.exit(0)
