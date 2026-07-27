// DEVS - Digital Evidence Verification System
// Main JavaScript File

// Global Variables
let currentUser = null;
let systemStats = {
    total: 0,
    verified: 0,
    modified: 0,
    invalid: 0
};

// Initialize System
document.addEventListener('DOMContentLoaded', function() {
    initializeSystem();
    
    // Handle browser back/forward navigation
    window.addEventListener('popstate', function(event) {
        handlePopState(event);
    });
    
    // Initialize history state
    if (window.history.state === null) {
        window.history.replaceState({ page: window.location.pathname }, '', window.location.href);
    }
});

// Handle browser back/forward navigation
function handlePopState(event) {
    const user = sessionStorage.getItem('devs-user');
    const currentPath = window.location.pathname;
    
    // If user is logged in and trying to go back to login, prevent it
    if (user && (currentPath.endsWith('index.html') || currentPath.endsWith('/'))) {
        event.preventDefault();
        window.history.pushState({ page: 'dashboard' }, '', 'dashboard.html');
        return false;
    }
    
    // If user is not logged in and trying to access protected pages, redirect to login
    if (!user && !currentPath.endsWith('index.html') && !currentPath.endsWith('forgot.html')) {
        event.preventDefault();
        window.history.pushState({ page: 'login' }, '', 'index.html');
        return false;
    }
}

function initializeSystem() {
    // Load user session
    loadUserSession();
    
    // Load system statistics
    loadSystemStats();
    
    // Set up global event listeners
    setupGlobalListeners();
    
    // Initialize tooltips and other UI elements
    initializeUI();
}

// Authentication Functions
function checkAuth() {
    const user = sessionStorage.getItem('devs-user');
    if (!user && !window.location.pathname.endsWith('index.html') && !window.location.pathname.endsWith('forgot.html')) {
        // Store the attempted URL for redirect after login
        sessionStorage.setItem('devs-redirect', window.location.href);
        window.location.href = 'index.html';
        return false;
    }
    
    // If user is logged in and tries to access login page, redirect to dashboard
    if (user && (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/'))) {
        window.location.href = 'dashboard.html';
        return false;
    }
    
    return true;
}

function loadUserSession() {
    currentUser = sessionStorage.getItem('devs-user');
    if (currentUser) {
        updateUserDisplay();
    }
}

function updateUserDisplay() {
    const userElements = document.querySelectorAll('#user-display, #welcome-user');
    userElements.forEach(element => {
        if (element) {
            element.textContent = currentUser.split('@')[0] || currentUser;
        }
    });
}

// Password Toggle Functions
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const passwordIcon = document.getElementById('password-icon');
    
    if (passwordInput && passwordIcon) {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            passwordIcon.textContent = '🙈';
        } else {
            passwordInput.type = 'password';
            passwordIcon.textContent = '👁️';
        }
    }
}

