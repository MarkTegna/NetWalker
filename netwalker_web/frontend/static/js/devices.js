// Device inventory page logic

let currentOffset = 0;
let currentFilters = {};
const PAGE_SIZE = 50;

// Load devices with current filters
async function loadDevices(offset = 0, append = false) {
    try {
        const params = new URLSearchParams({
            limit: PAGE_SIZE,
            offset: offset
        });
        
        // Add filters to params
        Object.keys(currentFilters).forEach(key => {
            if (currentFilters[key]) {
                params.append(key, currentFilters[key]);
            }
        });
        
        const response = await fetch(`/api/devices?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch devices');
        
        const devices = await response.json();
        const tbody = document.getElementById('devices-table');
        
        if (!append) {
            tbody.innerHTML = '';
        }
        
        if (devices.length === 0) {
            if (!append) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center">No devices found</td></tr>';
                document.getElementById('load-more').style.display = 'none';
            } else {
                document.getElementById('load-more').style.display = 'none';
            }
            updateShowingInfo(offset);
            return;
        }
        
        devices.forEach(device => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${device.device_name || '-'}</td>
                <td>${device.platform || '-'}</td>
                <td>${device.hardware_model || '-'}</td>
                <td>${device.ip_address || '-'}</td>
                <td>${device.serial_number || '-'}</td>
                <td>${device.software_version || '-'}</td>
                <td><small>${device.capabilities || '-'}</small></td>
                <td><span class="badge bg-${device.status === 'active' ? 'success' : 'secondary'}">${device.status}</span></td>
            `;
            tbody.appendChild(row);
        });
        
        // Show/hide load more button
        if (devices.length === PAGE_SIZE) {
            document.getElementById('load-more').style.display = 'block';
        } else {
            document.getElementById('load-more').style.display = 'none';
        }
        
        updateShowingInfo(offset + devices.length);
        
    } catch (error) {
        console.error('Error loading devices:', error);
        document.getElementById('devices-table').innerHTML = 
            '<tr><td colspan="8" class="text-center text-danger">Error loading devices</td></tr>';
    }
}

// Load device count
async function loadDeviceCount() {
    try {
        const params = new URLSearchParams();
        
        // Add filters to params
        Object.keys(currentFilters).forEach(key => {
            if (currentFilters[key]) {
                params.append(key, currentFilters[key]);
            }
        });
        
        const response = await fetch(`/api/devices/count?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch count');
        
        const data = await response.json();
        document.getElementById('total-count').textContent = data.count;
        
        // Show/hide filtered indicator
        if (data.filtered) {
            document.getElementById('filtered-indicator').style.display = 'inline-block';
        } else {
            document.getElementById('filtered-indicator').style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error loading count:', error);
        document.getElementById('total-count').textContent = 'Error';
    }
}

// Update showing info
function updateShowingInfo(count) {
    document.getElementById('showing-info').textContent = `Showing ${count} devices`;
}

// Apply filters
function applyFilters(event) {
    event.preventDefault();
    
    // Get filter values
    currentFilters = {
        device_name: document.getElementById('filter-device-name').value.trim(),
        platform: document.getElementById('filter-platform').value.trim(),
        hardware_model: document.getElementById('filter-hardware-model').value.trim(),
        ip_address: document.getElementById('filter-ip-address').value.trim(),
        serial_number: document.getElementById('filter-serial-number').value.trim(),
        software_version: document.getElementById('filter-software-version').value.trim(),
        capabilities: document.getElementById('filter-capabilities').value.trim()
    };
    
    // Remove empty filters
    Object.keys(currentFilters).forEach(key => {
        if (!currentFilters[key]) {
            delete currentFilters[key];
        }
    });
    
    // Reset offset and reload
    currentOffset = 0;
    loadDevices(currentOffset);
    loadDeviceCount();
}

// Clear all filters
function clearFilters() {
    document.getElementById('filter-form').reset();
    currentFilters = {};
    currentOffset = 0;
    loadDevices(currentOffset);
    loadDeviceCount();
}

// Export to Excel
function exportToExcel() {
    const params = new URLSearchParams();
    
    // Add filters to params
    Object.keys(currentFilters).forEach(key => {
        if (currentFilters[key]) {
            params.append(key, currentFilters[key]);
        }
    });
    
    // Open export URL in new window
    const url = `/api/reports/devices?${params.toString()}`;
    window.open(url, '_blank');
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadDevices(currentOffset);
    loadDeviceCount();
    
    // Set up event listeners
    document.getElementById('filter-form').addEventListener('submit', applyFilters);
    document.getElementById('clear-filters').addEventListener('click', clearFilters);
    document.getElementById('export-button').addEventListener('click', exportToExcel);
    
    document.getElementById('load-more').addEventListener('click', function() {
        currentOffset += PAGE_SIZE;
        loadDevices(currentOffset, true);
    });
});
