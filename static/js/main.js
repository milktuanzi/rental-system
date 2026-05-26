// ============================================
// 智能房屋租赁系统 - 优化版JavaScript
// 性能优化版本 v2.0
// ============================================

// 全局配置
const CONFIG = {
    debounceDelay: 300,
    toastDuration: 3000,
    animationDuration: 300,
    lazyLoadThreshold: 0.1
};

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 应用初始化
function initializeApp() {
    // 初始化组件（按优先级排序）
    initImageLazyLoad();           // 图片懒加载 - 最先初始化，提升性能
    initNavbarScrollEffect();      // 导航栏滚动效果
    initAnimations();              // 动画效果
    initFormValidation();          // 表单验证
    initCardHoverEffects();        // 卡片悬停效果
    initSmoothScroll();            // 平滑滚动
    initSearchEnhancements();      // 搜索增强
    initTooltips();                // 工具提示
}

// ============================================
// 图片懒加载 - 提升页面加载速度
// ============================================
function initImageLazyLoad() {
    // 使用原生懒加载（现代浏览器）
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    loadImage(img);
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: CONFIG.lazyLoadThreshold
        });

        images.forEach(img => {
            img.classList.add('lazy-loading');
            imageObserver.observe(img);
        });
    } else {
        // 降级处理：直接加载所有图片
        images.forEach(img => loadImage(img));
    }
}

function loadImage(img) {
    img.src = img.dataset.src;
    img.removeAttribute('data-src');
    img.classList.remove('lazy-loading');
    img.classList.add('lazy-loaded');
    
    img.addEventListener('load', function() {
        img.classList.add('loaded');
    });
}

// ============================================
// 导航栏滚动效果
// ============================================
function initNavbarScrollEffect() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    let ticking = false;
    let lastScrollY = 0;

    function updateNavbar() {
        const scrollY = window.scrollY;
        
        // 防止重复切换
        if (Math.abs(scrollY - lastScrollY) < 5) {
            ticking = false;
            return;
        }
        
        if (scrollY > 50) {
            if (!navbar.classList.contains('scrolled')) {
                navbar.classList.add('scrolled');
            }
        } else {
            if (navbar.classList.contains('scrolled')) {
                navbar.classList.remove('scrolled');
            }
        }
        
        lastScrollY = scrollY;
        ticking = false;
    }

    // 使用passive模式提升滚动性能
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateNavbar);
            ticking = true;
        }
    }, { passive: true });
    
    // 初始化状态
    updateNavbar();
}

// ============================================
// 入场动画初始化
// ============================================
function initAnimations() {
    const animatedElements = document.querySelectorAll('.card, .property-card, .fade-in-on-scroll, .animate-on-scroll');
    
    if (!animatedElements.length) return;

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    const delay = entry.target.dataset.delay || index * 50;
                    setTimeout(() => {
                        entry.target.classList.add('animate-in');
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, delay);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '0px',
            threshold: CONFIG.lazyLoadThreshold
        });

        animatedElements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = `opacity 0.6s ease, transform 0.6s ease`;
            el.dataset.delay = index * 50;
            observer.observe(el);
        });
    } else {
        // 降级处理：直接显示所有元素
        animatedElements.forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        });
    }
}

// ============================================
// 卡片悬停效果增强
// ============================================
function initCardHoverEffects() {
    const cards = document.querySelectorAll('.property-card');
    
    cards.forEach(card => {
        let hoverTimeout;
        
        card.addEventListener('mouseenter', function() {
            clearTimeout(hoverTimeout);
            this.classList.add('hovered');
        });
        
        card.addEventListener('mouseleave', function() {
            hoverTimeout = setTimeout(() => {
                this.classList.remove('hovered');
            }, 150);
        });
    });
}

// ============================================
// 搜索增强功能
// ============================================
function initSearchEnhancements() {
    const searchInputs = document.querySelectorAll('.search-box input, .search-box select');
    
    searchInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.closest('.search-box')?.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.closest('.search-box')?.classList.remove('focused');
        });
    });
}

// ============================================
// 表单验证增强
// ============================================
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // 实时验证反馈
    const inputs = document.querySelectorAll('.form-control, .form-select');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', debounce(function() {
            if (input.classList.contains('was-validated')) {
                validateField(input);
            }
        }, CONFIG.debounceDelay));
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
}