// Alert System
function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fade-in`;
    alertDiv.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 1.2rem;">×</button>
        </div>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 5000);
}

// System Statistics
function loadSystemStats() {
    const stats = JSON.parse(localStorage.getItem('devs-stats') || '{}');
    systemStats = {
        total: stats.total || 0,
        verified: stats.verified || 0,
        modified: stats.modified || 0,
        invalid: stats.invalid || 0
    };
}

function updateSystemStats(newStats) {
    systemStats = { ...systemStats, ...newStats };
    localStorage.setItem('devs-stats', JSON.stringify(systemStats));
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function generateHash() {
    const chars = '0123456789abcdef';
    let hash = '';
    for (let i = 0; i < 64; i++) {
        hash += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return hash;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// File Handling
function validateFile(file) {
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/png',
        'video/mp4',
        'video/avi',
        'application/zip'
    ];
    
    if (file.size > maxSize) {
        showAlert('danger', 'File size exceeds 100MB limit');
        return false;
    }
    
    if (!allowedTypes.includes(file.type) && !file.type.startsWith('image/')) {
        showAlert('danger', 'File type not supported');
        return false;
    }
    
    return true;
}

// Navigation Functions
function navigateTo(page) {
    window.location.href = page;
}

function logout() {
    sessionStorage.removeItem('devs-user');
    localStorage.removeItem('devs-remember');
    window.location.href = 'index.html';
}

// UI Initialization
function initializeUI() {
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Global Event Listeners
function setupGlobalListeners() {
    // Handle keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search (if search exists)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="text"], input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('[id$="modal"]');
            modals.forEach(modal => {
                if (!modal.classList.contains('hidden')) {
                    modal.classList.add('hidden');
                }
            });
        }
    });
    
    // Handle online/offline status
    window.addEventListener('online', function() {
        showAlert('success', 'Connection restored');
    });
    
    window.addEventListener('offline', function() {
        showAlert('warning', 'Connection lost. Some features may be unavailable.');
    });
    
    // Handle page visibility change
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            // Refresh data when page becomes visible again
            loadSystemStats();
            if (typeof loadResults === 'function') {
                loadResults();
            }
        }
    });
}

// Data Management
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        console.log(`Saved ${key}:`, data); // Debug log
        return true;
    } catch (e) {
        console.error('Error saving to localStorage:', e);
        showAlert('danger', 'Error saving data. Storage may be full.');
        return false;
    }
}

function loadFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        const parsed = data ? JSON.parse(data) : null;
        console.log(`Loaded ${key}:`, parsed); // Debug log
        return parsed;
    } catch (e) {
        console.error('Error loading from localStorage:', e);
        return null;
    }
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
        localStorage.clear();
        sessionStorage.clear();
        showAlert('success', 'All data cleared successfully');
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1500);
    }
}

// Backup and restore functions for debugging
function backupData() {
    const backup = {};
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        backup[key] = localStorage.getItem(key);
    }
    console.log('Data backup:', backup);
    return backup;
}

function restoreData(backup) {
    localStorage.clear();
    for (const key in backup) {
        localStorage.setItem(key, backup[key]);
    }
    console.log('Data restored from backup');
}

// Auto-backup before page unload (for debugging)
window.addEventListener('beforeunload', function() {
    console.log('Page unloading - localStorage should persist');
});

// Security Functions
function sanitizeInput(input) {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return passwordRegex.test(password);
}

// Export Functions
function exportToCSV(data, filename) {
    if (!data || data.length === 0) {
        showAlert('warning', 'No data to export');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    downloadFile(filename, csvContent);
    showAlert('success', 'Data exported successfully');
}

function exportToJSON(data, filename) {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(filename, jsonContent);
    showAlert('success', 'Data exported successfully');
}

// Print Functions
function printReport(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        showAlert('danger', 'Report not found');
        return;
    }
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>DEVS Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .no-print { display: none; }
                @media print { .no-print { display: none; } }
            </style>
        </head>
        <body>
            ${element.innerHTML}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Theme Functions (for future enhancement)
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('devs-theme', theme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem('devs-theme') || 'light';
    setTheme(savedTheme);
}

// Performance Monitoring
function logPerformance(action, startTime) {
    const endTime = performance.now();
    const duration = endTime - startTime;
    console.log(`${action} completed in ${duration.toFixed(2)}ms`);
    
    // Could send this to analytics in a real application
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showAlert('danger', 'An unexpected error occurred. Please refresh the page.');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showAlert('danger', 'A system error occurred. Please try again.');
});

// Development Helper Functions (remove in production)
function devLog(message) {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('[DEVS Dev]', message);
    }
}

function showDebugInfo() {
    const debugInfo = {
        currentUser: currentUser,
        systemStats: systemStats,
        localStorage: Object.keys(localStorage),
        sessionStorage: Object.keys(sessionStorage),
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
    };
    
    console.table(debugInfo);
    return debugInfo;
}

// Make functions globally available
window.DEVS = {
    showAlert,
    formatFileSize,
    generateHash,
    downloadFile,
    logout,
    clearAllData,
    exportToCSV,
    exportToJSON,
    printReport,
    showDebugInfo
};
