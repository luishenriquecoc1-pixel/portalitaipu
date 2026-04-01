// Portal MKT - Global JavaScript Utilities

// API Helper
async function api(url, method = 'GET', body = null) {
    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) options.body = JSON.stringify(body);
    const res = await fetch(url, options);
    if (res.status === 307 || res.redirected) { window.location.href = '/login'; return null; }
    return res.json();
}

// Format numbers
function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('pt-BR');
}

function timeAgo(dateStr) {
    const now = new Date();
    const d = new Date(dateStr);
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return 'agora';
    if (diff < 3600) return Math.floor(diff / 60) + 'min';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h';
    if (diff < 604800) return Math.floor(diff / 86400) + 'd';
    return formatDate(dateStr);
}

// Toast notification with animation
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const colors = { success: 'bg-green-500', error: 'bg-red-500', warning: 'bg-amber-500', info: 'bg-blue-500' };
    const icons = { success: 'check-circle', error: 'x-circle', warning: 'exclamation-triangle', info: 'info-circle' };
    toast.className = `fixed bottom-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-xl shadow-lg z-[100] flex items-center gap-2 text-sm font-medium animate-fadeInUp`;
    toast.innerHTML = `<i class="bi bi-${icons[type]}"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// Counter animation for KPI numbers
function animateCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseInt(el.dataset.counter);
        const duration = 1200;
        const start = performance.now();
        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            el.textContent = Math.floor(target * eased).toLocaleString('pt-BR');
            if (progress < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    });
}

// Stagger animation helper
function staggerElements(selector, animClass = 'animate-fadeInUp', delayMs = 60) {
    document.querySelectorAll(selector).forEach((el, i) => {
        el.style.opacity = '0';
        el.style.animationDelay = `${i * delayMs}ms`;
        el.classList.add(animClass);
        el.addEventListener('animationend', () => { el.style.opacity = ''; }, { once: true });
    });
}

// Ripple effect for buttons
document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-ripple');
    if (!btn) return;
    const ripple = document.createElement('span');
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    ripple.style.cssText = `position:absolute;width:${size}px;height:${size}px;left:${e.clientX - rect.left - size / 2}px;top:${e.clientY - rect.top - size / 2}px;background:rgba(255,255,255,0.3);border-radius:50%;transform:scale(0);animation:ripple 0.6s ease-out;pointer-events:none;`;
    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
});

// Esc to close modals
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('[id$="-modal"]').forEach(m => m.classList.add('hidden'));
    }
});

// Click outside modal to close
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('fixed') && e.target.classList.contains('backdrop-blur-sm')) {
        e.target.classList.add('hidden');
    }
});

// Init counters on load
document.addEventListener('DOMContentLoaded', animateCounters);
