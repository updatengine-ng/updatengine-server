/**
 * UPDATENGINE MODERN - Main JavaScript
 * NinjaOne-inspired interactions
 */

// Import dependencies
import Alpine from 'alpinejs';
import htmx from 'htmx.org';
import Chart from 'chart.js/auto';

// ========================================
// ALPINE.JS SETUP
// ========================================

// Initialize Alpine.js
window.Alpine = Alpine;
Alpine.start();

// Dark mode toggle component
Alpine.data('darkMode', () => ({
  dark: localStorage.getItem('darkMode') === 'true',
  
  init() {
    this.updateTheme();
  },
  
  toggle() {
    this.dark = !this.dark;
    localStorage.setItem('darkMode', this.dark);
    this.updateTheme();
  },
  
  updateTheme() {
    if (this.dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }
}));

// Sidebar toggle component
Alpine.data('sidebar', () => ({
  open: true,
  
  toggle() {
    this.open = !this.open;
  }
}));

// Notifications component
Alpine.data('notifications', () => ({
  items: [],
  
  add(message, type = 'info') {
    const id = Date.now();
    this.items.push({ id, message, type });
    
    // Auto-remove after 5 seconds
    setTimeout(() => this.remove(id), 5000);
  },
  
  remove(id) {
    this.items = this.items.filter(item => item.id !== id);
  }
}));

// ========================================
// HTMX CONFIGURATION
// ========================================

// HTMX global config
document.body.addEventListener('htmx:configRequest', (event) => {
  // Add CSRF token to all requests
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  if (csrfToken) {
    event.detail.headers['X-CSRFToken'] = csrfToken;
  }
});

// HTMX loading indicators
document.body.addEventListener('htmx:beforeRequest', (event) => {
  event.target.classList.add('htmx-loading');
});

document.body.addEventListener('htmx:afterRequest', (event) => {
  event.target.classList.remove('htmx-loading');
});

// ========================================
// CHARTS (Chart.js)
// ========================================

// Global chart defaults
Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
Chart.defaults.color = '#6b7280';
Chart.defaults.borderColor = '#e5e7eb';

// Function to create a dashboard chart
window.createDashboardChart = (elementId, config) => {
  const ctx = document.getElementById(elementId);
  if (!ctx) return null;
  
  return new Chart(ctx, {
    ...config,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      ...config.options
    }
  });
};

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Debounce function for search inputs
window.debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Copy to clipboard
window.copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
};

// Format bytes to human readable
window.formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

// ========================================
// WEBSOCKET (for real-time updates)
// ========================================

class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };
  }
  
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
    }
  }
  
  handleMessage(data) {
    // Dispatch custom event for components to listen
    document.dispatchEvent(new CustomEvent('ws:message', { detail: data }));
  }
  
  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

// Initialize WebSocket if needed
// const wsManager = new WebSocketManager('ws://localhost:8000/ws/');
// wsManager.connect();

// ========================================
// INITIALIZATION
// ========================================

console.log('✨ UpdatEngine Modern initialized!');

// Export for global access
export { Chart, Alpine, htmx };
