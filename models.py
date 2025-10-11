// static/js/script.js

// Initialize tooltips and other functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Password strength checker
    window.CMS = window.CMS || {};
    
    window.CMS.checkPasswordStrength = function(password) {
        if (!password) return { level: 'secondary', message: 'Enter a password' };
        
        let strength = 0;
        let messages = [];
        
        // Length check
        if (password.length >= 8) strength++;
        else messages.push('at least 8 characters');
        
        // Lowercase check
        if (/[a-z]/.test(password)) strength++;
        else messages.push('lowercase letters');
        
        // Uppercase check
        if (/[A-Z]/.test(password)) strength++;
        else messages.push('uppercase letters');
        
        // Numbers check
        if (/[0-9]/.test(password)) strength++;
        else messages.push('numbers');
        
        // Special characters check
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        else messages.push('special characters');
        
        const levels = [
            { level: 'danger', message: 'Very Weak' },
            { level: 'warning', message: 'Weak' },
            { level: 'info', message: 'Fair' },
            { level: 'success', message: 'Good' },
            { level: 'success', message: 'Strong' },
            { level: 'success', message: 'Very Strong' }
        ];
        
        return levels[Math.min(strength, 5)] || levels[0];
    };

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('form[novalidate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });

    // File input preview enhancement
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'No file chosen';
            const label = this.nextElementSibling || this.parentNode.querySelector('.file-name');
            if (label) {
                label.textContent = fileName;
            }
        });
    });

    // Initialize interactive components if they exist on the page
    if (document.querySelector('.todo-checkbox')) {
        initTodoInteractions();
    }
    
    if (document.querySelector('.message-item')) {
        initMessageInteractions();
    }
    
    if (document.querySelector('.document-download-btn')) {
        initDocumentManagement();
    }
});

// Interactive Functions
function initTodoInteractions() {
    const todoCheckboxes = document.querySelectorAll('.todo-checkbox');
    todoCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const todoItem = this.closest('.todo-item');
            if (this.checked) {
                todoItem.classList.add('completed');
                todoItem.style.opacity = '0.7';
            } else {
                todoItem.classList.remove('completed');
                todoItem.style.opacity = '1';
            }
        });
    });
}

function initMessageInteractions() {
    const messageItems = document.querySelectorAll('.message-item');
    messageItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't trigger if clicking on links or buttons
            if (!e.target.closest('a') && !e.target.closest('button')) {
                this.classList.toggle('expanded');
            }
        });
    });
}

function initDocumentManagement() {
    const downloadButtons = document.querySelectorAll('.document-download-btn');
    downloadButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const documentId = this.dataset.documentId;
            const filename = this.dataset.filename;
            console.log(`Downloading document ${documentId}: ${filename}`);
            // In production, trigger actual download via AJAX or form submission
        });
    });
}

function markMessageAsRead(messageId, element) {
    console.log(`Marking message ${messageId} as read`);
    // In production, make API call to mark as read
    fetch(`/api/messages/${messageId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            element.classList.remove('unread-message');
            const badge = element.querySelector('.badge.bg-warning');
            if (badge) {
                badge.remove();
            }
        }
    })
    .catch(error => {
        console.error('Error marking message as read:', error);
    });
}

// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    toast.style.cssText = `
        margin-bottom: 10px;
        animation: slideInRight 0.3s ease;
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            const bsAlert = new bootstrap.Alert(toast);
            bsAlert.close();
        }
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
    `;
    document.body.appendChild(container);
    
    // Add CSS animation if not already present
    if (!document.querySelector('#toast-animations')) {
        const style = document.createElement('style');
        style.id = 'toast-animations';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    return container;
}

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateString;
    }
}

function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 Bytes';
    try {
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    } catch (error) {
        console.error('Error formatting file size:', error);
        return 'Unknown size';
    }
}

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Safe query selector with error handling
function safeQuerySelector(selector) {
    try {
        return document.querySelector(selector);
    } catch (error) {
        console.error('Invalid selector:', selector, error);
        return null;
    }
}

// Safe query selector all with error handling
function safeQuerySelectorAll(selector) {
    try {
        return document.querySelectorAll(selector);
    } catch (error) {
        console.error('Invalid selector:', selector, error);
        return [];
    }
}