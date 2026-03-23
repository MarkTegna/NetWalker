// Common functions for NetWalker Web UI

// Load and display statistics
async function loadStats() {
    try {
        const stats = await getSummaryStats();
        document.getElementById('total-devices').textContent = stats.total_devices || 0;
        document.getElementById('stack-devices').textContent = stats.stack_devices || 0;
        document.getElementById('total-connections').textContent = stats.total_connections || 0;
        document.getElementById('total-vlans').textContent = stats.total_vlans || 0;
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load and display devices
async function loadDevices(offset = 0, append = false) {
    try {
        const devices = await getDevices(50, offset);
        const tbody = document.getElementById('devices-table');
        
        if (!append) {
            tbody.innerHTML = '';
        }
        
        if (devices.length === 0) {
            if (!append) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">No devices found</td></tr>';
            }
            return;
        }
        
        devices.forEach(device => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${device.device_name || '-'}</td>
                <td>${device.platform || '-'}</td>
                <td>${device.hardware_model || '-'}</td>
                <td>${device.ip_address || '-'}</td>
                <td>${device.software_version || '-'}</td>
                <td><span class="badge bg-${device.status === 'active' ? 'success' : 'secondary'}">${device.status}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading devices:', error);
        document.getElementById('devices-table').innerHTML = 
            '<tr><td colspan="6" class="text-center text-danger">Error loading devices</td></tr>';
    }
}

// Perform device search
async function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    
    try {
        const results = await searchDevices(query);
        const resultsDiv = document.getElementById('search-results');
        
        if (results.length === 0) {
            resultsDiv.innerHTML = '<div class="alert alert-info">No devices found matching your search.</div>';
            return;
        }
        
        let html = '<div class="table-responsive"><table class="table table-sm table-striped">';
        html += '<thead><tr><th>Device Name</th><th>Platform</th><th>Model</th><th>IP Address</th><th>Serial Number</th></tr></thead><tbody>';
        
        results.forEach(device => {
            html += `
                <tr>
                    <td>${device.device_name || '-'}</td>
                    <td>${device.platform || '-'}</td>
                    <td>${device.hardware_model || '-'}</td>
                    <td>${device.ip_address || '-'}</td>
                    <td>${device.serial_number || '-'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        resultsDiv.innerHTML = html;
    } catch (error) {
        console.error('Error searching devices:', error);
        document.getElementById('search-results').innerHTML = 
            '<div class="alert alert-danger">Error performing search</div>';
    }
}

// Load platform chart
async function loadPlatformChart() {
    try {
        const data = await getPlatformStats();
        const platforms = data.platforms || [];
        
        if (platforms.length === 0) return;
        
        const ctx = document.getElementById('platform-chart');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: platforms.map(p => p.platform),
                datasets: [{
                    label: 'Device Count',
                    data: platforms.map(p => p.count),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading platform chart:', error);
    }
}
