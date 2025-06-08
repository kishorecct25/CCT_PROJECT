// Main JavaScript file for CCT Web Application

// Authentication functions
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register') && window.location.pathname !== '/') {
        window.location.href = '/login';
        return false;
    }
    return true;
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// API request helper
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        }
    };
    
    const requestOptions = { ...defaultOptions, ...options };
    
    if (options.body && typeof options.body === 'object') {
        requestOptions.body = JSON.stringify(options.body);
    }
    
    try {
        const response = await fetch(endpoint, requestOptions);
        
        if (response.status === 401) {
            // Unauthorized, redirect to login
            logout();
            return null;
        }
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        return null;
    }
}

// User data functions
async function loadUserData() {
    const userData = await apiRequest('/api/v1/users/me');
    if (userData) {
        // Update UI with user data
        const usernameElements = document.querySelectorAll('.username-display');
        usernameElements.forEach(el => {
            el.textContent = userData.username;
        });
        
        return userData;
    }
    return null;
}

// Device functions
async function loadUserDevices() {
    const devices = await apiRequest('/api/v1/users/me/devices');
    return devices || [];
}

async function addUserDevice(deviceId) {
    return await apiRequest(`/api/v1/users/me/devices/${deviceId}`, {
        method: 'POST'
    });
}

async function getDeviceProbes(deviceId) {
    return await apiRequest(`/api/v1/devices/${deviceId}/probes`);
}

async function getDeviceTemperatureHistory(deviceId, probeId = null, limit = 100) {
    let url = `/api/v1/temperature/${deviceId}/history?limit=${limit}`;
    if (probeId) {
        url += `&probe_id=${probeId}`;
    }
    return await apiRequest(url);
}

// Notification functions
async function loadUserNotifications(unreadOnly = false, limit = 100) {
    return await apiRequest(`/api/v1/notifications?unread_only=${unreadOnly}&limit=${limit}`);
}

async function markNotificationAsRead(notificationId) {
    return await apiRequest(`/api/v1/notifications/${notificationId}/read`, {
        method: 'PUT'
    });
}

async function markAllNotificationsAsRead() {
    return await apiRequest('/api/v1/notifications/read-all', {
        method: 'PUT'
    });
}

// Settings functions
async function loadNotificationSettings() {
    return await apiRequest('/api/v1/users/me/notification-settings');
}

async function updateNotificationSettings(settings) {
    return await apiRequest('/api/v1/users/me/notification-settings', {
        method: 'PUT',
        body: settings
    });
}

async function loadCustomTriggers() {
    return await apiRequest('/api/v1/users/me/triggers');
}

async function createCustomTrigger(triggerData) {
    return await apiRequest('/api/v1/users/me/triggers', {
        method: 'POST',
        body: triggerData
    });
}

async function updateCustomTrigger(triggerId, triggerData) {
    return await apiRequest(`/api/v1/users/me/triggers/${triggerId}`, {
        method: 'PUT',
        body: triggerData
    });
}

// Temperature functions
async function setTargetTemperature(deviceId, temperature, userId = null) {
    const data = {
        device_id: deviceId,
        temperature: temperature
    };
    
    if (userId) {
        data.set_by_user_id = userId;
    }
    
    return await apiRequest('/api/v1/temperature/target', {
        method: 'POST',
        body: data
    });
}

async function getTargetTemperature(deviceId) {
    return await apiRequest(`/api/v1/temperature/${deviceId}/target`);
}

// Chart helpers
function createTemperatureChart(canvasId, labels, data, label = 'Temperature (°F)') {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Temperature (°F)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });
}

// Utility functions
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return 'Never';
    return new Date(dateTimeString).toLocaleString();
}

function formatTemperature(temp, unit = 'C') {
    if (temp === null || temp === undefined) return 'N/A';
    return `${temp.toFixed(1)}°${unit}`;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    if (!checkAuth()) return;
    
    // Set up logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Load user data if authenticated
    if (localStorage.getItem('token')) {
        loadUserData();
    }
    
    // Initialize page-specific functionality
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('/dashboard')) {
        initDashboard();
    } else if (currentPath.includes('/devices')) {
        initDevicesPage();
    } else if (currentPath.includes('/device/')) {
        const deviceId = currentPath.split('/').pop();
        initDeviceDetailPage(deviceId);
    } else if (currentPath.includes('/notifications')) {
        initNotificationsPage();
    } else if (currentPath.includes('/profile')) {
        initProfilePage();
    } else if (currentPath.includes('/settings')) {
        initSettingsPage();
    }
});

