// API Base URL Configuration
// When running in docker, API is accessed via relative proxy or external IP.
// We'll detect context or default to environment
const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : ''; // Empty string assumes Nginx proxies /api request to backend

let currentSource = null;
let searchQuery = '';

document.addEventListener('DOMContentLoaded', () => {
    fetchSources();
    fetchNews();
    setupEventListeners();
});

function setupEventListeners() {
    // Search functionality with debounce
    const searchInput = document.getElementById('search-input');
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = e.target.value;
            fetchNews();
        }, 500);
    });

    // Refresh Manual Trigger
    document.getElementById('refresh-btn').addEventListener('click', async function() {
        const icon = this.querySelector('i');
        icon.classList.add('spin');
        this.disabled = true;
        
        try {
            await fetch(`${API_BASE}/api/trigger-aggregation`, { method: 'POST' });
            // Wait a tiny bit for aggregation to start saving then refetch
            setTimeout(() => {
                fetchNews();
                icon.classList.remove('spin');
                this.disabled = false;
            }, 2000);
        } catch (err) {
            console.error("Trigger failed", err);
            icon.classList.remove('spin');
            this.disabled = false;
        }
    });

    // Filter All Button
    document.querySelector('[data-filter="all"]').addEventListener('click', function() {
        currentSource = null;
        
        // Update UI Active State
        document.querySelectorAll('.nav-links li, .source-list li').forEach(el => el.classList.remove('active'));
        this.classList.add('active');
        
        document.getElementById('page-title').innerText = 'Latest Discovery';
        fetchNews();
    });

    // Modal Logic
    const modal = document.getElementById('add-source-modal');
    const openBtn = document.getElementById('open-modal-btn');
    const closeBtns = [document.getElementById('close-modal-btn'), document.getElementById('cancel-btn')];
    const form = document.getElementById('add-source-form');

    openBtn.addEventListener('click', () => modal.classList.remove('hidden'));
    closeBtns.forEach(btn => btn.addEventListener('click', () => modal.classList.add('hidden')));
    
    // Handle clicking backdrop
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerText;
        submitBtn.innerText = 'Saving...';
        submitBtn.disabled = true;

        const payload = {
            name: document.getElementById('src-name').value,
            url: document.getElementById('src-url').value,
            category: document.getElementById('src-cat').value || 'General'
        };

        try {
            const response = await fetch(`${API_BASE}/api/sources/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to add source');
            }

            // Success
            form.reset();
            modal.classList.add('hidden');
            
            // Show quick feedback toast could go here
            alert('Source added successfully! Fetching news...');
            
            // Refresh list and re-run aggregator
            fetchSources();
            fetchNews();
            
        } catch (error) {
            alert(error.message);
        } finally {
            submitBtn.innerText = originalText;
            submitBtn.disabled = false;
        }
    });

    // Settings Modal Logic
    const settingsModal = document.getElementById('settings-modal');
    const openSettingsBtn = document.getElementById('open-settings-link');
    const closeSettingsBtns = [document.getElementById('close-settings-btn'), document.getElementById('cancel-settings-btn')];
    const settingsForm = document.getElementById('settings-form');

    openSettingsBtn.addEventListener('click', async () => {
        // Load current settings first
        try {
            const response = await fetch(`${API_BASE}/api/settings/`);
            const config = await response.json();
            
            document.getElementById('discord-enabled').checked = config.discord_enabled;
            document.getElementById('discord-url').value = config.discord_webhook_url || '';
            
            document.getElementById('telegram-enabled').checked = config.telegram_enabled;
            document.getElementById('telegram-token').value = config.telegram_bot_token || '';
            document.getElementById('telegram-chat').value = config.telegram_chat_id || '';

            // Load AI Config
            document.getElementById('ai-enabled').checked = config.ai_deduplication_enabled || false;
            document.getElementById('gemini-key').value = config.gemini_api_key || '';
            
            settingsModal.classList.remove('hidden');
        } catch (err) {
            alert('Could not load settings.');
        }
    });

    closeSettingsBtns.forEach(btn => btn.addEventListener('click', () => settingsModal.classList.add('hidden')));
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) settingsModal.classList.add('hidden');
    });

    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const saveBtn = settingsForm.querySelector('button[type="submit"]');
        saveBtn.innerText = 'Saving Configurations...';
        saveBtn.disabled = true;

        const configPayload = {
            discord_enabled: document.getElementById('discord-enabled').checked,
            discord_webhook_url: document.getElementById('discord-url').value,
            telegram_enabled: document.getElementById('telegram-enabled').checked,
            telegram_bot_token: document.getElementById('telegram-token').value,
            telegram_chat_id: document.getElementById('telegram-chat').value,
            // Append AI fields
            gemini_api_key: document.getElementById('gemini-key').value,
            ai_deduplication_enabled: document.getElementById('ai-enabled').checked
        };

        try {
            const response = await fetch(`${API_BASE}/api/settings/`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configPayload)
            });
            if (response.ok) {
                alert('Notifications configurations stored and activated successfully!');
                settingsModal.classList.add('hidden');
            } else {
                throw new Error('Failed to update');
            }
        } catch (err) {
            alert('Save failed: ' + err.message);
        } finally {
            saveBtn.innerText = 'Save Configurations';
            saveBtn.disabled = false;
        }
    });
}

async function fetchSources() {
    try {
        // Changed to query list of actual configured sources
        const response = await fetch(`${API_BASE}/api/sources/`);
        const sources = await response.json();
        
        const sourceList = document.getElementById('source-list');
        sourceList.innerHTML = '';
        
        if (sources.length === 0) {
            sourceList.innerHTML = '<li class="loading-item">No sources added yet</li>';
            return;
        }

        sources.forEach(source => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fa-solid fa-hashtag"></i> <span>${source.name}</span>`;
            li.addEventListener('click', () => {
                // Update active state
                document.querySelectorAll('.nav-links li, .source-list li').forEach(el => el.classList.remove('active'));
                li.classList.add('active');
                
                currentSource = source.name;
                document.getElementById('page-title').innerText = source.name;
                fetchNews();
            });
            sourceList.appendChild(li);
        });
    } catch (error) {
        console.error("Error fetching sources:", error);
        document.getElementById('source-list').innerHTML = '<li class="loading-item">Error loading sources</li>';
    }
}

