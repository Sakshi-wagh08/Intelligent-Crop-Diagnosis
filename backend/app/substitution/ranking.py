import logging
from typing import List, Optional, Dict, Any, Tuple
from backend.app.schemas.substitution import RankingWeights, ScoreBreakdown

logger = logging.getLogger(__name__)


class MerchantProductRanker:
    """Computes normalized multi-factor ranking scores for eligible merchant-product pairings.

    Multi-Criteria Utility:
        Score = (wp * PriceScore + wd * DistanceScore + ws * StockScore) / (wp + wd + ws)

    Criteria Direction:
    - Price: Lower cost yields higher utility (affordability maximization).
    - Distance: Closer distance yields higher utility (travel minimization).
    - Stock: Sufficient inventory yields higher utility (fulfillment certainty).
    """

    @classmethod
    def normalize_price(cls, price: Optional[float], min_price: float, max_price: float) -> float:
        """Normalizes cost utility between 0.0 (most expensive) and 1.0 (least expensive)."""
        if price is None or price <= 0.0:
            return 0.0
        if max_price <= min_price:
            return 1.0
        val = 1.0 - ((price - min_price) / (max_price - min_price))
        return round(max(0.0, min(1.0, val)), 4)

    @classmethod
    def normalize_distance(cls, distance_km: float, max_search_radius_km: float) -> float:
        """Normalizes geographic proximity utility between 0.0 (at boundary) and 1.0 (at origin)."""
        if max_search_radius_km <= 0.0:
            return 1.0
        if distance_km <= 0.0:
            return 1.0
        val = 1.0 - (distance_km / max_search_radius_km)
        return round(max(0.0, min(1.0, val)), 4)

    @classmethod
    def normalize_stock(cls, stock_quantity: Optional[int], packages_needed: int) -> float:
        """Normalizes stock fulfillment utility between 0.0 (out of stock) and 1.0 (sufficient)."""
        if stock_quantity is None or stock_quantity <= 0:
            return 0.0
        if packages_needed <= 0:
            return 1.0
        if stock_quantity >= packages_needed:
            return 1.0
        val = float(stock_quantity) / float(packages_needed)
        return round(max(0.0, min(1.0, val)), 4)

    @classmethod
    def compute_composite_score(
        cls,
        price_score: float,
        distance_score: float,
        stock_score: float,
        weights: RankingWeights,
    ) -> float:
        """Calculates normalized composite weighted score."""
        w_sum = weights.price + weights.distance + weights.stock
        if w_sum <= 0.0:
            w_sum = 1.0

        # Normalized weights ensuring exact sum to 1.0
        wp = weights.price / w_sum
        wd = weights.distance / w_sum
        ws = weights.stock / w_sum

        weighted_sum = (wp * price_score) + (wd * distance_score) + (ws * stock_score)
        return round(weighted_sum, 4)

    @classmethod
    def generate_explanation(
        cls,
        rank: int,
        brand_name: str,
        merchant_name: str,
        total_cost: float,
        distance_km: float,
        stock_qty: Optional[int],
        packages_needed: int,
        price_score: float,
        distance_score: float,
        stock_score: float,
    ) -> str:
        """Constructs an explainable summary of why the dealer and product were recommended."""
        reasons = []

        if price_score >= 0.80:
            reasons.append(f"highly competitive price (INR {total_cost:.2f})")
        elif price_score >= 0.50:
            reasons.append(f"moderate price (INR {total_cost:.2f})")
        else:
            reasons.append(f"premium price (INR {total_cost:.2f})")

        if distance_score >= 0.75:
            reasons.append(f"very close proximity ({distance_km:.1f} km)")
        elif distance_score >= 0.40:
            reasons.append(f"moderate travel distance ({distance_km:.1f} km)")
        else:
            reasons.append(f"outer search boundary ({distance_km:.1f} km)")

        actual_stock = stock_qty if stock_qty is not None else 0
        if actual_stock >= packages_needed:
            reasons.append(f"full inventory availability ({actual_stock} packs in stock vs {packages_needed} required)")
        elif actual_stock > 0:
            reasons.append(f"partial inventory ({actual_stock} packs in stock vs {packages_needed} required)")
        else:
            reasons.append("currently out of stock")

        explanation_str = f"Ranked #{rank}: Selected for {', '.join(reasons)}."
        return explanation_str
