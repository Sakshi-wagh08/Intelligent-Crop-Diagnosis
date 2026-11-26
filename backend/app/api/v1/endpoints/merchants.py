import math
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from geoalchemy2.shape import to_shape

from backend.app.db.session import get_db, check_database_connection
from backend.app.models.merchant import Merchant, Product
from backend.app.schemas.merchant import NearbyMerchantResponse, MerchantResponse, ProductResponse
from backend.app.schemas.substitution import (
    SubstitutionCalculationRequest,
    SubstitutionCalculationResponse,
    SubstituteAndRankRequest,
    SubstituteAndRankResponse,
    RankingWeights,
)
from backend.app.substitution.service import SubstitutionService, haversine_distance
from backend.app.substitution.exceptions import SubstitutionError
from backend.app.core.logging import logger

router = APIRouter()


def _extract_coordinates(geom) -> tuple[Optional[float], Optional[float]]:
    """Helper to extract (latitude, longitude) from WKT or GeoAlchemy2 Geometry."""
    lat, lon = None, None
    try:
        if hasattr(geom, "data"):
            shape = to_shape(geom)
            lon, lat = shape.x, shape.y
            return lat, lon
    except Exception:
        pass

    geom_str = str(geom)
    match = re.search(r"point\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", geom_str, re.IGNORECASE)
    if match:
        lon, lat = float(match.group(1)), float(match.group(2))
    return lat, lon


@router.get("/nearby", response_model=List[NearbyMerchantResponse], summary="Spatial Nearby Merchant Search")
def get_nearby_merchants(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Farmer field latitude"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Farmer field longitude"),
    max_distance_km: float = Query(25.0, gt=0, le=200.0, description="Maximum search radius in kilometers (d_max)"),
    active_ingredient_id: Optional[int] = Query(None, description="Optional filter by required active chemical ingredient"),
    db: Session = Depends(get_db)
) -> List[NearbyMerchantResponse]:
    """Queries agro-dealers within spatial radius d_max using PostGIS or fallback spatial calculation."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning(f"Database unavailable for nearby merchants search: {exc}")
        return []

    results: List[NearbyMerchantResponse] = []
    bind_dialect = getattr(db.bind, "dialect", None)
    is_postgres = getattr(bind_dialect, "name", "") == "postgresql"

    # 1. Native PostGIS spatial radius query when executing on PostgreSQL
    if is_postgres:
        try:
            max_meters = max_distance_km * 1000.0
            query_sql = """
                SELECT 
                    m.id AS merchant_id,
                    m.name AS merchant_name,
                    m.contact_phone,
                    m.address,
                    ROUND((ST_Distance(m.location_geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) / 1000.0)::numeric, 2) AS distance_km,
                    p.id AS product_id,
                    p.brand_name,
                    p.concentration_Cs,
                    p.price,
                    p.stock_quantity,
                    m.is_demo
                FROM merchants m
                LEFT JOIN products p ON p.merchant_id = m.id AND p.is_legally_registered = TRUE
                WHERE m.is_active = TRUE
                  AND ST_DWithin(m.location_geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :max_meters)
            """
            params = {"lon": longitude, "lat": latitude, "max_meters": max_meters}
            if active_ingredient_id:
                query_sql += " AND p.active_ingredient_id = :active_ingredient_id"
                params["active_ingredient_id"] = active_ingredient_id

            query_sql += " ORDER BY distance_km ASC"

            rows = db.execute(text(query_sql), params).fetchall()
            for row in rows:
                results.append(
                    NearbyMerchantResponse(
                        merchant_id=row.merchant_id,
                        merchant_name=row.merchant_name,
                        contact_phone=row.contact_phone,
                        address=row.address,
                        distance_km=float(row.distance_km),
                        product_id=row.product_id,
                        brand_name=row.brand_name,
                        concentration_Cs=float(row.concentration_cs) if row.concentration_cs is not None else None,
                        price=float(row.price) if row.price is not None else None,
                        stock_quantity=row.stock_quantity,
                        is_demo=bool(row.is_demo),
                    )
                )
            return results
        except Exception as e:
            logger.warning(f"PostGIS spatial query failed, falling back to python spatial filter: {e}")

    # 2. Python Haversine fallback engine for test environments and non-PostGIS backends
    try:
        merchants = db.query(Merchant).filter(Merchant.is_active == True).all()
        for m in merchants:
            m_lat, m_lon = _extract_coordinates(m.location_geom)

            if m_lat is not None and m_lon is not None:
                dist = haversine_distance(latitude, longitude, m_lat, m_lon)
                if dist <= max_distance_km:
                    matching_products = [
                        p for p in m.products
                        if (not active_ingredient_id or p.active_ingredient_id == active_ingredient_id)
                        and p.is_legally_registered
                    ]
                    if matching_products:
                        for p in matching_products:
                            results.append(
                                NearbyMerchantResponse(
                                    merchant_id=m.id,
                                    merchant_name=m.name,
                                    contact_phone=m.contact_phone,
                                    address=m.address,
                                    distance_km=round(dist, 2),
                                    product_id=p.id,
                                    brand_name=p.brand_name,
                                    concentration_Cs=p.concentration_Cs,
                                    price=p.price,
                                    stock_quantity=p.stock_quantity,
                                    is_demo=m.is_demo,
                                )
                            )
                    elif not active_ingredient_id:
                        results.append(
                            NearbyMerchantResponse(
                                merchant_id=m.id,
                                merchant_name=m.name,
                                contact_phone=m.contact_phone,
                                address=m.address,
                                distance_km=round(dist, 2),
                                is_demo=m.is_demo,
                            )
                        )

        results.sort(key=lambda r: r.distance_km)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying nearby merchants: {exc}"
        )


@router.post(
    "/calculate-substitution",
    response_model=SubstitutionCalculationResponse,
    summary="Standalone Chemical Active Ingredient Substitution Calculation",
)
def calculate_product_substitution(
    request: SubstitutionCalculationRequest,
) -> SubstitutionCalculationResponse:
    """Calculates equivalent chemical active ingredient substitute dosage using Qs = Qr * (Cr / Cs)."""
    try:
        return SubstitutionService.calculate_standalone_substitution(request)
    except SubstitutionError as se:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(se))
    except Exception as exc:
        logger.exception("Unexpected error in substitution calculation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating product substitution: {exc}"
        )


@router.post(
    "/substitute-and-rank",
    response_model=SubstituteAndRankResponse,
    summary="Localized Dealer Discovery, Product Substitution, and Multi-Criteria Ranking",
)
def substitute_and_rank_merchants(
    request: SubstituteAndRankRequest,
    db: Session = Depends(get_db),
) -> SubstituteAndRankResponse:
    """Discovers nearby agro-dealers, verifies chemical eligibility and crop registration,

    calculates equivalent dosages Qs = Qr * (Cr / Cs), and produces multi-criteria rankings.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        weights = request.weights or RankingWeights()
        return SubstituteAndRankResponse(
            status="DATABASE_OFFLINE",
            message=f"Agro-dealer database is currently offline or unreachable: {exc}. PostgreSQL/PostGIS connection required for spatial dealer discovery.",
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
            weights_configured={
                "price": weights.price,
                "distance": weights.distance,
                "stock": weights.stock,
            },
            demonstration_advisory="Database offline. Launch PostgreSQL/PostGIS to query dealer inventories.",
        )

    try:
        return SubstitutionService.substitute_and_rank(db, request)
    except SubstitutionError as se:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(se))
    except Exception as exc:
        logger.exception("Unexpected error in merchant substitute and rank: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error discovering and ranking nearby merchants: {exc}"
        )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Get Commercial Agro-dealer Product by ID",
)
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Retrieves full commercial product specification and registration information."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    ai_name = product.active_ingredient.common_name if product.active_ingredient else None
    return ProductResponse(
        id=product.id,
        brand_name=product.brand_name,
        active_ingredient_name=ai_name,
        concentration_Cs=product.concentration_Cs,
        concentration_unit=product.concentration_unit or "%",
        formulation_type=product.formulation_type,
        package_size=product.package_size,
        price=product.price,
        currency=product.currency,
        stock_quantity=product.stock_quantity,
        registration_number=product.registration_number,
        is_legally_registered=product.is_legally_registered,
        registered_crops=product.registered_crops,
        registered_diseases=product.registered_diseases,
        application_method=product.application_method or "Foliar Spray",
        is_demo=product.is_demo,
    )


