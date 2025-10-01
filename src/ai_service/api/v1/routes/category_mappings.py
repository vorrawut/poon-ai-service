"""API routes for category mapping management."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ....application.services.intelligent_mapping_service import (
    IntelligentMappingService,
)
from ....domain.entities.category_mapping import (
    CategoryMapping,
    CategoryMappingId,
    MappingStatus,
    MappingType,
)
from ....domain.repositories.category_mapping_repository import (
    CategoryMappingRepository,
)
from ..schemas.category_mappings import (
    CategoryMappingCreateRequest,
    CategoryMappingResponse,
    CategoryMappingUpdateRequest,
    MappingCandidateResponse,
    MappingStatsResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


async def get_mapping_repository(request: Request) -> CategoryMappingRepository:
    """Get category mapping repository from app state."""
    return request.app.state.category_mapping_repository


async def get_mapping_service(request: Request) -> IntelligentMappingService:
    """Get intelligent mapping service from app state."""
    return request.app.state.intelligent_mapping_service


@router.get("/", response_model=list[CategoryMappingResponse])
async def list_mappings(
    language: str | None = Query(None, description="Filter by language"),
    mapping_type: MappingType | None = Query(
        None, description="Filter by mapping type"
    ),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of mappings to return"),
    offset: int = Query(0, ge=0, description="Number of mappings to skip"),
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> list[CategoryMappingResponse]:
    """List category mappings with optional filters."""
    try:
        mappings = await repository.find_all(
            language=language,
            mapping_type=mapping_type,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        return [CategoryMappingResponse.from_entity(mapping) for mapping in mappings]

    except Exception as e:
        logger.error(f"Failed to list category mappings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category mappings",
        ) from e


@router.post(
    "/", response_model=CategoryMappingResponse, status_code=status.HTTP_201_CREATED
)
async def create_mapping(
    request: CategoryMappingCreateRequest,
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> CategoryMappingResponse:
    """Create a new category mapping."""
    try:
        # Check for existing mapping with same key
        existing = await repository.find_by_key(
            request.key, request.language, request.mapping_type
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mapping already exists for key '{request.key}' in language '{request.language}'",
            )

        # Create new mapping
        mapping = CategoryMapping(
            key=request.key,
            target_category=request.target_category,
            mapping_type=request.mapping_type,
            language=request.language,
            aliases=request.aliases or [],
            patterns=request.patterns or [],
            priority=request.priority,
            confidence=request.confidence,
            source=request.source,
            status=MappingStatus.ACTIVE,
            metadata=request.metadata or {},
        )

        saved_mapping = await repository.save(mapping)
        logger.info(f"Created category mapping: {saved_mapping.key}")

        return CategoryMappingResponse.from_entity(saved_mapping)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create category mapping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category mapping",
        ) from e


@router.get("/{mapping_id}", response_model=CategoryMappingResponse)
async def get_mapping(
    mapping_id: str,
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> CategoryMappingResponse:
    """Get a specific category mapping by ID."""
    try:
        mapping_id_obj = CategoryMappingId.from_string(mapping_id)
        mapping = await repository.get_by_id(mapping_id_obj)

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category mapping with ID '{mapping_id}' not found",
            )

        return CategoryMappingResponse.from_entity(mapping)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get category mapping {mapping_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category mapping",
        ) from e


@router.put("/{mapping_id}", response_model=CategoryMappingResponse)
async def update_mapping(
    mapping_id: str,
    request: CategoryMappingUpdateRequest,
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> CategoryMappingResponse:
    """Update an existing category mapping."""
    try:
        mapping_id_obj = CategoryMappingId.from_string(mapping_id)
        existing_mapping = await repository.get_by_id(mapping_id_obj)

        if not existing_mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category mapping with ID '{mapping_id}' not found",
            )

        # Update fields if provided
        if request.target_category is not None:
            existing_mapping.target_category = request.target_category
        if request.aliases is not None:
            existing_mapping.aliases = request.aliases
        if request.patterns is not None:
            existing_mapping.patterns = request.patterns
        if request.priority is not None:
            existing_mapping.priority = request.priority
        if request.confidence is not None:
            existing_mapping.confidence = request.confidence
        if request.is_active is not None:
            existing_mapping.is_active = request.is_active
        if request.metadata is not None:
            existing_mapping.metadata = request.metadata

        # Update version and timestamp
        existing_mapping.version += 1
        from datetime import datetime

        existing_mapping.updated_at = datetime.utcnow()

        updated_mapping = await repository.save(existing_mapping)
        logger.info(f"Updated category mapping: {updated_mapping.key}")

        return CategoryMappingResponse.from_entity(updated_mapping)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update category mapping {mapping_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category mapping",
        ) from e


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    mapping_id: str,
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
):
    """Delete a category mapping."""
    try:
        mapping_id_obj = CategoryMappingId.from_string(mapping_id)
        existing_mapping = await repository.get_by_id(mapping_id_obj)

        if not existing_mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category mapping with ID '{mapping_id}' not found",
            )

        await repository.delete(mapping_id_obj)
        logger.info(f"Deleted category mapping: {mapping_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete category mapping {mapping_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category mapping",
        ) from e


@router.post("/search", response_model=list[CategoryMappingResponse])
async def search_mappings(
    key: str = Query(..., description="Search key"),
    language: str = Query("en", description="Language"),
    mapping_type: MappingType = Query(MappingType.CATEGORY, description="Mapping type"),
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> list[CategoryMappingResponse]:
    """Search for category mappings by key."""
    try:
        mappings = await repository.find_by_key(key, language, mapping_type)
        return [CategoryMappingResponse.from_entity(mapping) for mapping in mappings]

    except Exception as e:
        logger.error(f"Failed to search category mappings for key '{key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search category mappings",
        ) from e


@router.get("/candidates/", response_model=list[MappingCandidateResponse])
async def list_candidates(
    limit: int = Query(
        100, ge=1, le=1000, description="Number of candidates to return"
    ),
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> list[MappingCandidateResponse]:
    """List mapping candidates that need review."""
    try:
        candidates = await repository.find_candidates_for_review(limit=limit)
        return [
            MappingCandidateResponse.from_entity(candidate) for candidate in candidates
        ]

    except Exception as e:
        logger.error(f"Failed to list mapping candidates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mapping candidates",
        ) from e


@router.post(
    "/candidates/{candidate_id}/approve", response_model=CategoryMappingResponse
)
async def approve_candidate(
    candidate_id: str,
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> CategoryMappingResponse:
    """Approve a mapping candidate and create a mapping."""
    try:
        from ....domain.entities.category_mapping import MappingCandidateId

        candidate_id_obj = MappingCandidateId.from_string(candidate_id)
        candidate = await repository.get_candidate_by_id(candidate_id_obj)

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping candidate with ID '{candidate_id}' not found",
            )

        # Create mapping from candidate
        mapping = CategoryMapping(
            key=candidate.normalized_text,
            target_category=candidate.suggested_category,
            mapping_type=MappingType.CATEGORY,
            language=candidate.language,
            confidence=candidate.suggested_confidence,
            source=candidate.suggestion_source,
            status=MappingStatus.ACTIVE,
            metadata={"approved_from_candidate": candidate_id},
        )

        saved_mapping = await repository.save(mapping)

        # Mark candidate as approved
        await repository.approve_candidate(candidate_id_obj)

        logger.info(
            f"Approved mapping candidate {candidate_id} -> mapping {saved_mapping.id}"
        )

        return CategoryMappingResponse.from_entity(saved_mapping)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve mapping candidate {candidate_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve mapping candidate",
        ) from e


@router.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def reject_candidate(
    candidate_id: str,
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
):
    """Reject a mapping candidate."""
    try:
        from ....domain.entities.category_mapping import MappingCandidateId

        candidate_id_obj = MappingCandidateId.from_string(candidate_id)
        await repository.reject_candidate(candidate_id_obj)

        logger.info(f"Rejected mapping candidate {candidate_id}")

    except Exception as e:
        logger.error(f"Failed to reject mapping candidate {candidate_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject mapping candidate",
        ) from e


@router.get("/stats", response_model=MappingStatsResponse)
async def get_mapping_stats(
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> MappingStatsResponse:
    """Get statistics about category mappings."""
    try:
        total_mappings = await repository.count_mappings()
        active_mappings = await repository.count_mappings(is_active=True)
        english_mappings = await repository.count_mappings(language="en")
        thai_mappings = await repository.count_mappings(language="th")

        candidates = await repository.find_candidates_for_review(limit=1000)
        pending_candidates = len([c for c in candidates if c.status == "pending"])

        return MappingStatsResponse(
            total_mappings=total_mappings,
            active_mappings=active_mappings,
            inactive_mappings=total_mappings - active_mappings,
            english_mappings=english_mappings,
            thai_mappings=thai_mappings,
            pending_candidates=pending_candidates,
            languages=["en", "th"],
            mapping_types=["category", "merchant", "rule"],
        )

    except Exception as e:
        logger.error(f"Failed to get mapping stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mapping statistics",
        ) from e


@router.post("/test", response_model=dict[str, Any])
async def test_category_mapping(
    request: dict[str, str],
    mapping_service: IntelligentMappingService = Depends(get_mapping_service),
) -> dict[str, Any]:
    """Test category mapping for a given text."""
    try:
        text = request.get("text", "")
        language = request.get("language", "en")

        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Text is required"
            )

        result = await mapping_service.map_category(text, language)

        return {
            "input_text": text,
            "language": language,
            "mapped_category": result.category if result.is_successful() else None,
            "confidence": result.confidence,
            "method": result.method,
            "is_successful": result.is_successful(),
            "error": result.error_message if not result.is_successful() else None,
        }

    except Exception as e:
        logger.error(f"Failed to test mapping for text '{text}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test category mapping",
        ) from e


@router.post("/bulk-create", response_model=dict[str, Any])
async def bulk_create_mappings(
    mappings: list[CategoryMappingCreateRequest],
    repository: CategoryMappingRepository = Depends(get_mapping_repository),
) -> dict[str, Any]:
    """Bulk create category mappings."""
    try:
        created_mappings = []
        errors = []

        for mapping_request in mappings:
            try:
                # Check for existing mapping
                existing = await repository.find_by_key(
                    mapping_request.key,
                    mapping_request.language,
                    mapping_request.mapping_type,
                )
                if existing:
                    errors.append(
                        {
                            "key": mapping_request.key,
                            "error": f"Mapping already exists for key '{mapping_request.key}'",
                        }
                    )
                    continue

                # Create mapping
                mapping = CategoryMapping(
                    key=mapping_request.key,
                    target_category=mapping_request.target_category,
                    mapping_type=mapping_request.mapping_type,
                    language=mapping_request.language,
                    aliases=mapping_request.aliases or [],
                    patterns=mapping_request.patterns or [],
                    priority=mapping_request.priority,
                    confidence=mapping_request.confidence,
                    source=mapping_request.source,
                    status=MappingStatus.ACTIVE,
                    metadata=mapping_request.metadata or {},
                )

                saved_mapping = await repository.save(mapping)
                created_mappings.append(saved_mapping.key)

            except Exception as e:
                errors.append({"key": mapping_request.key, "error": str(e)})

        logger.info(
            f"Bulk created {len(created_mappings)} mappings with {len(errors)} errors"
        )

        return {
            "created_count": len(created_mappings),
            "error_count": len(errors),
            "created_mappings": created_mappings,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"Failed to bulk create mappings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create mappings",
        ) from e
