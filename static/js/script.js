/**
 * ShopEase - Interactive Client Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initAlertDismissal();
  initQuantityControls();
  initImageFallbacks();
  initPaymentMethodSelector();
  initAjaxCartButtons();
});

/* ---------------- Mobile Navigation ---------------- */
function initMobileNav() {
  const toggleBtn = document.getElementById('mobileToggleBtn');
  const mainNav = document.getElementById('mainNav');

  if (toggleBtn && mainNav) {
    toggleBtn.addEventListener('click', () => {
      mainNav.classList.toggle('active');
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!mainNav.contains(e.target) && !toggleBtn.contains(e.target)) {
        mainNav.classList.remove('active');
      }
    });
  }
}

/* ---------------- Flash Alerts Dismissal ---------------- */
function initAlertDismissal() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert) => {
    // Add close click
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        dismissAlert(alert);
      });
    }

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      dismissAlert(alert);
    }, 5000);
  });
}

function dismissAlert(alertEl) {
  if (!alertEl) return;
  alertEl.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
  alertEl.style.opacity = '0';
  alertEl.style.transform = 'translateY(-8px)';
  setTimeout(() => {
    if (alertEl.parentNode) {
      alertEl.remove();
    }
  }, 400);
}

/* ---------------- Quantity Selector (+ / -) ---------------- */
function initQuantityControls() {
  const qtyWrappers = document.querySelectorAll('.quantity-control');

  qtyWrappers.forEach((wrapper) => {
    const input = wrapper.querySelector('.qty-input');
    const btnMinus = wrapper.querySelector('.qty-btn-minus');
    const btnPlus = wrapper.querySelector('.qty-btn-plus');

    if (!input || !btnMinus || !btnPlus) return;

    const maxStock = parseInt(input.getAttribute('max') || '9999', 10);
    const minQty = parseInt(input.getAttribute('min') || '1', 10);

    btnMinus.addEventListener('click', () => {
      let currentVal = parseInt(input.value, 10) || minQty;
      if (currentVal > minQty) {
        input.value = currentVal - 1;
        triggerChangeEvent(input);
      }
    });

    btnPlus.addEventListener('click', () => {
      let currentVal = parseInt(input.value, 10) || minQty;
      if (currentVal < maxStock) {
        input.value = currentVal + 1;
        triggerChangeEvent(input);
      } else {
        showToast(`Only ${maxStock} units available in stock.`, 'warning');
      }
    });

    input.addEventListener('change', () => {
      let val = parseInt(input.value, 10);
      if (isNaN(val) || val < minQty) {
        input.value = minQty;
      } else if (val > maxStock) {
        input.value = maxStock;
        showToast(`Adjusted to maximum available stock (${maxStock}).`, 'warning');
      }
    });
  });
}

function triggerChangeEvent(element) {
  const event = new Event('change', { bubbles: true });
  element.dispatchEvent(event);
}

/* ---------------- Image Fallbacks ---------------- */
function initImageFallbacks() {
  const images = document.querySelectorAll('img');
  const fallbackSrc = '/static/images/placeholder.svg';

  images.forEach((img) => {
    img.addEventListener('error', function () {
      if (this.src !== fallbackSrc && !this.src.endsWith(fallbackSrc)) {
        this.src = fallbackSrc;
      }
    });
  });
}

/* ---------------- Checkout Payment Radio Selectors ---------------- */
function initPaymentMethodSelector() {
  const paymentCards = document.querySelectorAll('.payment-method-card');

  paymentCards.forEach((card) => {
    const radio = card.querySelector('input[type="radio"]');
    if (!radio) return;

    // Apply active styling on initial load
    if (radio.checked) {
      highlightPaymentCard(card);
    }

    card.addEventListener('click', () => {
      radio.checked = true;
      highlightPaymentCard(card);
    });

    radio.addEventListener('change', () => {
      if (radio.checked) {
        highlightPaymentCard(card);
      }
    });
  });

  function highlightPaymentCard(selectedCard) {
    paymentCards.forEach((c) => {
      c.style.borderColor = 'var(--border-light)';
      c.style.background = '#ffffff';
    });
    selectedCard.style.borderColor = 'var(--primary)';
    selectedCard.style.background = 'var(--primary-light)';
  }
}

/* ---------------- AJAX Quick Add to Cart ---------------- */
function initAjaxCartButtons() {
  const ajaxButtons = document.querySelectorAll('.btn-ajax-add-cart');

  ajaxButtons.forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const form = btn.closest('form');
      if (!form) return;

      const url = form.action;
      const formData = new FormData(form);

      // Add visual loading state
      const originalHtml = btn.innerHTML;
      btn.innerHTML = `
        <svg style="animation: spin 1s linear infinite; width: 16px; height: 16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
          <path d="M12 2a10 10 0 0 1 10 10" />
        </svg> Adding...
      `;
      btn.disabled = true;

      try {
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
          headers: {
            'x-requested-with': 'XMLHttpRequest',
          },
        });

        if (response.ok) {
          const data = await response.json();
          // Update cart badge in navbar
          const cartBadge = document.querySelector('.cart-badge');
          if (cartBadge && data.cart_count !== undefined) {
            cartBadge.textContent = data.cart_count;
            cartBadge.style.transform = 'scale(1.3)';
            setTimeout(() => {
              cartBadge.style.transform = 'scale(1)';
            }, 250);
          }

          showToast(data.message || 'Product added to cart!', 'success');
        } else {
          // If server responded with redirect or error, fall back to form submit
          form.submit();
        }
      } catch (err) {
        // Fallback to standard form post
        form.submit();
      } finally {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }
    });
  });
}

/* ---------------- Lightweight Toast Notification ---------------- */
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
    `;
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bgColors = {
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#4f46e5',
  };

  toast.style.cssText = `
    background: ${bgColors[type] || '#1e293b'};
    color: #ffffff;
    padding: 12px 20px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);
    display: flex;
    align-items: center;
    gap: 8px;
    pointer-events: auto;
    animation: toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  `;
  toast.textContent = message;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// Add CSS keyframe for toast & spin
const styleEl = document.createElement('style');
styleEl.textContent = `
  @keyframes toastSlideIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleEl);
