"""
Compatibility shim: marketplace endpoints removed.
Clients hitting /api/marketplace/* will receive 410 Gone and be guided to `/api/templates`.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/{path:path}")
async def marketplace_removed(path: str):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Marketplace endpoints have been removed. "
            "Use /api/templates endpoints for template discovery, search, purchases, favorites and reviews."
        ),
    )
