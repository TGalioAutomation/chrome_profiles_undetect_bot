// Main application JavaScript

// Global variables
// socket is declared in base.html
let profiles = [];
let systemStatus = {};
let autoLayoutEnabled = false;
let layoutConfig = {
    margin: 10,
    titleBarHeight: 30,
    taskbarHeight: 40
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Socket.IO connection is already initialized in base.html
    // Just set up event listeners
    setupSocketEvents();
    setupGlobalEventListeners();

    console.log('Chrome Profiles Manager initialized');
}

function setupSocketEvents() {
    // Connection events
    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus(true);
        showNotification('Connected to server', 'success');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
        showNotification('Disconnected from server', 'warning');
    });
    
    // Profile events
    socket.on('profiles_updated', function() {
        console.log('Profiles updated');
        if (typeof loadProfiles === 'function') {
            loadProfiles();
        }
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        }
    });
    
    // Browser events
    socket.on('browser_started', function(data) {
        console.log('Browser started:', data.profile);
        showNotification(`Browser started for profile: ${data.profile}`, 'success');
        refreshData();
    });
    
    socket.on('browser_stopped', function(data) {
        console.log('Browser stopped:', data.profile);
        showNotification(`Browser stopped for profile: ${data.profile}`, 'info');
        refreshData();
    });
    
    socket.on('browser_error', function(data) {
        console.error('Browser error:', data);
        showNotification(`Browser error for ${data.profile}: ${data.error}`, 'danger');
        refreshData();
    });
    
    // Status events
    socket.on('status', function(data) {
        console.log('Status update:', data);
        if (data.message) {
            showNotification(data.message, 'info');
        }
    });
}

function setupGlobalEventListeners() {
    // Global keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+R or F5 - Refresh data
        if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
            e.preventDefault();
            refreshData();
        }
        
        // Ctrl+N - New profile (if on profiles page)
        if (e.ctrlKey && e.key === 'n' && window.location.pathname.includes('profiles')) {
            e.preventDefault();
            const createModal = document.getElementById('createProfileModal');
            if (createModal) {
                new bootstrap.Modal(createModal).show();
            }
        }
    });
    
    // Handle form submissions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.classList.contains('ajax-form')) {
            e.preventDefault();
            handleAjaxForm(form);
        }
    });
}

function updateConnectionStatus(connected) {
    const statusIcon = document.getElementById('connection-status');
    const statusText = document.getElementById('connection-text');
    
    if (statusIcon && statusText) {
        if (connected) {
            statusIcon.className = 'fas fa-circle text-success';
            statusText.textContent = 'Connected';
        } else {
            statusIcon.className = 'fas fa-circle text-danger';
            statusText.textContent = 'Disconnected';
        }
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alertId = 'alert-' + Date.now();
    const alertClass = `alert-${type}`;
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert" id="${alertId}">
            <i class="fas fa-${getIconForType(type)}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertsContainer.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after specified duration
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, duration);
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle',
        'primary': 'info-circle',
        'secondary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function refreshData() {
    // Refresh data based on current page
    if (typeof loadProfiles === 'function') {
        loadProfiles();
    }
    if (typeof loadDashboardData === 'function') {
        loadDashboardData();
    }
}

