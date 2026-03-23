"""
Device API endpoints

Author: Mark Oldham
"""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


class Device(BaseModel):
    """Device model"""
    device_id: int
    device_name: str
    platform: Optional[str] = None
    hardware_model: Optional[str] = None
    serial_number: Optional[str] = None
    capabilities: Optional[str] = None
    status: str
    software_version: Optional[str] = None
    ip_address: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


@router.get("/devices", response_model=List[Device])
async def get_devices(
    request: Request,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    device_name: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    hardware_model: Optional[str] = Query(None),
    serial_number: Optional[str] = Query(None),
    capabilities: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    software_version: Optional[str] = Query(None)
):
    """
    Get all devices with pagination and filtering
    
    Args:
        limit: Maximum number of devices to return (1-1000)
        offset: Number of devices to skip
        device_name: Filter by device name (partial match)
        platform: Filter by platform (partial match)
        hardware_model: Filter by hardware model (partial match)
        serial_number: Filter by serial number (partial match)
        capabilities: Filter by capabilities (partial match)
        ip_address: Filter by IP address (partial match)
        software_version: Filter by software version (partial match)
    
    Returns:
        List of devices matching filters
    """
    try:
        # Build filters dictionary
        filters = {}
        if device_name:
            filters['device_name'] = device_name
        if platform:
            filters['platform'] = platform
        if hardware_model:
            filters['hardware_model'] = hardware_model
        if serial_number:
            filters['serial_number'] = serial_number
        if capabilities:
            filters['capabilities'] = capabilities
        if ip_address:
            filters['ip_address'] = ip_address
        if software_version:
            filters['software_version'] = software_version
        
        devices = request.app.state.device_queries.get_all_devices(
            limit=limit, 
            offset=offset,
            filters=filters if filters else None
        )
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}")
async def get_device(request: Request, device_id: int):
    """
    Get device details by ID
    
    Args:
        device_id: Device ID
    
    Returns:
        Device details
    """
    try:
        device = request.app.state.device_queries.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/search/{query}")
async def search_devices(
    request: Request,
    query: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Search devices by name, IP, or serial number
    
    Args:
        query: Search query
        limit: Maximum number of results
    
    Returns:
        List of matching devices
    """
    try:
        devices = request.app.state.device_queries.search_devices(query, limit=limit)
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/count")
async def get_device_count(
    request: Request,
    device_name: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    hardware_model: Optional[str] = Query(None),
    serial_number: Optional[str] = Query(None),
    capabilities: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    software_version: Optional[str] = Query(None)
):
    """
    Get total count of active devices with optional filters
    
    Returns:
        Device count
    """
    try:
        # Build filters dictionary
        filters = {}
        if device_name:
            filters['device_name'] = device_name
        if platform:
            filters['platform'] = platform
        if hardware_model:
            filters['hardware_model'] = hardware_model
        if serial_number:
            filters['serial_number'] = serial_number
        if capabilities:
            filters['capabilities'] = capabilities
        if ip_address:
            filters['ip_address'] = ip_address
        if software_version:
            filters['software_version'] = software_version
        
        count = request.app.state.device_queries.get_device_count(filters if filters else None)
        return {"count": count, "filtered": bool(filters)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
