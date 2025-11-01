/**
 * Local Storage Manager for SPSCon 2025
 * Handles anonymous user data persistence and sync with server when logged in
 */

class LocalStorageManager {
    constructor() {
        this.storageKeys = {
            favorites: 'spscon_favorites',
            visited: 'spscon_visited',
            userPreferences: 'spscon_preferences',
            searchHistory: 'spscon_search_history',
            lastVisit: 'spscon_last_visit'
        };
        
        this.isLoggedIn = document.body.classList.contains('user-logged-in');
        this.init();
    }

    init() {
        // Initialize data structures if they don't exist
        this.initializeStorage();
        
        // Set last visit timestamp
        this.setLastVisit();
        
        // Auto-save user preferences
        this.saveUserPreferences();
        
        // Sync with server if logged in
        if (this.isLoggedIn) {
            this.syncWithServer();
        }
    }

    initializeStorage() {
        // Initialize favorites
        if (!this.getFavorites()) {
            this.setFavorites([]);
        }
        
        // Initialize visited posters
        if (!this.getVisited()) {
            this.setVisited([]);
        }
        
        // Initialize user preferences
        if (!this.getUserPreferences()) {
            this.setUserPreferences({
                theme: 'light',
                notifications: true,
                autoMarkVisited: false,
                showQRCode: true,
                compactView: false
            });
        }
        
        // Initialize search history
        if (!this.getSearchHistory()) {
            this.setSearchHistory([]);
        }
    }

    // Favorites management
    getFavorites() {
        try {
            const favorites = localStorage.getItem(this.storageKeys.favorites);
            return favorites ? JSON.parse(favorites) : [];
        } catch (e) {
            console.error('Error reading favorites from localStorage:', e);
            return [];
        }
    }

    setFavorites(favorites) {
        try {
            localStorage.setItem(this.storageKeys.favorites, JSON.stringify(favorites));
            this.updateFavoritesUI();
        } catch (e) {
            console.error('Error saving favorites to localStorage:', e);
        }
    }

    toggleFavorite(posterId) {
        const favorites = this.getFavorites();
        const index = favorites.indexOf(posterId);
        
        if (index > -1) {
            favorites.splice(index, 1);
            this.setFavorites(favorites);
            return false; // Removed
        } else {
            favorites.push(posterId);
            this.setFavorites(favorites);
            return true; // Added
        }
    }

    isFavorite(posterId) {
        return this.getFavorites().includes(posterId);
    }

    // Visited posters management
    getVisited() {
        try {
            const visited = localStorage.getItem(this.storageKeys.visited);
            return visited ? JSON.parse(visited) : [];
        } catch (e) {
            console.error('Error reading visited from localStorage:', e);
            return [];
        }
    }

    setVisited(visited) {
        try {
            localStorage.setItem(this.storageKeys.visited, JSON.stringify(visited));
            this.updateVisitedUI();
        } catch (e) {
            console.error('Error saving visited to localStorage:', e);
        }
    }

    toggleVisited(posterId) {
        const visited = this.getVisited();
        const index = visited.indexOf(posterId);
        
        if (index > -1) {
            visited.splice(index, 1);
            this.setVisited(visited);
            return false; // Removed
        } else {
            visited.push(posterId);
            this.setVisited(visited);
            return true; // Added
        }
    }
    
    markVisited(posterId) {
        const visited = this.getVisited();
        if (!visited.includes(posterId)) {
            visited.push(posterId);
            this.setVisited(visited);
            return true; // Newly visited
        }
        return false; // Already visited
    }

    isVisited(posterId) {
        return this.getVisited().includes(posterId);
    }

    // User preferences management
    getUserPreferences() {
        try {
            const preferences = localStorage.getItem(this.storageKeys.userPreferences);
            return preferences ? JSON.parse(preferences) : {};
        } catch (e) {
            console.error('Error reading preferences from localStorage:', e);
            return {};
        }
    }