// API helper functions
async function apiRequest(url, options = {}) {
    try {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        return data;
        
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

async function getProfiles() {
    return await apiRequest('/api/profiles');
}

async function createProfile(profileData) {
    return await apiRequest('/api/profiles', {
        method: 'POST',
        body: JSON.stringify(profileData)
    });
}


async function updateProfile(profileName, updateData) {
    return await apiRequest(`/api/profiles/${profileName}`, {
        method: 'PUT',
        body: JSON.stringify(updateData)
    });
}

async function deleteProfile(profileName) {
    return await apiRequest(`/api/profiles/${profileName}`, {
        method: 'DELETE'
    });
}

async function startBrowser(profileName) {
    return await apiRequest(`/api/profiles/${profileName}/start`, {
        method: 'POST'
    });
}

async function stopBrowser(profileName) {
    return await apiRequest(`/api/profiles/${profileName}/stop`, {
        method: 'POST'
    });
}

async function navigateBrowser(profileName, url) {
    return await apiRequest(`/api/profiles/${profileName}/navigate`, {
        method: 'POST',
        body: JSON.stringify({ url: url })
    });
}

async function startAllBrowsers() {
    try {
        const response = await fetch('/api/profiles');
        const data = await response.json();

        if (data.success) {
            const stoppedProfiles = data.profiles
                .filter(p => !p.is_running)
                .map(p => p.name);

            if (stoppedProfiles.length === 0) {
                showNotification('All browsers are already running', 'info');
                return;
            }

            if (autoLayoutEnabled) {
                await startMultipleBrowsersWithLayout(stoppedProfiles);
            } else {
                showNotification(`Starting ${stoppedProfiles.length} browsers...`, 'info');

                const promises = stoppedProfiles.map(async (profileName) => {
                    try {
                        await startBrowser(profileName);
                    } catch (error) {
                        console.error(`Error starting browser ${profileName}:`, error);
                    }
                });

                await Promise.all(promises);
                showNotification('All browsers started!', 'success');
            }
        }
    } catch (error) {
        console.error('Error starting all browsers:', error);
        showNotification('Error starting browsers', 'danger');
    }
}

async function stopAllBrowsers() {
    try {
        const response = await fetch('/api/profiles');
        const data = await response.json();

        if (data.success) {
            const runningProfiles = data.profiles
                .filter(p => p.is_running)
                .map(p => p.name);

            if (runningProfiles.length === 0) {
                showNotification('No browsers are running', 'info');
                return;
            }

            showNotification(`Stopping ${runningProfiles.length} browsers...`, 'info');

            const promises = runningProfiles.map(async (profileName) => {
                try {
                    await stopBrowser(profileName);
                } catch (error) {
                    console.error(`Error stopping browser ${profileName}:`, error);
                }
            });

            await Promise.all(promises);
            showNotification('All browsers stopped!', 'success');
        }
    } catch (error) {
        console.error('Error stopping all browsers:', error);
        showNotification('Error stopping browsers', 'danger');
    }
}

async function getSystemStatus() {
    return await apiRequest('/api/status');
}

async function refreshStatus() {
    try {
        showNotification('Refreshing status...', 'info');

        // Refresh system status
        const statusData = await getSystemStatus();
        if (statusData.success) {
            systemStatus = statusData.status;

            // Update dashboard if on dashboard page
            if (typeof updateDashboard === 'function') {
                updateDashboard();
            }

            // Update profiles if on profiles page
            if (typeof loadProfiles === 'function') {
                loadProfiles();
            }

            showNotification('Status refreshed successfully', 'success');
        } else {
            showNotification('Failed to refresh status', 'danger');
        }
    } catch (error) {
        console.error('Error refreshing status:', error);
        showNotification('Error refreshing status', 'danger');
    }
}

// Global loadProfiles function for profiles page
async function loadProfilesGlobal() {
    try {
        console.log('🔄 Loading profiles (global)...');
        const response = await fetch('/api/profiles');
        const data = await response.json();

        console.log('📊 API Response:', data);

        if (data.success) {
            profiles = data.profiles;
            console.log('📋 Profiles loaded:', profiles.length);

            // Update profiles table if on profiles page
            if (typeof updateProfilesTable === 'function') {
                updateProfilesTable();
            }

            // Update dashboard if on dashboard page
            if (typeof updateDashboard === 'function') {
                updateDashboard();
            }

            return data;
        } else {
            console.error('❌ API Error:', data.error);
            showNotification('Error loading profiles: ' + data.error, 'danger');
        }

    } catch (error) {
        console.error('❌ Error loading profiles:', error);
        showNotification('Error loading profiles', 'danger');
    }
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'Never';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatUserAgent(userAgent) {
    if (!userAgent) return 'Unknown';
    
    // Extract browser and version info
    const chromeMatch = userAgent.match(/Chrome\/(\d+\.\d+)/);
    const osMatch = userAgent.match(/(Windows NT \d+\.\d+|Mac OS X \d+_\d+_\d+|X11; Linux)/);
    
    let result = '';
    if (chromeMatch) {
        result += `Chrome ${chromeMatch[1]}`;
    }
    if (osMatch) {
        let os = osMatch[1];
        if (os.includes('Windows NT')) {
            os = 'Windows';
        } else if (os.includes('Mac OS X')) {
            os = 'macOS';
        } else if (os.includes('X11; Linux')) {
            os = 'Linux';
        }
        result += ` on ${os}`;
    }
    
    return result || userAgent.substring(0, 50) + '...';
}

function validateProfileData(data) {
    const errors = [];
    
    if (!data.name || data.name.trim().length === 0) {
        errors.push('Profile name is required');
    }
    
    if (!data.user_agent || data.user_agent.trim().length === 0) {
        errors.push('User agent is required');
    }
    
    if (data.proxy && !isValidProxy(data.proxy)) {
        errors.push('Invalid proxy format');
    }
    
    if (data.window_size && (!Array.isArray(data.window_size) || data.window_size.length !== 2)) {
        errors.push('Invalid window size format');
    }
    
    return errors;
}

function isValidProxy(proxy) {
    try {
        const url = new URL(proxy);
        return ['http:', 'https:', 'socks4:', 'socks5:'].includes(url.protocol);
    } catch {
        return false;
    }
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch {
        return false;
    }
}

// Loading states
function setLoading(element, loading = true) {
    if (loading) {
        element.classList.add('loading');
        element.disabled = true;
    } else {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

function showLoadingSpinner(container) {
    container.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="mt-2">Loading...</div>
        </div>
    `;
}

// Global createProfile function for UI
async function createProfileFromUI() {
    console.log('🚀 createProfileFromUI function called');

    try {
        const form = document.getElementById('createProfileForm');
        console.log('📋 Form element:', form);

        if (!form) {
            console.error('❌ Form not found');
            showNotification('Form not found', 'danger');
            return;
        }

        // Validate form first
        if (!form.checkValidity()) {
            console.log('❌ Form validation failed');
            form.reportValidity();
            return;
        }

        const userAgent = document.getElementById('userAgent').value === 'custom'
            ? document.getElementById('customUserAgent').value
            : document.getElementById('userAgent').value;

        console.log('🔍 Selected user agent:', userAgent);

        // Validate user agent
        if (!userAgent || userAgent.trim() === '') {
            console.log('❌ User agent validation failed');
            showNotification('Please select or enter a user agent', 'danger');
            return;
        }

        const customOptions = document.getElementById('customOptions').value
            .split('\n')
            .map(opt => opt.trim())
            .filter(opt => opt.length > 0);

        const profileData = {
            name: document.getElementById('profileName').value.trim(),
            display_name: document.getElementById('displayName').value.trim() || document.getElementById('profileName').value.trim(),
            user_agent: userAgent.trim(),
            proxy: document.getElementById('proxy').value.trim() || null,
            window_size: [
                parseInt(document.getElementById('windowWidth').value) || 1920,
                parseInt(document.getElementById('windowHeight').value) || 1080
            ],
            headless: document.getElementById('headless').checked,
            custom_options: customOptions,
            notes: document.getElementById('notes').value.trim(),
            // Gmail account fields
            gmail_email: document.getElementById('gmailEmail').value.trim() || null,
            gmail_password: document.getElementById('gmailPassword').value.trim() || null,
            gmail_recovery_email: document.getElementById('gmailRecoveryEmail').value.trim() || null,
            gmail_phone: document.getElementById('gmailPhone').value.trim() || null,
            gmail_2fa_secret: document.getElementById('gmail2faSecret').value.trim() || null,
            gmail_auto_login: document.getElementById('gmailAutoLogin').checked
        };

        console.log('📊 Creating profile with data:', profileData);

        // Validate required fields
        if (!profileData.name) {
            showNotification('Profile name is required', 'danger');
            return;
        }

        // Call API
        console.log('📡 Calling API with data:', profileData);

        const response = await fetch('/api/profiles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });

        console.log('📡 Response status:', response.status);

        const data = await response.json();
        console.log('📄 Response data:', data);

        if (data && data.success) {
            showNotification(data.message, 'success');

            // Close modal
            const modal = document.getElementById('createProfileModal');
            if (modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }

            // Reset form
            form.reset();

            // Reload profiles if function exists
            if (typeof loadProfiles === 'function') {
                loadProfiles();
            }
        } else {
            const errorMsg = data && data.error ? data.error : 'Unknown error occurred';
            showNotification('Error creating profile: ' + errorMsg, 'danger');
            console.error('❌ API Error:', data);
        }

    } catch (error) {
        console.error('❌ Error creating profile:', error);
        showNotification('Error creating profile: ' + error.message, 'danger');
    }
}

// Export functions for global use
window.ChromeProfilesManager = {
    apiRequest,
    getProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    startBrowser,
    stopBrowser,
    navigateBrowser,
    getSystemStatus,
    showNotification,
    formatDate,
    formatUserAgent,
    validateProfileData,
    isValidProxy,
    isValidUrl,
    setLoading,
    showLoadingSpinner
};

// Make createProfile available globally with different name to avoid conflict
window.createProfileUI = createProfileFromUI;

// Make showAlert alias for showNotification
window.showAlert = showNotification;

// Make functions available globally
window.startAllBrowsers = startAllBrowsers;
window.stopAllBrowsers = stopAllBrowsers;
window.refreshStatus = refreshStatus;
window.startBrowser = startBrowser;
window.stopBrowser = stopBrowser;
window.navigateBrowser = navigateBrowser;
window.autoArrangeRunningBrowsers = autoArrangeRunningBrowsers;
window.loadProfiles = loadProfilesGlobal;

// Auto Layout Functions
function getScreenInfo() {
    return {
        width: screen.width,
        height: screen.height,
        availWidth: screen.availWidth,
        availHeight: screen.availHeight,
        colorDepth: screen.colorDepth,
        pixelDepth: screen.pixelDepth
    };
}

function calculateOptimalLayout(numWindows) {
    const screen = getScreenInfo();
    const usableWidth = screen.availWidth - (layoutConfig.margin * 2);
    const usableHeight = screen.availHeight - layoutConfig.taskbarHeight - (layoutConfig.margin * 2);

    // Calculate optimal grid layout
    let cols = Math.ceil(Math.sqrt(numWindows));
    let rows = Math.ceil(numWindows / cols);

    // Adjust for screen aspect ratio
    const screenRatio = usableWidth / usableHeight;
    if (screenRatio > 1.5) { // Wide screen
        cols = Math.min(cols + 1, numWindows);
        rows = Math.ceil(numWindows / cols);
    }

    const windowWidth = Math.floor(usableWidth / cols) - layoutConfig.margin;
    const windowHeight = Math.floor(usableHeight / rows) - layoutConfig.margin - layoutConfig.titleBarHeight;

    const positions = [];
    for (let i = 0; i < numWindows; i++) {
        const col = i % cols;
        const row = Math.floor(i / cols);

        positions.push({
            x: layoutConfig.margin + (col * (windowWidth + layoutConfig.margin)),
            y: layoutConfig.margin + (row * (windowHeight + layoutConfig.margin + layoutConfig.titleBarHeight)),
            width: windowWidth,
            height: windowHeight
        });
    }

    return {
        positions,
        grid: { cols, rows },
        windowSize: { width: windowWidth, height: windowHeight },
        screenInfo: screen
    };
}

function applyAutoLayout(profileNames) {
    if (!profileNames || profileNames.length === 0) {
        showNotification('No profiles to arrange', 'warning');
        return;
    }

    const layout = calculateOptimalLayout(profileNames.length);

    showNotification(`Arranging ${profileNames.length} windows in ${layout.grid.cols}x${layout.grid.rows} grid`, 'info');

    // Apply layout to each profile
    profileNames.forEach((profileName, index) => {
        if (index < layout.positions.length) {
            const pos = layout.positions[index];
            applyWindowPosition(profileName, pos);
        }
    });

    return layout;
}

async function applyWindowPosition(profileName, position) {
    try {
        const response = await fetch(`/api/profiles/${profileName}/window-position`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                x: position.x,
                y: position.y,
                width: position.width,
                height: position.height
            })
        });

        const data = await response.json();
        if (!data.success) {
            console.warn(`Failed to position window for ${profileName}:`, data.error);
        }
    } catch (error) {
        console.error(`Error positioning window for ${profileName}:`, error);
    }
}

// Auto layout for running browsers
async function autoArrangeRunningBrowsers() {
    try {
        const response = await fetch('/api/profiles');
        const data = await response.json();

        if (data.success) {
            const runningProfiles = data.profiles
                .filter(p => p.is_running)
                .map(p => p.name);

            if (runningProfiles.length > 0) {
                applyAutoLayout(runningProfiles);
            } else {
                showNotification('No running browsers to arrange', 'info');
            }
        }
    } catch (error) {
        console.error('Error getting running profiles:', error);
        showNotification('Error getting running profiles', 'danger');
    }
}

// Auto layout when starting multiple browsers
async function startMultipleBrowsersWithLayout(profileNames) {
    if (!profileNames || profileNames.length === 0) return;

    showNotification(`Starting ${profileNames.length} browsers with auto layout...`, 'info');

    // Calculate layout first
    const layout = calculateOptimalLayout(profileNames.length);

    // Start browsers with calculated positions
    const promises = profileNames.map(async (profileName, index) => {
        try {
            // Start browser
            await startBrowser(profileName);

            // Wait a bit for browser to start
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Apply position
            if (index < layout.positions.length) {
                await applyWindowPosition(profileName, layout.positions[index]);
            }
        } catch (error) {
            console.error(`Error starting browser ${profileName}:`, error);
        }
    });

    await Promise.all(promises);
    showNotification('Browsers started and arranged!', 'success');
}
