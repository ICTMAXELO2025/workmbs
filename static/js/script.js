// script.js - Employee Management System JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeSystem();
    setupEventListeners();
    setupFormValidations();
    setupRealTimeUpdates();
});

// System Initialization
function initializeSystem() {
    console.log('Maxelo Management System Initialized');
    
    // Set current year in footer if exists
    const currentYearElement = document.getElementById('current-year');
    if (currentYearElement) {
        currentYearElement.textContent = new Date().getFullYear();
    }
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize file upload previews
    initializeFileUploads();
    
    // Load initial data if needed
    loadInitialData();
}

// Event Listeners Setup
function setupEventListeners() {
    // Navigation and UI interactions
    setupNavigation();
    setupModalHandlers();
    setupDropdowns();
    setupCollapsibleSections();
    
    // Form interactions
    setupFormSubmissions();
    setupInputMasks();
    setupAutoSave();
    
    // Notifications and alerts
    setupNotificationSystem();
    setupAutoDismissAlerts();
}

// Form Validations
function setupFormValidations() {
    // Password strength validation
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', validatePasswordStrength);
    });
    
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', validateEmail);
    });
    
    // Phone number validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('blur', validatePhoneNumber);
    });
    
    // File upload validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', validateFileUpload);
    });
    
    // Date validation
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', validateDateRange);
    });
}

// Real-time Updates
function setupRealTimeUpdates() {
    // Auto-refresh notifications
    setInterval(updateNotificationCount, 30000); // Every 30 seconds
    
    // Update current time
    setInterval(updateCurrentTime, 60000); // Every minute
    
    // Check for new messages
    setInterval(checkNewMessages, 120000); // Every 2 minutes
}

// Tooltip Initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Date Picker Initialization
function initializeDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // Set min date to today for future dates
        if (!input.hasAttribute('min') && input.id !== 'start_date') {
            input.min = new Date().toISOString().split('T')[0];
        }
        
        // Add date formatting
        input.addEventListener('change', function() {
            formatDateDisplay(this);
        });
    });
    
    // Initialize date range calculations
    initializeDateRangeCalculators();
}

// File Upload Initialization
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const files = e.target.files;
            if (files.length > 0) {
                showFilePreview(files[0], input);
                updateFileSizeDisplay(files[0]);
            }
        });
    });
}

