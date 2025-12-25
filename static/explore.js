// Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const diseaseContainer = document.getElementById('disease-container');
const loadingSpinner = document.getElementById('loading-spinner');
const errorMessage = document.getElementById('error-message');
const searchInput = document.getElementById('search-input');
const filterSelect = document.getElementById('filter-crop');
const resultsCount = document.getElementById('results-count');

// State
let allDiseases = [];
let filteredDiseases = [];

/**
 * Initialize the application
 */
function init() {
    console.log('🚀 Initializing Crop Disease Explorer...');
    initializeEventListeners();
    fetchDiseases();
}

/**
 * Fetch disease data from API
 */
async function fetchDiseases() {
    try {
        showLoading(true);
        hideError();
        
        // Ensure your Flask backend has a route: @app.route('/api/explore')
        const response = await fetch(`${API_BASE_URL}/api/explore`);
        
        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Adjust this check based on how your Python API returns data
        // Assuming it returns { success: true, data: [...] }
        if (result.success || Array.isArray(result)) {
            // Handle if result is just the array or an object wrapper
            allDiseases = result.data || result; 
            filteredDiseases = [...allDiseases];
            
            populateFilterDropdown();
            renderDiseases(filteredDiseases);
            updateResultsCount();
            
            console.log(`✅ Loaded ${allDiseases.length} items`);
        } else {
            throw new Error('API returned unsuccessful response');
        }
        
    } catch (error) {
        console.error('Error fetching diseases:', error);
        showError(`⚠️ Could not load data. Is the Backend Server running? (${error.message})`);
    } finally {
        showLoading(false);
    }
}

/**
 * Populate the crop filter dropdown
 */
function populateFilterDropdown() {
    if (!filterSelect) return;
    
    // Get unique crop names safely
    const uniqueCrops = [...new Set(allDiseases.map(d => d.crop_name))];
    uniqueCrops.sort();
    
    // Clear existing options (except "All Crops")
    filterSelect.innerHTML = '<option value="">All Crops</option>';
    
    // Add crop options
    uniqueCrops.forEach(crop => {
        const option = document.createElement('option');
        option.value = crop;
        option.textContent = crop;
        filterSelect.appendChild(option);
    });
}

/**
 * Render disease cards
 */
function renderDiseases(diseases) {
    if (!diseaseContainer) return;
    
    diseaseContainer.innerHTML = '';
    
    if (diseases.length === 0) {
        diseaseContainer.innerHTML = `
            <div class="no-results" style="grid-column: 1/-1; text-align: center;">
                <p>No results found matching your criteria.</p>
            </div>
        `;
        return;
    }
    
    diseases.forEach(disease => {
        const card = createDiseaseCard(disease);
        diseaseContainer.appendChild(card);
    });
}

/**
 * Create a disease card element
 */
function createDiseaseCard(disease) {
    const card = document.createElement('div');
    // Using existing class 'explore-card' from your CSS, adding 'disease-card' for JS targeting
    card.className = 'explore-card disease-card'; 
    
    // Safe checks for null data
    const imgUrl = disease.crop_image_url || 'https://via.placeholder.com/400x200?text=No+Image';
    const symptoms = disease.symptoms || 'No detailed symptoms available.';
    const treatment = disease.treatment_name || 'Consult an expert.';

    card.innerHTML = `
        <div class="card-image-wrapper" style="margin-bottom:15px;">
            <img src="${imgUrl}" alt="${disease.crop_name}" style="width:100%; border-radius:8px; height:150px; object-fit:cover;">
            <div class="badge" style="margin-top:5px;">${disease.crop_name}</div>
        </div>
        
        <h3>${disease.disease_name}</h3>
        
        <div class="card-details" style="font-size: 0.9rem; color: #ccc;">
            <p><strong>Symptoms:</strong> ${symptoms.substring(0, 80)}...</p>
            <p><strong>Treatment:</strong> ${treatment}</p>
        </div>
    `;
    
    return card;
}

/**
 * Filter diseases by search term and crop selection
 */
function filterDiseases() {
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const selectedCrop = filterSelect ? filterSelect.value : '';
    
    filteredDiseases = allDiseases.filter(disease => {
        // Safe null checks
        const dName = (disease.disease_name || '').toLowerCase();
        const cName = (disease.crop_name || '').toLowerCase();
        const symp = (disease.symptoms || '').toLowerCase();

        // Search filter
        const matchesSearch = !searchTerm || 
            dName.includes(searchTerm) ||
            cName.includes(searchTerm) ||
            symp.includes(searchTerm);
        
        // Crop filter
        const matchesCrop = !selectedCrop || disease.crop_name === selectedCrop;
        
        return matchesSearch && matchesCrop;
    });
    
    renderDiseases(filteredDiseases);
    updateResultsCount();
}

/**
 * Update results count display
 */
function updateResultsCount() {
    if (resultsCount) {
        resultsCount.textContent = `Showing ${filteredDiseases.length} results`;
    }
}

/**
 * Show/hide loading spinner
 */
function showLoading(show) {
    if (loadingSpinner) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }
}

/**
 * Show error message
 */
function showError(message) {
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
}

/**
 * Hide error message
 */
function hideError() {
    if (errorMessage) {
        errorMessage.style.display = 'none';
    }
}

/**
 * Debounce function for search input
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterDiseases, 300));
    }
    
    if (filterSelect) {
        filterSelect.addEventListener('change', filterDiseases);
    }
}

// Start the application
document.addEventListener('DOMContentLoaded', init);