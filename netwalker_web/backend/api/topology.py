"""
Topology API endpoints

Author: Mark Oldham
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/topology")
async def get_topology(request: Request):
    """
    Get full network topology
    
    Returns:
        All network connections
    """
    try:
        connections = request.app.state.topology_queries.get_all_connections()
        return {"connections": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topology/{device_id}")
async def get_device_topology(request: Request, device_id: int):
    """
    Get topology for a specific device
    
    Args:
        device_id: Device ID
    
    Returns:
        Device neighbors
    """
    try:
        neighbors = request.app.state.topology_queries.get_device_neighbors(device_id)
        return {"device_id": device_id, "neighbors": neighbors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
