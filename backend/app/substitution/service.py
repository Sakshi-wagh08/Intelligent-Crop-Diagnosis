import re
import math
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from geoalchemy2.shape import to_shape

from backend.app.models.merchant import Merchant, Product
from backend.app.models.chemical import ActiveIngredient
from backend.app.schemas.substitution import (
    SubstituteAndRankRequest,
    SubstituteAndRankResponse,
    RankedProductOffering,
    IneligibleProductOffering,
    ScoreBreakdown,
    RankingWeights,
    SubstitutionCalculationRequest,
    SubstitutionCalculationResponse,
)
from backend.app.substitution.engine import ProductSubstitutionEngine
from backend.app.substitution.ranking import MerchantProductRanker
from backend.app.substitution.exceptions import (
    SubstitutionError,
    IncompatibleConcentrationUnitError,
    InvalidDosageError,
)

logger = logging.getLogger(__name__)

DEMO_MERCHANT_DISCLAIMER = (
    "DEMONSTRATION NOTICE: Agro-dealer profiles, product inventory, and pricing returned by this "
    "system are synthetic demonstration records created strictly for academic research and software testing. "
    "They do NOT represent verified commercial retail locations or real-time inventory. "
    "Farmers must verify actual stock, physical label claims, and pricing with certified local agricultural input dealers."
)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in kilometers."""
    r_earth = 6371.0  # Earth mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r_earth * c, 3)


class SubstitutionService:
    """Orchestrates geospatial merchant discovery, product eligibility screening,

    chemical concentration substitution, and multi-factor dealer ranking.
    """

    @classmethod
    def get_merchants_within_radius(
        cls,
        db: Session,
        latitude: float,
        longitude: float,
        max_distance_km: float,
        allow_demo: bool = True,
    ) -> List[Tuple[Merchant, float]]:
        """Queries merchants within max_distance_km using PostGIS GiST or Haversine fallback."""
        if max_distance_km <= 0.0:
            return []

        merchants_with_distance: List[Tuple[Merchant, float]] = []
        bind_dialect = getattr(db.bind, "dialect", None)
        is_postgres = getattr(bind_dialect, "name", "") == "postgresql"

        if is_postgres:
            try:
                max_meters = max_distance_km * 1000.0
                query_sql = """
                    SELECT 
                        m.id,
                        ROUND((ST_Distance(m.location_geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000.0)::numeric, 3) AS distance_km
                    FROM merchants m
                    WHERE m.is_active = TRUE
                      AND ST_DWithin(m.location_geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :max_meters)
                    ORDER BY distance_km ASC
                """
                rows = db.execute(text(query_sql), {"lon": longitude, "lat": latitude, "max_meters": max_meters}).fetchall()
                merchant_ids = [r[0] for r in rows]
                dist_map = {r[0]: float(r[1]) for r in rows}

                if merchant_ids:
                    merchants = db.query(Merchant).filter(Merchant.id.in_(merchant_ids)).all()
                    for m in merchants:
                        if not allow_demo and m.is_demo:
                            continue
                        merchants_with_distance.append((m, dist_map[m.id]))

                merchants_with_distance.sort(key=lambda x: x[1])
                return merchants_with_distance
            except Exception as e:
                logger.warning("PostGIS spatial query failed, falling back to python Haversine: %s", e)

        # Python Haversine fallback for SQLite and non-PostGIS test harnesses
        merchants = db.query(Merchant).filter(Merchant.is_active == True).all()
        for m in merchants:
            if not allow_demo and m.is_demo:
                continue

            m_lat, m_lon = None, None
            try:
                if hasattr(m.location_geom, "data"):
                    shape = to_shape(m.location_geom)
                    m_lon, m_lat = shape.x, shape.y
            except Exception:
                pass

            if m_lat is None or m_lon is None:
                geom_str = str(m.location_geom)
                match = re.search(r"point\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", geom_str, re.IGNORECASE)
                if match:
                    m_lon, m_lat = float(match.group(1)), float(match.group(2))

            if m_lat is not None and m_lon is not None:
                dist = haversine_distance(latitude, longitude, m_lat, m_lon)
                if dist <= max_distance_km:
                    merchants_with_distance.append((m, dist))

        merchants_with_distance.sort(key=lambda x: x[1])
        return merchants_with_distance

    @classmethod
    def substitute_and_rank(
        cls,
        db: Session,
        request: SubstituteAndRankRequest,
    ) -> SubstituteAndRankResponse:
        """Executes full localized merchant discovery, product eligibility checks,

        substitute dose calculation Qs = Qr * (Cr / Cs), and multi-criteria ranking.
        """
        if request.max_distance_km <= 0.0:
            raise InvalidDosageError(f"Search radius max_distance_km must be > 0.0, got {request.max_distance_km}")

        weights = request.weights or RankingWeights()

        # Step 1: Discover nearby merchants within search radius
        merchants_nearby = cls.get_merchants_within_radius(
            db=db,
            latitude=request.latitude,
            longitude=request.longitude,
            max_distance_km=request.max_distance_km,
            allow_demo=request.allow_demo,
        )

        if not merchants_nearby:
            return SubstituteAndRankResponse(
                status="NO_MERCHANTS_WITHIN_RADIUS",
                message=f"No active agricultural input dealers found within {request.max_distance_km} km of coordinates ({request.latitude}, {request.longitude}).",
                farmer_location={"latitude": request.latitude, "longitude": request.longitude},
                search_radius_km=request.max_distance_km,
                target_crop=request.crop_name,
                target_disease=request.disease_name,
                reference_active_ingredient=request.active_ingredient,
                reference_dose_Qr=request.reference_dose_Qr,
                reference_dose_unit=request.reference_dose_unit,
                reference_concentration_Cr=request.reference_concentration_Cr,
                field_area_acres=request.field_area_acres,
                total_merchants_searched=0,
                total_eligible_products=0,
                ranked_offerings=[],
                ineligible_candidates=[],
                weights_configured={"price": weights.price, "distance": weights.distance, "stock": weights.stock},
                demonstration_advisory=DEMO_MERCHANT_DISCLAIMER,
            )

        # Step 2: Screen merchant products for active ingredient match and eligibility
        candidate_items: List[Dict[str, Any]] = []
        ineligible_items: List[IneligibleProductOffering] = []

        for merchant, distance_km in merchants_nearby:
            for product in merchant.products:
                # Active ingredient name check
                ai_name = product.active_ingredient.common_name if product.active_ingredient else ""
                if ai_name.strip().lower() != request.active_ingredient.strip().lower():
                    continue  # Ignore products with completely different chemicals

                # Verify eligibility (Registration, Formulation, Crop/Disease registration)
                is_eligible, reason = ProductSubstitutionEngine.evaluate_product_eligibility(
                    product_brand=product.brand_name,
                    product_active_ingredient=ai_name,
                    product_formulation=product.formulation_type,
                    is_legally_registered=product.is_legally_registered,
                    registration_number=product.registration_number,
                    registered_crops=product.registered_crops,
                    registered_diseases=product.registered_diseases,
                    required_active_ingredient=request.active_ingredient,
                    target_crop=request.crop_name,
                    target_disease=request.disease_name,
                    prescribed_application_method=request.prescribed_application_method,
                )

                if not is_eligible:
                    ineligible_items.append(
                        IneligibleProductOffering(
                            merchant_id=merchant.id,
                            merchant_name=merchant.name,
                            product_id=product.id,
                            brand_name=product.brand_name,
                            active_ingredient=ai_name,
                            distance_km=distance_km,
                            ineligibility_reason=reason,
                        )
                    )
                    continue

                # Check retail price validity
                if product.price is None or float(product.price) <= 0.0:
                    ineligible_items.append(
                        IneligibleProductOffering(
                            merchant_id=merchant.id,
                            merchant_name=merchant.name,
                            product_id=product.id,
                            brand_name=product.brand_name,
                            active_ingredient=ai_name,
                            distance_km=distance_km,
                            ineligibility_reason=f"Invalid or unlisted product retail price ({product.price})",
                        )
                    )
                    continue

                # Check inventory: Out of stock or missing stock products cannot be ranked
                if product.stock_quantity is None or product.stock_quantity <= 0:
                    ineligible_items.append(
                        IneligibleProductOffering(
                            merchant_id=merchant.id,
                            merchant_name=merchant.name,
                            product_id=product.id,
                            brand_name=product.brand_name,
                            active_ingredient=ai_name,
                            distance_km=distance_km,
                            ineligibility_reason=f"Out of stock ({product.stock_quantity or 0} retail packs available at dealer)",
                        )
                    )
                    continue

                # Step 3: Compute substitute dosage Qs = Qr * (Cr / Cs) with basis reconciliation
                try:
                    substitute_dose_Qs, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
                        reference_dose_Qr=request.reference_dose_Qr,
                        reference_concentration_Cr=request.reference_concentration_Cr,
                        substitute_concentration_Cs=product.concentration_Cs,
                        reference_unit_Cr="%",
                        substitute_unit_Cs=product.concentration_unit or "%",
                        substitute_formulation=product.formulation_type,
                        reference_dose_unit=request.reference_dose_unit,
                    )
                except IncompatibleConcentrationUnitError as icu:
                    ineligible_items.append(
                        IneligibleProductOffering(
                            merchant_id=merchant.id,
                            merchant_name=merchant.name,
                            product_id=product.id,
                            brand_name=product.brand_name,
                            active_ingredient=ai_name,
                            distance_km=distance_km,
                            ineligibility_reason=str(icu),
                        )
                    )
                    continue

                # Step 4: Compute package count and total purchase cost with mass/volume checks
                try:
                    total_qty, packs_needed, pack_desc = ProductSubstitutionEngine.calculate_required_packages(
                        substitute_dose_Qs=substitute_dose_Qs,
                        field_area_acres=request.field_area_acres,
                        package_size_str=product.package_size,
                        dose_unit=request.reference_dose_unit,
                    )
                except IncompatibleConcentrationUnitError as icu_pack:
                    ineligible_items.append(
                        IneligibleProductOffering(
                            merchant_id=merchant.id,
                            merchant_name=merchant.name,
                            product_id=product.id,
                            brand_name=product.brand_name,
                            active_ingredient=ai_name,
                            distance_km=distance_km,
                            ineligibility_reason=str(icu_pack),
                        )
                    )
                    continue

                total_cost = round(packs_needed * float(product.price), 2)

                candidate_items.append({
                    "merchant": merchant,
                    "product": product,
                    "distance_km": distance_km,
                    "substitute_dose_Qs": substitute_dose_Qs,
                    "concentration_ratio": ratio,
                    "total_quantity": total_qty,
                    "packs_needed": packs_needed,
                    "pack_desc": pack_desc,
                    "total_cost": total_cost,
                })

        if not candidate_items:
            return SubstituteAndRankResponse(
                status="NO_ELIGIBLE_PRODUCTS",
                message=(
                    f"Found {len(merchants_nearby)} merchants within {request.max_distance_km} km, "
                    f"but no eligible in-stock substitute formulation was found for {request.active_ingredient} "
                    f"registered on {request.crop_name} {request.disease_name}."
                ),
                farmer_location={"latitude": request.latitude, "longitude": request.longitude},
                search_radius_km=request.max_distance_km,
                target_crop=request.crop_name,
                target_disease=request.disease_name,
                reference_active_ingredient=request.active_ingredient,
                reference_dose_Qr=request.reference_dose_Qr,
                reference_dose_unit=request.reference_dose_unit,
                reference_concentration_Cr=request.reference_concentration_Cr,
                field_area_acres=request.field_area_acres,
                total_merchants_searched=len(merchants_nearby),
                total_eligible_products=0,
                ranked_offerings=[],
                ineligible_candidates=ineligible_items,
                weights_configured={"price": weights.price, "distance": weights.distance, "stock": weights.stock},
                demonstration_advisory=DEMO_MERCHANT_DISCLAIMER,
            )

        # Step 5: Normalize criteria and compute multi-criteria ranking scores
        costs = [c["total_cost"] for c in candidate_items]
        min_cost = min(costs)
        max_cost = max(costs)

        scored_candidates = []
        for c in candidate_items:
            p_score = MerchantProductRanker.normalize_price(c["total_cost"], min_cost, max_cost)
            d_score = MerchantProductRanker.normalize_distance(c["distance_km"], request.max_distance_km)
            s_score = MerchantProductRanker.normalize_stock(c["product"].stock_quantity, c["packs_needed"])

            comp_score = MerchantProductRanker.compute_composite_score(
                price_score=p_score,
                distance_score=d_score,
                stock_score=s_score,
                weights=weights,
            )

            scored_candidates.append({
                **c,
                "price_score": p_score,
                "distance_score": d_score,
                "stock_score": s_score,
                "composite_score": comp_score,
            })

        # Sort candidates descending by composite score, then by distance ascending
        scored_candidates.sort(key=lambda x: (x["composite_score"], -x["distance_km"]), reverse=True)

        # Step 6: Assemble ranked offerings with explanations
        ranked_offerings: List[RankedProductOffering] = []
        for idx, item in enumerate(scored_candidates, start=1):
            m = item["merchant"]
            p = item["product"]

            explanation = MerchantProductRanker.generate_explanation(
                rank=idx,
                brand_name=p.brand_name,
                merchant_name=m.name,
                total_cost=item["total_cost"],
                distance_km=item["distance_km"],
                stock_qty=p.stock_quantity,
                packages_needed=item["packs_needed"],
                price_score=item["price_score"],
                distance_score=item["distance_score"],
                stock_score=item["stock_score"],
            )

            score_breakdown = ScoreBreakdown(
                price_score=item["price_score"],
                distance_score=item["distance_score"],
                stock_score=item["stock_score"],
                weights_applied={
                    "price": weights.price,
                    "distance": weights.distance,
                    "stock": weights.stock,
                },
            )

            ranked_offerings.append(
                RankedProductOffering(
                    rank=idx,
                    composite_score=item["composite_score"],
                    merchant_id=m.id,
                    merchant_name=m.name,
                    contact_phone=m.contact_phone,
                    address=m.address,
                    distance_km=item["distance_km"],
                    product_id=p.id,
                    brand_name=p.brand_name,
                    active_ingredient=p.active_ingredient.common_name,
                    concentration_Cs=p.concentration_Cs,
                    concentration_unit=p.concentration_unit or "%",
                    formulation_type=p.formulation_type,
                    package_size=p.package_size,
                    unit_price=float(p.price),
                    currency=p.currency,
                    stock_quantity=p.stock_quantity,
                    registration_number=p.registration_number,
                    is_legally_registered=p.is_legally_registered,
                    substitute_dose_Qs=item["substitute_dose_Qs"],
                    dose_unit=request.reference_dose_unit,
                    packages_needed=item["packs_needed"],
                    estimated_total_cost=item["total_cost"],
                    score_breakdown=score_breakdown,
                    ranking_explanation=explanation,
                    is_demo=bool(m.is_demo or p.is_demo),
                )
            )

        return SubstituteAndRankResponse(
            status="SUCCESS",
            message=(
                f"Successfully discovered {len(merchants_nearby)} nearby agro-dealers and ranked "
                f"{len(ranked_offerings)} eligible substitute product formulations."
            ),
            farmer_location={"latitude": request.latitude, "longitude": request.longitude},
            search_radius_km=request.max_distance_km,
            target_crop=request.crop_name,
            target_disease=request.disease_name,
            reference_active_ingredient=request.active_ingredient,
            reference_dose_Qr=request.reference_dose_Qr,
            reference_dose_unit=request.reference_dose_unit,
            reference_concentration_Cr=request.reference_concentration_Cr,
            field_area_acres=request.field_area_acres,
            total_merchants_searched=len(merchants_nearby),
            total_eligible_products=len(ranked_offerings),
            ranked_offerings=ranked_offerings,
            ineligible_candidates=ineligible_items,
            weights_configured={"price": weights.price, "distance": weights.distance, "stock": weights.stock},
            demonstration_advisory=DEMO_MERCHANT_DISCLAIMER,
        )

    @classmethod
    def calculate_standalone_substitution(
        cls,
        request: SubstitutionCalculationRequest,
    ) -> SubstitutionCalculationResponse:
        """Computes standalone chemical active ingredient substitution without spatial queries."""
        substitute_dose_Qs, ratio = ProductSubstitutionEngine.calculate_substitute_dose(
            reference_dose_Qr=request.reference_dose_Qr,
            reference_concentration_Cr=request.reference_concentration_Cr,
            substitute_concentration_Cs=request.substitute_concentration_Cs,
            reference_unit_Cr=request.concentration_unit_Cr,
            substitute_unit_Cs=request.concentration_unit_Cs,
            reference_dose_unit=request.reference_dose_unit,
        )

        total_qty, packs_needed, pack_desc = ProductSubstitutionEngine.calculate_required_packages(
            substitute_dose_Qs=substitute_dose_Qs,
            field_area_acres=request.field_area_acres,
            package_size_str=request.package_size_str,
            dose_unit=request.reference_dose_unit,
        )

        total_cost = None
        if request.product_price is not None:
            total_cost = round(packs_needed * request.product_price, 2)

        explanation = (
            f"Reference active ingredient concentration Cr = {request.reference_concentration_Cr}% adjusted to "
            f"substitute formulation concentration Cs = {request.substitute_concentration_Cs}%. "
            f"Concentration ratio (Cr / Cs) = {ratio:.4f}. "
            f"Substitute dose Qs = {request.reference_dose_Qr} * {ratio:.4f} = {substitute_dose_Qs} {request.reference_dose_unit}."
        )

        return SubstitutionCalculationResponse(
            reference_dose_Qr=request.reference_dose_Qr,
            reference_concentration_Cr=request.reference_concentration_Cr,
            substitute_concentration_Cs=request.substitute_concentration_Cs,
            concentration_ratio=ratio,
            substitute_dose_Qs=substitute_dose_Qs,
            dose_unit=request.reference_dose_unit,
            field_area_acres=request.field_area_acres,
            total_substitute_quantity=total_qty,
            package_size_parsed=pack_desc,
            packages_needed=packs_needed,
            estimated_total_cost=total_cost,
            currency="INR",
            formula_expression="Qs = Qr * (Cr / Cs)",
            explanation=explanation,
        )