    setUserPreferences(preferences) {
        try {
            localStorage.setItem(this.storageKeys.userPreferences, JSON.stringify(preferences));
            this.applyPreferences(preferences);
        } catch (e) {
            console.error('Error saving preferences to localStorage:', e);
        }
    }

    updatePreference(key, value) {
        const preferences = this.getUserPreferences();
        preferences[key] = value;
        this.setUserPreferences(preferences);
    }

    // Search history management
    getSearchHistory() {
        try {
            const history = localStorage.getItem(this.storageKeys.searchHistory);
            return history ? JSON.parse(history) : [];
        } catch (e) {
            console.error('Error reading search history from localStorage:', e);
            return [];
        }
    }

    setSearchHistory(history) {
        try {
            // Keep only last 20 searches
            const limitedHistory = history.slice(-20);
            localStorage.setItem(this.storageKeys.searchHistory, JSON.stringify(limitedHistory));
        } catch (e) {
            console.error('Error saving search history to localStorage:', e);
        }
    }

    addSearchQuery(query) {
        if (!query || query.trim().length < 2) return;
        
        const history = this.getSearchHistory();
        const trimmedQuery = query.trim();
        
        // Remove if already exists
        const index = history.indexOf(trimmedQuery);
        if (index > -1) {
            history.splice(index, 1);
        }
        
        // Add to beginning
        history.unshift(trimmedQuery);
        this.setSearchHistory(history);
    }

    // Last visit tracking
    setLastVisit() {
        try {
            localStorage.setItem(this.storageKeys.lastVisit, new Date().toISOString());
        } catch (e) {
            console.error('Error saving last visit to localStorage:', e);
        }
    }

    getLastVisit() {
        try {
            return localStorage.getItem(this.storageKeys.lastVisit);
        } catch (e) {
            console.error('Error reading last visit from localStorage:', e);
            return null;
        }
    }

    // UI Updates
    updateFavoriteButton(posterId) {
        const btn = document.getElementById(`favoriteBtn${posterId}`);
        if (!btn) return;
        
        const favorites = this.getFavorites();
        const isFavorite = favorites.includes(posterId);
        
        if (isFavorite) {
            btn.innerHTML = '<i class="bi bi-heart-fill"></i> Remove from Favorites';
            btn.classList.add('favorited');
        } else {
            btn.innerHTML = '<i class="bi bi-heart"></i> Add to Favorites';
            btn.classList.remove('favorited');
        }
        
        // Update navbar count
        this.updateNavbarCounts();
    }

    updateVisitedButton(posterId) {
        const btn = document.getElementById(`visitBtn${posterId}`);
        if (!btn) return;
        
        const visited = this.getVisited();
        const isVisited = visited.includes(posterId);
        
        if (isVisited) {
            btn.innerHTML = '<i class="bi bi-check-circle"></i> Visited';
            btn.classList.add('btn-success');
            btn.classList.remove('btn-outline-success');
        } else {
            btn.innerHTML = '<i class="bi bi-check-circle"></i> Mark as Visited';
            btn.classList.remove('btn-success');
            btn.classList.add('btn-outline-success');
        }
        
        // Update navbar count
        this.updateNavbarCounts();
    }
    
    updateNavbarCounts() {
        // Only update from localStorage for anonymous users
        // Logged-in users' counts come from server and are updated via API responses
        if (!this.isLoggedIn) {
            // Update favorites count
            const favoritesCountSpan = document.querySelector('.favorites-count');
            if (favoritesCountSpan) {
                const favorites = this.getFavorites();
                favoritesCountSpan.textContent = favorites.length;
            }
            
            // Update visited count
            const visitedCountSpan = document.querySelector('.visited-count');
            if (visitedCountSpan) {
                const visited = this.getVisited();
                visitedCountSpan.textContent = visited.length;
            }
        }
    }
    