// ============================================
// 平滑滚动
// ============================================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ============================================
// 工具提示初始化
// ============================================
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ============================================
// Toast 通知系统
// ============================================
const Toast = {
    container: null,
    
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'true');
            this.container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 400px;
            `;
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'info', duration = CONFIG.toastDuration) {
        this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        
        const colors = {
            success: { bg: '#d1fae5', border: '#10b981', icon: '#059669' },
            error: { bg: '#fee2e2', border: '#ef4444', icon: '#dc2626' },
            warning: { bg: '#fef3c7', border: '#f59e0b', icon: '#d97706' },
            info: { bg: '#dbeafe', border: '#3b82f6', icon: '#2563eb' }
        };
        
        const color = colors[type] || colors.info;
        
        toast.style.cssText = `
            background: ${color.bg};
            border-left: 4px solid ${color.border};
            color: ${color.icon};
            padding: 1rem 1.5rem;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            min-width: 280px;
            animation: slideInRight 0.3s ease;
        `;
        
        toast.innerHTML = `
            <div class="toast-icon" style="flex-shrink: 0;">
                ${this.getIcon(type)}
            </div>
            <div class="toast-message" style="flex: 1;">${message}</div>
            <button class="toast-close" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: ${color.icon}; opacity: 0.5; padding: 0; line-height: 1;" onclick="Toast.close(this.parentElement)">×</button>
        `;
        
        this.container.appendChild(toast);
        
        // 自动关闭
        setTimeout(() => {
            this.close(toast);
        }, duration);
    },
    
    close(toast) {
        if (!toast || !toast.parentElement) return;
        
        toast.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300);
    },
    
    getIcon(type) {
        const icons = {
            success: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
            error: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
            warning: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
            info: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
        };
        return icons[type] || icons.info;
    }
};

// 添加动画样式
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    img.lazy-loading {
        opacity: 0.5;
        transition: opacity 0.3s ease;
    }
    
    img.lazy-loaded,
    img.loaded {
        opacity: 1;
    }
`;
document.head.appendChild(styleSheet);

// 全局暴露 Toast
window.Toast = Toast;

// ============================================
// 简化的提示函数（兼容旧代码）
// ============================================
function showSuccess(message) { Toast.show(message, 'success'); }
function showError(message) { Toast.show(message, 'error'); }
function showWarning(message) { Toast.show(message, 'warning'); }
function showInfo(message) { Toast.show(message, 'info'); }

// ============================================
// 显示加载中消息
// ============================================
function showLoading(message = '加载中...') {
    let overlay = document.querySelector('.loading-overlay');
    
    if (overlay) {
        return overlay;
    }
    
    overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    
    const content = document.createElement('div');
    content.className = 'loading-content';
    content.innerHTML = `
        <div class="spinner-lg loading" style="margin: 0 auto 1rem;"></div>
        <p style="margin: 0; color: #059669; font-weight: 500;">${message}</p>
    `;
    
    overlay.appendChild(content);
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        backdrop-filter: blur(5px);
    `;
    
    document.body.appendChild(overlay);
    return overlay;
}

function removeLoading(overlay) {
    if (overlay) {
        overlay.style.animation = 'fadeOutLoading 0.3s ease forwards';
        setTimeout(() => {
            if (overlay.parentElement) {
                overlay.remove();
            }
        }, 300);
    }
}

// 添加淡出动画
const fadeOutStyle = document.createElement('style');
fadeOutStyle.textContent = `
    @keyframes fadeOutLoading {
        to { opacity: 0; }
    }
`;
document.head.appendChild(fadeOutStyle);

// ============================================
// 显示提示框（兼容旧代码）
// ============================================
function showAlert(message, type = 'info') {
    Toast.show(message, type);
}

// ============================================
// AJAX 请求封装
// ============================================
async function apiRequest(url, method = 'GET', data = null) {
    const loading = showLoading();
    
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin' // 发送cookies
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `请求失败 (${response.status})`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showError(error.message || '请求失败，请稍后重试');
        return null;
    } finally {
        removeLoading(loading);
    }
}

// ============================================
// 格式化函数
// ============================================
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
    };
    return date.toLocaleDateString('zh-CN', options);
}

function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

function formatNumber(num) {
    return new Intl.NumberFormat('zh-CN').format(num);
}

// ============================================
// 工具函数
// ============================================
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

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

function isEmpty(value) {
    return value === null || value === undefined || value === '';
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
}

// ============================================
// 复制到剪贴板
// ============================================
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccess('已复制到剪贴板');
        }).catch(() => {
            showError('复制失败');
        });
    } else {
        // 降级处理
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showSuccess('已复制到剪贴板');
        } catch (err) {
            showError('复制失败');
        }
        document.body.removeChild(textarea);
    }
}

// ============================================
// 确认对话框
// ============================================
function confirmAction(message, onConfirm, onCancel) {
    const confirmed = confirm(message);
    if (confirmed && typeof onConfirm === 'function') {
        onConfirm();
    } else if (!confirmed && typeof onCancel === 'function') {
        onCancel();
    }
}

// ============================================
// 性能监控（可选）
// ============================================
function reportPerformance() {
    if (window.performance && window.performance.getEntriesByType) {
        const perfData = window.performance.getEntriesByType('navigation')[0];
        if (perfData) {
            console.log('页面加载时间:', perfData.loadEventEnd - perfData.startTime, 'ms');
            console.log('DOM解析时间:', perfData.domContentLoadedEventEnd - perfData.startTime, 'ms');
        }
    }
}

// 页面加载完成后报告性能
window.addEventListener('load', reportPerformance);

// ============================================
// 导出全局函数
// ============================================
window.showLoading = showLoading;
window.removeLoading = removeLoading;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;
window.showAlert = showAlert;
window.apiRequest = apiRequest;
window.formatDate = formatDate;
window.formatCurrency = formatCurrency;
window.formatNumber = formatNumber;
window.debounce = debounce;
window.throttle = throttle;
window.getUrlParameter = getUrlParameter;
window.isEmpty = isEmpty;
window.isValidEmail = isValidEmail;
window.isValidPhone = isValidPhone;
window.copyToClipboard = copyToClipboard;
window.confirmAction = confirmAction;