@router.get(
    "/{merchant_id}/products",
    response_model=List[ProductResponse],
    summary="Get All Products Stocked by a Specific Merchant",
)
def get_merchant_products(
    merchant_id: int,
    db: Session = Depends(get_db),
) -> List[ProductResponse]:
    """Retrieves catalog of commercial agricultural inputs stocked by a dealer."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {merchant_id} not found"
        )
    results = []
    for product in merchant.products:
        ai_name = product.active_ingredient.common_name if product.active_ingredient else None
        results.append(
            ProductResponse(
                id=product.id,
                brand_name=product.brand_name,
                active_ingredient_name=ai_name,
                concentration_Cs=product.concentration_Cs,
                concentration_unit=product.concentration_unit or "%",
                formulation_type=product.formulation_type,
                package_size=product.package_size,
                price=product.price,
                currency=product.currency,
                stock_quantity=product.stock_quantity,
                registration_number=product.registration_number,
                is_legally_registered=product.is_legally_registered,
                registered_crops=product.registered_crops,
                registered_diseases=product.registered_diseases,
                application_method=product.application_method or "Foliar Spray",
                is_demo=product.is_demo,
            )
        )
    return results


@router.get(
    "/{merchant_id}",
    response_model=MerchantResponse,
    summary="Get Merchant Profile by ID",
)
def get_merchant_by_id(
    merchant_id: int,
    db: Session = Depends(get_db),
) -> MerchantResponse:
    """Retrieves dealer contact details, geographic location, and stocked inventory."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {merchant_id} not found"
        )
    m_lat, m_lon = _extract_coordinates(merchant.location_geom)
    products_out = []
    for product in merchant.products:
        ai_name = product.active_ingredient.common_name if product.active_ingredient else None
        products_out.append(
            ProductResponse(
                id=product.id,
                brand_name=product.brand_name,
                active_ingredient_name=ai_name,
                concentration_Cs=product.concentration_Cs,
                concentration_unit=product.concentration_unit or "%",
                formulation_type=product.formulation_type,
                package_size=product.package_size,
                price=product.price,
                currency=product.currency,
                stock_quantity=product.stock_quantity,
                registration_number=product.registration_number,
                is_legally_registered=product.is_legally_registered,
                registered_crops=product.registered_crops,
                registered_diseases=product.registered_diseases,
                application_method=product.application_method or "Foliar Spray",
                is_demo=product.is_demo,
            )
        )
    return MerchantResponse(
        id=merchant.id,
        name=merchant.name,
        contact_phone=merchant.contact_phone,
        contact_email=merchant.contact_email,
        address=merchant.address,
        latitude=m_lat if m_lat is not None else 0.0,
        longitude=m_lon if m_lon is not None else 0.0,
        is_active=merchant.is_active,
        is_demo=merchant.is_demo,
        products=products_out,
    )