    incrementNavbarCount(type) {
        // Increment navbar count by 1 (for logged-in users after API success)
        const countSpan = document.querySelector(type === 'favorite' ? '.favorites-count' : '.visited-count');
        if (countSpan) {
            const currentCount = parseInt(countSpan.textContent) || 0;
            countSpan.textContent = currentCount + 1;
        }
        
        // Also update the dashboard stat card if we're on the dashboard
        if (type === 'visited') {
            const dashboardCounter = document.getElementById('totalVisitsCounter');
            if (dashboardCounter) {
                const currentCount = parseInt(dashboardCounter.textContent) || 0;
                dashboardCounter.textContent = currentCount + 1;
            }
        }
    }
    
    decrementNavbarCount(type) {
        // Decrement navbar count by 1 (for logged-in users after API success)
        const countSpan = document.querySelector(type === 'favorite' ? '.favorites-count' : '.visited-count');
        if (countSpan) {
            const currentCount = parseInt(countSpan.textContent) || 0;
            countSpan.textContent = Math.max(0, currentCount - 1);
        }
        
        // Also update the dashboard stat card if we're on the dashboard
        if (type === 'visited') {
            const dashboardCounter = document.getElementById('totalVisitsCounter');
            if (dashboardCounter) {
                const currentCount = parseInt(dashboardCounter.textContent) || 0;
                dashboardCounter.textContent = Math.max(0, currentCount - 1);
            }
        }
    }

