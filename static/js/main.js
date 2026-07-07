// Main JavaScript for Xiaohongshu Analyzer

// Utility function for formatting numbers
function formatNumber(num) {
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    return num.toLocaleString();
}

// Utility function for API calls
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Refresh stats on dashboard
async function refreshStats() {
    try {
        const stats = await apiCall('/api/stats');
        // Update stats if elements exist
        // This can be extended to update specific elements
        console.log('Stats refreshed:', stats);
    } catch (error) {
        console.error('Failed to refresh stats:', error);
    }
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('已复制到剪贴板');
    }).catch(err => {
        console.error('复制失败:', err);
    });
}

// Confirm action helper
function confirmAction(message) {
    return confirm(message);
}

// Initialize page-specific features
document.addEventListener('DOMContentLoaded', function() {
    // Add any page-specific initialization here

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Auto-close alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
        if (alert.classList.contains('auto-close')) {
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000);
        }
    });

    // Form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    valid = false;
                } else {
                    field.classList.remove('error');
                }
            });

            if (!valid) {
                e.preventDefault();
                alert('请填写所有必填字段');
            }
        });
    });

    // Number input formatting
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.value = 0;
            }
        });
    });
});

// Export functions for global use
window.formatNumber = formatNumber;
window.apiCall = apiCall;
window.refreshStats = refreshStats;
window.copyToClipboard = copyToClipboard;
window.confirmAction = confirmAction;