async function fetchNews() {
    const grid = document.getElementById('news-grid');
    const loader = document.getElementById('loader');
    const emptyState = document.getElementById('empty-state');
    
    // Show loader
    loader.classList.remove('hidden');
    grid.classList.add('hidden');
    emptyState.classList.add('hidden');
    
    try {
        let url = `${API_BASE}/api/news/?limit=30`;
        if (currentSource) url += `&source=${encodeURIComponent(currentSource)}`;
        if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
        
        const response = await fetch(url);
        const news = await response.json();
        
        grid.innerHTML = '';
        
        if (news.length === 0) {
            emptyState.classList.remove('hidden');
        } else {
            news.forEach(article => {
                const card = createNewsCard(article);
                grid.appendChild(card);
            });
            grid.classList.remove('hidden');
        }
    } catch (error) {
        console.error("Error fetching news:", error);
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: #ef4444;">Failed to connect to backend. Make sure containers are running.</div>`;
        grid.classList.remove('hidden');
    } finally {
        loader.classList.add('hidden');
    }
}

function createNewsCard(article) {
    const card = document.createElement('a');
    card.href = article.link;
    card.target = "_blank";
    card.className = 'news-card';
    
    const date = new Date(article.published_at);
    const formattedDate = date.toLocaleDateString('vi-VN', { 
        day: 'numeric', 
        month: 'short', 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    // Fallback image strategy
    const imgUrl = article.image_url || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=500&q=80';
    
    card.innerHTML = `
        <div class="news-card-image" style="background-image: url('${imgUrl}')">
            <span class="source-tag">${article.source_name}</span>
        </div>
        <div class="news-card-content">
            <span class="news-date">${formattedDate}</span>
            <h3 class="news-title">${article.title}</h3>
            <p class="news-summary">${article.summary || 'Click to read more...'}</p>
            <div class="card-footer">
                <span>${article.category}</span>
                <span class="read-more">Read Details <i class="fa-solid fa-arrow-right"></i></span>
            </div>
        </div>
    `;
    
    return card;
}
