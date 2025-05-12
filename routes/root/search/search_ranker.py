# Part 1: Normalize popularity counts
import math
from datetime import datetime, timedelta

from pymongo import UpdateOne


class RealTimeSearchRanker:
    # def __init__(self, decay_per_hour=0.1, k=0.5, theta=3, recency_bonus=2):          # OG
    def __init__(self, decay_per_hour=0.1, k=100, theta=2/3, recency_bonus=2):
        self.decay_per_second = 1 - (1 - decay_per_hour) ** (1/3600)  # Convert hourly decay to per-second
        self.k = k                  # caps highest rate. 100 caps it to 10
        self.theta = theta          # for increase in theta the curve steepens goof for giving popularity boost for lower conts
        self.recency_bonus = recency_bonus      # adds to the count
        self.searches = {}  # Format: {'query': {'hits': float, 'last_updated': datetime}}

    def compressed_sigmoid(self, x):
        # sigmoid = 1 / (1 + math.exp(-self.k * (x - self.theta)))              # OG
        sigmoid = math.sqrt(1 / ((1/self.k) + math.exp(-(x * self.theta))))
        return int(sigmoid*3)

    def log_search(self, query):
        now = datetime.now()
        is_new = query not in self.searches

        # Apply exponential decay based on seconds since last update
        if not is_new:
            elapsed_seconds = (now - self.searches[query]['last_updated']).total_seconds()
            decay_factor = math.exp(-self.decay_per_second * elapsed_seconds)
            self.searches[query]['hits'] *= decay_factor
            self.searches[query]['hits'] += 1
        else:       # if new query, add recency bonus and last updated.
            self.searches[query] = {'hits': 1 + self.recency_bonus, 'last_updated': now}

        self.searches[query]['last_updated'] = now
        return self.compressed_sigmoid(self.searches[query]['hits'])

    def get_suggestions(self, prefix="", limit=5):
        """Get suggestions with sub-second precision decay"""
        current_time = datetime.now()
        scored = []
        
        for query, data in self.searches.items():
            if prefix.lower() in query.lower():
                # Recalculate decay for exact current moment
                elapsed_seconds = (current_time - data['last_updated']).total_seconds()
                decayed_hits = data['hits'] * math.exp(-self.decay_per_second * elapsed_seconds)
                scored.append((query, self.compressed_sigmoid(decayed_hits)))
        
        return sorted(scored, key=lambda x: x[1], reverse=True)[:limit]
    


