// Main JavaScript functionality for Company Management System
document.addEventListener('DOMContentLoaded', function() {
    // Flash message auto-hide
    initFlashMessages();
    
    // Form validation
    initFormValidation();
    
    // Todo item interactions
    initTodoInteractions();
    
    // Message read status
    initMessageInteractions();
    
    // Delete confirmation
    initDeleteConfirmations();
    
    // Dynamic date formatting
    initDateFormatting();
    
    // Search functionality
    initSearchFunctionality();
    
    // Password strength checker
    initPasswordStrength();
    
    // Auto-update current year in footer
    updateCurrentYear();
});

// Flash message auto-hide
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        // Add close button if not present
        if (!message.querySelector('.btn-close')) {
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            closeButton.setAttribute('aria-label', 'Close');
            message.appendChild(closeButton);
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.style.opacity = '0';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 300);
            }
        }, 5000);
    });
}

// Form validation
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.classList.add('is-invalid');
                    
                    // Add error message if not exists
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        errorDiv.textContent = 'This field is required.';
                        field.parentNode.appendChild(errorDiv);
                    }
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });

            if (!valid) {
                e.preventDefault();
                showToast('Please fill in all required fields.', 'error');
            }
        });
    });
}

// Todo item interactions
function initTodoInteractions() {
    document.querySelectorAll('.todo-item').forEach(item => {
        const checkbox = item.querySelector('.todo-checkbox');
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                const form = this.closest('form');
                if (form) {
                    // Show loading state
                    const originalText = this.nextElementSibling?.textContent;
                    if (this.nextElementSibling) {
                        this.nextElementSibling.textContent = 'Updating...';
                    }
                    
                    form.submit();
                }
            });
        }
    });
}

// Message read status
function initMessageInteractions() {
    document.querySelectorAll('.message-item.unread').forEach(item => {
        item.addEventListener('click', function() {
            const messageId = this.dataset.messageId;
            if (messageId) {
                markMessageAsRead(messageId, this);
            }
        });
    });
}

// Delete confirmation
function initDeleteConfirmations() {
    document.querySelectorAll('.btn-delete, a[href*="delete"]').forEach(btn => {
        if (btn.href && btn.href.includes('delete')) {
            btn.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        }
    });
}

// Dynamic date formatting
function initDateFormatting() {
    document.querySelectorAll('.date-field').forEach(field => {
        const date = new Date(field.textContent);
        if (!isNaN(date)) {
            field.textContent = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
    });
}

// Search functionality
function initSearchFunctionality() {
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            const searchTerm = this.value.toLowerCase();
            const container = this.closest('.search-container');
            const items = container ? container.querySelectorAll('.search-item') : [];
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }, 300));
    });
}

// Password strength checker
function initPasswordStrength() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            const strength = checkPasswordStrength(this.value);
            let feedback = this.nextElementSibling;
            
            if (!feedback || !feedback.classList.contains('password-feedback')) {
                feedback = document.createElement('div');
                feedback.className = 'password-feedback mt-1 small';
                this.parentNode.appendChild(feedback);
            }
            
            feedback.textContent = strength.message;
            feedback.className = `password-feedback mt-1 small text-${strength.level}`;
        }, 500));
    });
}

// Utility Functions

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} toast-message`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        opacity: 0;
        transition: opacity 0.3s;
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.style.opacity = '1', 100);
    
    // Animate out and remove
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, 5000);
}

function checkPasswordStrength(password) {
    let strength = 0;
    let message = '';
    let level = 'danger';
    
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]+/)) strength++;
    if (password.match(/[A-Z]+/)) strength++;
    if (password.match(/[0-9]+/)) strength++;
    if (password.match(/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/)) strength++;
    
    switch (strength) {
        case 0:
        case 1:
        case 2:
            message = 'Weak password';
            level = 'danger';
            break;
        case 3:
        case 4:
            message = 'Medium strength password';
            level = 'warning';
            break;
        case 5:
            message = 'Strong password';
            level = 'success';
            break;
    }
    
    return { message, level };
}

function markMessageAsRead(messageId, element) {
    fetch(`/messages/${messageId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            element.classList.remove('unread');
            element.classList.remove('bg-light');
            showToast('Message marked as read', 'success');
            
            // Update unread count if exists
            const unreadBadge = document.querySelector('.unread-count');
            if (unreadBadge) {
                const currentCount = parseInt(unreadBadge.textContent) || 0;
                if (currentCount > 0) {
                    unreadBadge.textContent = currentCount - 1;
                    if (currentCount - 1 === 0) {
                        unreadBadge.style.display = 'none';
                    }
                }
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error marking message as read', 'error');
    });
}

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

function updateCurrentYear() {
    const yearElements = document.querySelectorAll('.current-year');
    const currentYear = new Date().getFullYear();
    yearElements.forEach(element => {
        element.textContent = currentYear;
    });
}

// Dashboard specific functionality
function initDashboardCharts() {
    const ctx = document.getElementById('dashboardChart');
    if (ctx) {
        // Initialize charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Leave Requests',
                        data: [12, 19, 3, 5, 2, 3],
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
}

// File upload preview
function initFileUploadPreview() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const preview = this.nextElementSibling;
                if (preview && preview.classList.contains('file-preview')) {
                    preview.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
                }
            }
        });
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Auto-save functionality for forms
function initAutoSave() {
    const autoSaveForms = document.querySelectorAll('form[data-autosave]');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        const saveKey = form.dataset.autosave;
        
        // Load saved data
        const savedData = localStorage.getItem(saveKey);
        if (savedData) {
            const data = JSON.parse(savedData);
            inputs.forEach(input => {
                if (data[input.name]) {
                    input.value = data[input.name];
                }
            });
        }
        
        // Save on input
        inputs.forEach(input => {
            input.addEventListener('input', debounce(function() {
                const formData = {};
                inputs.forEach(i => {
                    if (i.name) {
                        formData[i.name] = i.value;
                    }
                });
                localStorage.setItem(saveKey, JSON.stringify(formData));
                showToast('Changes saved locally', 'info');
            }, 1000));
        });
        
        // Clear on submit
        form.addEventListener('submit', function() {
            localStorage.removeItem(saveKey);
        });
    });
}

// Export functions for global use
window.CMS = {
    showToast,
    checkPasswordStrength,
    markMessageAsRead,
    initDashboardCharts,
    formatFileSize,
    debounce
};

// Initialize everything when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Re-initialize in case script is loaded after DOM is ready
        setTimeout(() => {
            if (typeof initFlashMessages === 'function') initFlashMessages();
            if (typeof initFormValidation === 'function') initFormValidation();
        }, 100);
    });
}