"""
Statistics API endpoints

Author: Mark Oldham
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/stats/summary")
async def get_summary_stats(request: Request):
    """
    Get summary statistics
    
    Returns:
        Summary statistics (device count, stack count, etc.)
    """
    try:
        stats = request.app.state.stats_queries.get_summary_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/platforms")
async def get_platform_stats(request: Request):
    """
    Get device count by platform
    
    Returns:
        Platform statistics
    """
    try:
        stats = request.app.state.stats_queries.get_platform_stats()
        return {"platforms": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