    applyPreferences(preferences) {
        // Apply theme
        if (preferences.theme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
        
        // Apply compact view
        if (preferences.compactView) {
            document.body.classList.add('compact-view');
        } else {
            document.body.classList.remove('compact-view');
        }
        
        // Apply auto-mark visited
        if (preferences.autoMarkVisited) {
            this.enableAutoMarkVisited();
        }
    }

    enableAutoMarkVisited() {
        // Auto-mark posters as visited when scrolled into view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const posterId = parseInt(entry.target.dataset.posterId);
                    if (posterId && !this.isVisited(posterId)) {
                        this.markVisited(posterId);
                        showToast('Auto-marked as visited!', 'info');
                    }
                }
            });
        }, { threshold: 0.5 });
        
        document.querySelectorAll('.poster-card').forEach(card => {
            observer.observe(card);
        });
    }

    // Server sync for logged-in users
    async syncWithServer() {
        if (!this.isLoggedIn) return;
        
        try {
            // Get server data
            const response = await fetch('/api/user-data');
            if (response.ok) {
                const serverData = await response.json();
                
                // Merge with local data (server takes precedence)
                const localFavorites = this.getFavorites();
                const localVisited = this.getVisited();
                
                // Update local storage with server data
                if (serverData.favorites) {
                    this.setFavorites(serverData.favorites);
                }
                if (serverData.visited) {
                    this.setVisited(serverData.visited);
                }
            }
        } catch (error) {
            console.error('Error syncing with server:', error);
        }
    }

    // Export/Import functionality
    exportData() {
        const data = {
            favorites: this.getFavorites(),
            visited: this.getVisited(),
            preferences: this.getUserPreferences(),
            searchHistory: this.getSearchHistory(),
            exportDate: new Date().toISOString(),
            version: '1.0'
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `spscon-data-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showToast('Data exported successfully!', 'success');
    }

    importData(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                
                if (data.favorites) this.setFavorites(data.favorites);
                if (data.visited) this.setVisited(data.visited);
                if (data.preferences) this.setUserPreferences(data.preferences);
                if (data.searchHistory) this.setSearchHistory(data.searchHistory);
                
                showToast('Data imported successfully!', 'success');
                this.updateFavoritesUI();
                this.updateVisitedUI();
            } catch (error) {
                showToast('Error importing data. Please check file format.', 'danger');
            }
        };
        reader.readAsText(file);
    }

    // Clear all data
    clearAllData() {
        if (confirm('Are you sure you want to clear all your local data? This cannot be undone.')) {
            Object.values(this.storageKeys).forEach(key => {
                localStorage.removeItem(key);
            });
            this.initializeStorage();
            this.updateFavoritesUI();
            this.updateVisitedUI();
            showToast('All data cleared!', 'info');
        }
    }

    // Get storage usage info
    getStorageInfo() {
        let totalSize = 0;
        Object.values(this.storageKeys).forEach(key => {
            const value = localStorage.getItem(key);
            if (value) {
                totalSize += value.length;
            }
        });
        
        return {
            totalSize: totalSize,
            totalSizeKB: (totalSize / 1024).toFixed(2),
            items: Object.keys(this.storageKeys).length,
            lastVisit: this.getLastVisit()
        };
    }
    
    // User preferences methods
    getUserPreferences() {
        try {
            return JSON.parse(localStorage.getItem(this.storageKeys.preferences) || '{}');
        } catch (e) {
            return {};
        }
    }
    
    setUserPreferences(preferences) {
        try {
            localStorage.setItem(this.storageKeys.preferences, JSON.stringify(preferences));
            return true;
        } catch (e) {
            console.error('Error saving user preferences:', e);
            return false;
        }
    }
    
    saveUserPreferences() {
        // Auto-save current preferences
        const currentPrefs = this.getUserPreferences();
        if (Object.keys(currentPrefs).length > 0) {
            this.setUserPreferences(currentPrefs);
        }
    }
}

// Initialize the local storage manager
// Note: localStorageManager is initialized in base.html to avoid conflicts

// Enhanced API functions that work with both logged-in and anonymous users
async function toggleFavoriteAPI(posterId) {
    const btn = document.getElementById(`favoriteBtn${posterId}`);
    // If guest, operate purely locally for instant UX
    if (document.body.classList.contains('user-anonymous')) {
        localStorageManager.toggleFavorite(posterId);
        localStorageManager.updateFavoriteButton(posterId);
        showToast(localStorageManager.isFavorite(posterId) ? 'Added to favorites!' : 'Removed from favorites!', localStorageManager.isFavorite(posterId) ? 'success' : 'info');
        return;
    }
    const originalText = showLoading(btn);
    
    try {
        const response = await fetch(`/api/favorite/${posterId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        let data = null;
        try {
            data = await response.json();
        } catch (e) {
            // If response is not JSON (e.g., redirect), treat as local storage
            data = { use_local_storage: true };
        }
        
        hideLoading(btn, originalText);
        
        if (data.use_local_storage) {
            // Handle with local storage
            localStorageManager.toggleFavorite(posterId);
            localStorageManager.updateFavoriteButton(posterId);
            showToast(localStorageManager.isFavorite(posterId) ? 'Added to favorites!' : 'Removed from favorites!', localStorageManager.isFavorite(posterId) ? 'success' : 'info');
        } else {
            // Handle server response for logged-in user
            // Update button state based on API response, not localStorage
            if (data.status === 'added') {
                btn.innerHTML = '<i class="bi bi-heart-fill"></i> Remove from Favorites';
                btn.classList.add('favorited');
                localStorageManager.incrementNavbarCount('favorite');
                showToast('Added to favorites!', 'success');
            } else if (data.status === 'removed') {
                btn.innerHTML = '<i class="bi bi-heart"></i> Add to Favorites';
                btn.classList.remove('favorited');
                localStorageManager.decrementNavbarCount('favorite');
                showToast('Removed from favorites!', 'info');
            }
        }
    } catch (error) {
        hideLoading(btn, originalText);
        // Network/parse issue – still fall back to local storage for a smooth UX
        localStorageManager.toggleFavorite(posterId);
        localStorageManager.updateFavoriteButton(posterId);
        showToast(localStorageManager.isFavorite(posterId) ? 'Added to favorites!' : 'Removed from favorites!', localStorageManager.isFavorite(posterId) ? 'success' : 'info');
    }
}

async function markVisitedAPI(posterId) {
    const btn = document.getElementById(`visitBtn${posterId}`);
    // If guest, operate purely locally for instant UX
    if (document.body.classList.contains('user-anonymous')) {
        const wasAdded = localStorageManager.toggleVisited(posterId);
        localStorageManager.updateVisitedButton(posterId);
        showToast(wasAdded ? 'Marked as visited!' : 'Removed from visited', wasAdded ? 'success' : 'info');
        return;
    }
    const originalText = showLoading(btn);
    
    try {
        const response = await fetch(`/api/visit/${posterId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        let data = null;
        try {
            data = await response.json();
        } catch (e) {
            // If response is not JSON (e.g., redirect), treat as local storage
            data = { use_local_storage: true };
        }
        
        hideLoading(btn, originalText);
        
        if (data.use_local_storage) {
            // Handle with local storage
            const wasAdded = localStorageManager.toggleVisited(posterId);
            localStorageManager.updateVisitedButton(posterId);
            showToast(wasAdded ? 'Marked as visited!' : 'Removed from visited', wasAdded ? 'success' : 'info');
        } else {
            // Handle server response for logged-in user
            // Update button state based on API response, not localStorage
            if (data.status === 'added') {
                btn.innerHTML = '<i class="bi bi-check-circle"></i> Visited';
                btn.classList.add('btn-success');
                btn.classList.remove('btn-outline-success');
                localStorageManager.incrementNavbarCount('visited');
                showToast('Marked as visited!', 'success');
            } else if (data.status === 'removed') {
                btn.innerHTML = '<i class="bi bi-check-circle"></i> Mark as Visited';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-success');
                localStorageManager.decrementNavbarCount('visited');
                showToast('Removed from visited', 'info');
            } else {
                showToast(data.message || 'Info', 'info');
            }
        }
    } catch (error) {
        hideLoading(btn, originalText);
        // Network/parse issue – still fall back to local storage for a smooth UX
        const wasAdded = localStorageManager.toggleVisited(posterId);
        localStorageManager.updateVisitedButton(posterId);
        showToast(wasAdded ? 'Marked as visited!' : 'Removed from visited', wasAdded ? 'success' : 'info');
    }
}

// Auto-save search queries
function autoSaveSearch(query) {
    if (query && query.trim().length >= 2) {
        localStorageManager.addSearchQuery(query.trim());
    }
}

// Initialize UI on page load
document.addEventListener('DOMContentLoaded', function() {
    localStorageManager.updateFavoritesUI();
    localStorageManager.updateVisitedUI();
    
    // Add search autocomplete
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        const searchHistory = localStorageManager.getSearchHistory();
        
        // Add autocomplete functionality
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const matches = searchHistory.filter(item => 
                item.toLowerCase().includes(query)
            ).slice(0, 5);
            
            // Show autocomplete suggestions
            showSearchSuggestions(matches, this);
        });
        
        // Save search on form submit
        const searchForm = searchInput.closest('form');
        if (searchForm) {
            searchForm.addEventListener('submit', function() {
                autoSaveSearch(searchInput.value);
            });
        }
    }
});

function showSearchSuggestions(suggestions, input) {
    // Remove existing suggestions
    const existingSuggestions = document.querySelector('.search-suggestions');
    if (existingSuggestions) {
        existingSuggestions.remove();
    }
    
    if (suggestions.length === 0) return;
    
    // Create suggestions container
    const container = document.createElement('div');
    container.className = 'search-suggestions position-absolute bg-white border rounded shadow-sm';
    container.style.top = '100%';
    container.style.left = '0';
    container.style.right = '0';
    container.style.zIndex = '1000';
    
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item p-2 border-bottom cursor-pointer';
        item.textContent = suggestion;
        item.addEventListener('click', function() {
            input.value = suggestion;
            container.remove();
            input.focus();
        });
        container.appendChild(item);
    });
    
    // Position relative to input
    input.parentElement.style.position = 'relative';
    input.parentElement.appendChild(container);
    
    // Remove suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!container.contains(e.target) && e.target !== input) {
            container.remove();
        }
    });
}

// Export for global use
window.localStorageManager = localStorageManager;
window.toggleFavoriteAPI = toggleFavoriteAPI;
window.markVisitedAPI = markVisitedAPI;
window.autoSaveSearch = autoSaveSearch;