// Page-specific initializations
function initDashboard() {
    console.log('Initializing dashboard...');
    // Load devices
    loadUserDevices().then(devices => {
        document.getElementById('deviceCount').textContent = devices.length;
        updateActiveDevicesList(devices);
        
        // Count probes and load temperature data
        let probeCount = 0;
        let probePromises = [];
        
        devices.forEach(device => {
            const promise = getDeviceProbes(device.device_id)
                .then(probes => {
                    if (probes) {
                        probeCount += probes.length;
                    }
                    return probes;
                });
            
            probePromises.push(promise);
        });
        
        Promise.all(probePromises).then(() => {
            document.getElementById('probeCount').textContent = probeCount;
            
            // Initialize temperature chart with data from first device if available
            if (devices.length > 0) {
                getDeviceTemperatureHistory(devices[0].device_id, null, 24)
                    .then(readings => {
                        if (readings && readings.length > 0) {
                            const labels = readings.map(r => {
                                const date = new Date(r.timestamp);
                                return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
                            }).reverse();
                            
                            const data = readings.map(r => r.temperature).reverse();
                            
                            createTemperatureChart('temperatureChart', labels, data);
                            document.getElementById('noDataMessage').classList.add('d-none');
                        } else {
                            document.getElementById('noDataMessage').classList.remove('d-none');
                        }
                    });
            } else {
                document.getElementById('noDataMessage').classList.remove('d-none');
            }
        });
    });
    
    // Load notifications
    loadUserNotifications(false, 5).then(notifications => {
        if (notifications) {
            const unreadCount = notifications.filter(n => !n.is_read).length;
            document.getElementById('notificationCount').textContent = unreadCount;
            document.getElementById('alertCount').textContent = unreadCount;
            updateRecentNotificationsList(notifications);
        }
    });
    
    // Set up event listeners
    document.getElementById('refreshData').addEventListener('click', () => {
        initDashboard();
    });
    
    document.getElementById('addDeviceBtn').addEventListener('click', () => {
        const modal = new bootstrap.Modal(document.getElementById('addDeviceModal'));
        modal.show();
    });
    
    document.getElementById('addDeviceSubmit').addEventListener('click', () => {
        const deviceId = document.getElementById('deviceId').value;
        if (deviceId) {
            addUserDevice(deviceId).then(result => {
                if (result) {
                    bootstrap.Modal.getInstance(document.getElementById('addDeviceModal')).hide();
                    document.getElementById('deviceId').value = '';
                    initDashboard();
                }
            });
        }
    });
}

function initDevicesPage() {
    console.log('Initializing devices page...');
    // Implementation similar to dashboard but focused on devices
}

function initDeviceDetailPage(deviceId) {
    console.log(`Initializing device detail page for ${deviceId}...`);
    // Implementation for single device view
}

function initNotificationsPage() {
    console.log('Initializing notifications page...');
    // Implementation for notifications page
}

function initProfilePage() {
    console.log('Initializing profile page...');
    // Implementation for user profile page
}

function initSettingsPage() {
    console.log('Initializing settings page...');
    // Implementation for settings page
}

// UI update functions
function updateActiveDevicesList(devices) {
    const listElement = document.getElementById('activeDevicesList');
    if (!listElement) return;
    
    const noDevicesMessage = document.getElementById('noDevicesMessage');
    
    if (devices.length === 0) {
        if (noDevicesMessage) noDevicesMessage.classList.remove('d-none');
        return;
    }
    
    if (noDevicesMessage) noDevicesMessage.classList.add('d-none');
    listElement.innerHTML = '';
    
    devices.forEach(device => {
        const isActive = device.is_active;
        const lastConnected = formatDateTime(device.last_connected);
        
        const deviceElement = document.createElement('a');
        deviceElement.href = `/device/${device.device_id}`;
        deviceElement.className = 'list-group-item list-group-item-action';
        deviceElement.innerHTML = `
            <div class="d-flex w-100 justify-content-between align-items-center">
                <h6 class="mb-1">${device.name || device.device_id}</h6>
                <span class="badge ${isActive ? 'bg-success' : 'bg-secondary'} rounded-pill">
                    ${isActive ? 'Active' : 'Inactive'}
                </span>
            </div>
            <p class="mb-1 text-muted small">Model: ${device.model}</p>
            <small class="text-muted">Last connected: ${lastConnected}</small>
        `;
        
        listElement.appendChild(deviceElement);
    });
}

function updateRecentNotificationsList(notifications) {
    const listElement = document.getElementById('recentNotificationsList');
    if (!listElement) return;
    
    const noNotificationsMessage = document.getElementById('noNotificationsMessage');
    
    if (notifications.length === 0) {
        if (noNotificationsMessage) noNotificationsMessage.classList.remove('d-none');
        return;
    }
    
    if (noNotificationsMessage) noNotificationsMessage.classList.add('d-none');
    listElement.innerHTML = '';
    
    notifications.forEach(notification => {
        const notificationElement = document.createElement('div');
        notificationElement.className = 'list-group-item';
        
        let typeClass = 'text-info';
        if (notification.notification_type === 'temperature_alert') {
            typeClass = 'text-warning';
        } else if (notification.notification_type === 'connection_lost') {
            typeClass = 'text-danger';
        }
        
        const createdAt = formatDateTime(notification.created_at);
        
        notificationElement.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1 ${typeClass}">${notification.title}</h6>
                <small class="text-muted">${createdAt}</small>
            </div>
            <p class="mb-1">${notification.message}</p>
            <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">Via ${notification.channel}</small>
                ${notification.is_read ? '' : '<span class="badge bg-primary rounded-pill">New</span>'}
            </div>
        `;
        
        listElement.appendChild(notificationElement);
    });
}