// File Preview Function
function showFilePreview(file, input) {
    const previewContainer = input.parentNode.querySelector('.file-preview');
    if (!previewContainer) return;
    
    previewContainer.innerHTML = '';
    
    const fileInfo = document.createElement('div');
    fileInfo.className = 'file-info alert alert-info mt-2';
    
    const fileType = getFileType(file.name);
    const fileSize = formatFileSize(file.size);
    
    fileInfo.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-file-${fileType} me-2 fa-2x"></i>
            <div>
                <strong>${file.name}</strong><br>
                <small>Size: ${fileSize}</small>
            </div>
        </div>
    `;
    
    previewContainer.appendChild(fileInfo);
}

// Format File Size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Get File Type
function getFileType(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const fileTypes = {
        'pdf': 'pdf',
        'doc': 'word',
        'docx': 'word',
        'xls': 'excel',
        'xlsx': 'excel',
        'ppt': 'powerpoint',
        'pptx': 'powerpoint',
        'jpg': 'image',
        'jpeg': 'image',
        'png': 'image',
        'gif': 'image',
        'txt': 'text',
        'csv': 'csv'
    };
    return fileTypes[extension] || 'file';
}

// Date Range Calculations
function initializeDateRangeCalculators() {
    const startDateInputs = document.querySelectorAll('input[name="start_date"]');
    const endDateInputs = document.querySelectorAll('input[name="end_date"]');
    
    startDateInputs.forEach(startInput => {
        const endInput = startInput.closest('form').querySelector('input[name="end_date"]');
        const durationDisplay = startInput.closest('form').querySelector('#duration_display');
        
        if (startInput && endInput) {
            startInput.addEventListener('change', function() {
                endInput.min = this.value;
                calculateDuration(startInput, endInput, durationDisplay);
            });
            
            endInput.addEventListener('change', function() {
                calculateDuration(startInput, endInput, durationDisplay);
            });
        }
    });
}

// Calculate Duration Between Dates
function calculateDuration(startInput, endInput, durationDisplay) {
    if (startInput.value && endInput.value) {
        const startDate = new Date(startInput.value);
        const endDate = new Date(endInput.value);
        const diffTime = Math.abs(endDate - startDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        
        if (durationDisplay) {
            durationDisplay.textContent = `${diffDays} day${diffDays !== 1 ? 's' : ''}`;
        }
        
        // Add visual feedback for long durations
        if (diffDays > 14) {
            durationDisplay.classList.add('text-warning');
        } else {
            durationDisplay.classList.remove('text-warning');
        }
    }
}

// Password Strength Validation
function validatePasswordStrength(input) {
    const password = input.value;
    const strengthIndicator = input.parentNode.querySelector('.password-strength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    let feedback = '';
    
    // Length check
    if (password.length >= 8) strength++;
    else feedback = 'Password should be at least 8 characters long. ';
    
    // Lowercase check
    if (/[a-z]/.test(password)) strength++;
    else feedback += 'Include lowercase letters. ';
    
    // Uppercase check
    if (/[A-Z]/.test(password)) strength++;
    else feedback += 'Include uppercase letters. ';
    
    // Number check
    if (/[0-9]/.test(password)) strength++;
    else feedback += 'Include numbers. ';
    
    // Special character check
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    else feedback += 'Include special characters. ';
    
    // Update strength indicator
    const strengthClasses = ['bg-danger', 'bg-warning', 'bg-info', 'bg-success'];
    strengthIndicator.className = `password-strength strength-${strength} ${strengthClasses[strength - 1] || 'bg-danger'}`;
    strengthIndicator.style.width = `${(strength / 5) * 100}%`;
    
    // Update feedback
    const feedbackElement = input.parentNode.querySelector('.password-feedback');
    if (feedbackElement) {
        if (password.length > 0) {
            feedbackElement.textContent = feedback || 'Strong password!';
            feedbackElement.className = `password-feedback small ${strength >= 4 ? 'text-success' : 'text-warning'}`;
        } else {
            feedbackElement.textContent = '';
        }
    }
}

// Email Validation
function validateEmail(input) {
    const email = input.value;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        showFieldError(input, 'Please enter a valid email address.');
        return false;
    } else {
        clearFieldError(input);
        return true;
    }
}

// Phone Number Validation
function validatePhoneNumber(input) {
    const phone = input.value.replace(/\D/g, '');
    
    if (phone && phone.length < 10) {
        showFieldError(input, 'Please enter a valid phone number.');
        return false;
    } else {
        clearFieldError(input);
        return true;
    }
}

// File Upload Validation
function validateFileUpload(input) {
    const file = input.files[0];
    if (!file) return true;
    
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'pptx', 'ppt', 'csv'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (file.size > maxSize) {
        showFieldError(input, 'File size must be less than 10MB.');
        input.value = '';
        return false;
    }
    
    if (!allowedTypes.includes(fileExtension)) {
        showFieldError(input, 'File type not allowed. Please check allowed formats.');
        input.value = '';
        return false;
    }
    
    clearFieldError(input);
    return true;
}

// Date Range Validation
function validateDateRange(input) {
    const form = input.closest('form');
    const startDateInput = form.querySelector('input[name="start_date"]');
    const endDateInput = form.querySelector('input[name="end_date"]');
    
    if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        
        if (endDate < startDate) {
            showFieldError(endDateInput, 'End date cannot be before start date.');
            return false;
        }
        
        if (startDate < new Date()) {
            showFieldError(startDateInput, 'Start date cannot be in the past.');
            return false;
        }
        
        clearFieldError(startDateInput);
        clearFieldError(endDateInput);
    }
    
    return true;
}

// Show Field Error
function showFieldError(input, message) {
    clearFieldError(input);
    
    input.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

// Clear Field Error
function clearFieldError(input) {
    input.classList.remove('is-invalid');
    
    const existingError = input.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

// Notification System
function setupNotificationSystem() {
    // Check for new notifications
    window.checkNotifications = function() {
        fetch('/api/notifications/count')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.count);
            })
            .catch(error => console.error('Error fetching notifications:', error));
    };
    
    // Mark notification as read
    window.markNotificationAsRead = function(notificationId) {
        fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.querySelector(`[data-notification-id="${notificationId}"]`).remove();
                updateNotificationBadge(-1);
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
    };
}

// Update Notification Badge
function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Auto-dismiss Alerts
function setupAutoDismissAlerts() {
    const autoDismissAlerts = document.querySelectorAll('.alert[data-auto-dismiss]');
    autoDismissAlerts.forEach(alert => {
        const delay = parseInt(alert.getAttribute('data-auto-dismiss')) || 5000;
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, delay);
    });
}

// Form Auto-save
function setupAutoSave() {
    const autoSaveForms = document.querySelectorAll('form[data-auto-save]');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        let saveTimeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    saveFormData(form);
                }, 1000);
            });
        });
    });
}

// Save Form Data
function saveFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem(`autoSave_${form.id}`, JSON.stringify(data));
    
    // Show save indicator
    showSaveIndicator(form, 'saved');
}

// Load Saved Form Data
function loadSavedFormData(form) {
    const savedData = localStorage.getItem(`autoSave_${form.id}`);
    if (savedData) {
        const data = JSON.parse(savedData);
        
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input && input.type !== 'file') {
                input.value = data[key];
            }
        });
        
        showSaveIndicator(form, 'loaded');
    }
}

// Show Save Indicator
function showSaveIndicator(form, type) {
    let indicator = form.querySelector('.auto-save-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'auto-save-indicator small text-muted mt-2';
        form.appendChild(indicator);
    }
    
    const messages = {
        saved: 'Draft saved locally',
        loaded: 'Draft restored'
    };
    
    indicator.textContent = messages[type];
    indicator.style.opacity = '1';
    
    setTimeout(() => {
        indicator.style.opacity = '0';
    }, 2000);
}

// Search and Filter Functionality
function setupSearchAndFilter() {
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.card').querySelector('table');
            
            if (table) {
                filterTable(table, searchTerm);
            }
        });
    });
    
    // Filter buttons
    const filterButtons = document.querySelectorAll('[data-filter]');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterValue = this.getAttribute('data-filter');
            const table = this.closest('.card').querySelector('table');
            
            if (table) {
                filterTableByAttribute(table, filterValue);
            }
        });
    });
}

// Filter Table Rows
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Filter Table by Attribute
function filterTableByAttribute(table, filterValue) {
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        if (filterValue === 'all') {
            row.style.display = '';
        } else {
            const status = row.querySelector('[data-status]');
            if (status && status.getAttribute('data-status') === filterValue) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

// Bulk Actions
function setupBulkActions() {
    const selectAllCheckboxes = document.querySelectorAll('.select-all');
    selectAllCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const table = this.closest('table');
            const rowCheckboxes = table.querySelectorAll('tbody input[type="checkbox"]');
            
            rowCheckboxes.forEach(rowCheckbox => {
                rowCheckbox.checked = this.checked;
            });
            
            updateBulkActionButtons(table);
        });
    });
    
    // Individual row selection
    document.addEventListener('change', function(e) {
        if (e.target.type === 'checkbox' && e.target.closest('tbody')) {
            const table = e.target.closest('table');
            updateBulkActionButtons(table);
            updateSelectAllCheckbox(table);
        }
    });
}

// Update Bulk Action Buttons
function updateBulkActionButtons(table) {
    const selectedCount = table.querySelectorAll('tbody input[type="checkbox"]:checked').length;
    const bulkActionContainer = table.closest('.card').querySelector('.bulk-actions');
    
    if (bulkActionContainer) {
        const actionButtons = bulkActionContainer.querySelectorAll('.btn');
        
        if (selectedCount > 0) {
            bulkActionContainer.style.display = 'block';
            actionButtons.forEach(btn => {
                btn.disabled = false;
                btn.textContent = btn.textContent.replace(/\d+/, selectedCount);
            });
        } else {
            bulkActionContainer.style.display = 'none';
        }
    }
}

// Update Select All Checkbox
function updateSelectAllCheckbox(table) {
    const selectAll = table.querySelector('.select-all');
    const rowCheckboxes = table.querySelectorAll('tbody input[type="checkbox"]');
    const selectedCount = table.querySelectorAll('tbody input[type="checkbox"]:checked').length;
    
    if (selectAll) {
        selectAll.checked = selectedCount === rowCheckboxes.length;
        selectAll.indeterminate = selectedCount > 0 && selectedCount < rowCheckboxes.length;
    }
}

// Export Data Functionality
function setupDataExport() {
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.getAttribute('data-format') || 'csv';
            const table = this.closest('.card').querySelector('table');
            
            if (table) {
                exportTableData(table, format);
            }
        });
    });
}

// Export Table Data
function exportTableData(table, format) {
    const headers = [];
    const rows = [];
    
    // Get headers
    table.querySelectorAll('thead th').forEach(header => {
        headers.push(header.textContent.trim());
    });
    
    // Get rows
    table.querySelectorAll('tbody tr').forEach(row => {
        if (row.style.display !== 'none') {
            const rowData = [];
            row.querySelectorAll('td').forEach(cell => {
                rowData.push(cell.textContent.trim());
            });
            rows.push(rowData);
        }
    });
    
    let content, mimeType, filename;
    
    if (format === 'csv') {
        content = [headers, ...rows].map(row => 
            row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',')
        ).join('\n');
        mimeType = 'text/csv';
        filename = 'export.csv';
    } else if (format === 'json') {
        const jsonData = rows.map(row => {
            const obj = {};
            headers.forEach((header, index) => {
                obj[header] = row[index];
            });
            return obj;
        });
        content = JSON.stringify(jsonData, null, 2);
        mimeType = 'application/json';
        filename = 'export.json';
    }
    
    // Download file
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Real-time Clock
function updateCurrentTime() {
    const timeElements = document.querySelectorAll('.current-time');
    const now = new Date();
    
    timeElements.forEach(element => {
        element.textContent = now.toLocaleString('en-ZA', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        }).replace(',', '');
    });
}

// Load Initial Data
function loadInitialData() {
    // Load any saved form data
    const autoSaveForms = document.querySelectorAll('form[data-auto-save]');
    autoSaveForms.forEach(form => {
        loadSavedFormData(form);
    });
    
    // Initialize search and filter
    setupSearchAndFilter();
    
    // Initialize bulk actions
    setupBulkActions();
    
    // Initialize data export
    setupDataExport();
    
    // Update current time immediately
    updateCurrentTime();
}

// Utility Functions
window.utils = {
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Format date
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('en-ZA');
    },
    
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-ZA', {
            style: 'currency',
            currency: 'ZAR'
        }).format(amount);
    },
    
    // Show loading spinner
    showLoading: function(element) {
        element.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>';
    },
    
    // Hide loading spinner
    hideLoading: function(element, originalContent) {
        element.innerHTML = originalContent;
    },
    
    // Copy to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    },
    
    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
};

// Error Handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    utils.showToast('An error occurred. Please try again.', 'danger');
});

// Unhandled Promise Rejection
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    utils.showToast('An unexpected error occurred.', 'danger');
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeSystem,
        setupEventListeners,
        utils
    };
}