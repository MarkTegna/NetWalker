"""
Stack member API endpoints

Author: Mark Oldham
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/stacks")
async def get_stacks(request: Request):
    """
    Get all stack devices
    
    Returns:
        List of devices with stack members
    """
    try:
        stacks = request.app.state.stack_queries.get_all_stacks()
        return {"stacks": stacks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stacks/{device_id}/members")
async def get_stack_members(request: Request, device_id: int):
    """
    Get stack members for a specific device
    
    Args:
        device_id: Device ID
    
    Returns:
        Stack member details
    """
    try:
        members = request.app.state.stack_queries.get_stack_members(device_id)
        return {"device_id": device_id, "members": members}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
