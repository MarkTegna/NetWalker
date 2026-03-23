// API client for NetWalker Web UI

const API_BASE = '/api';

// Get all devices
async function getDevices(limit = 50, offset = 0) {
    const response = await fetch(`${API_BASE}/devices?limit=${limit}&offset=${offset}`);
    if (!response.ok) throw new Error('Failed to fetch devices');
    return await response.json();
}

// Search devices
async function searchDevices(query) {
    const response = await fetch(`${API_BASE}/devices/search/${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search devices');
    return await response.json();
}

// Get summary statistics
async function getSummaryStats() {
    const response = await fetch(`${API_BASE}/stats/summary`);
    if (!response.ok) throw new Error('Failed to fetch statistics');
    return await response.json();
}

// Get platform statistics
async function getPlatformStats() {
    const response = await fetch(`${API_BASE}/stats/platforms`);
    if (!response.ok) throw new Error('Failed to fetch platform statistics');
    return await response.json();
}

// Get device topology
async function getDeviceTopology(deviceId) {
    const response = await fetch(`${API_BASE}/topology/${deviceId}`);
    if (!response.ok) throw new Error('Failed to fetch topology');
    return await response.json();
}

// Get stack members
async function getStackMembers(deviceId) {
    const response = await fetch(`${API_BASE}/stacks/${deviceId}/members`);
    if (!response.ok) throw new Error('Failed to fetch stack members');
    return await response.json();
}
