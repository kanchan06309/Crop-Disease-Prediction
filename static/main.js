import './style.css'
const API_BASE_URL = 'http://localhost:8000';


// Ensure DOM is ready (covering both module deferred and other states)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
