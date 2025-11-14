const navbarToggler = document.querySelector('.navbar-toggler');
const navBarLinks = document.querySelector('.dropdownNav');

if (navbarToggler && navBarLinks) {
        navbarToggler.addEventListener('click', () => {
                navBarLinks.classList.toggle('dropdownNav-show');
        });
}









// Section for real-time awake duration calculation

// Helper to read CSRF token from cookies (Django default)
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

/**
 * Calculate awake duration in real-time
 * @param {string} wakeTime - Time in HH:MM format
 * @param {number} timezoneOffset - GMT offset (e.g., -5 for GMT-5, +3 for GMT+3)
 * @returns {string} Duration as "X.Xh"
 */
function calculateAwakeDuration(wakeTime, timezoneOffset) {
    if (!wakeTime || timezoneOffset === null || timezoneOffset === undefined) {
        return '—';
    }

    // Parse wake time (HH:MM)
    const [wakeHour, wakeMinute] = wakeTime.split(':').map(Number);
    const wakeLocalMinutes = wakeHour * 60 + wakeMinute;

    // Convert wake time to UTC minutes
    const wakeUtcMinutes = wakeLocalMinutes - (timezoneOffset * 60);

    // Get current UTC time in minutes
    const now = new Date();
    const nowUtcMinutes = now.getUTCHours() * 60 + now.getUTCMinutes();

    // Calculate minutes awake (handle day rollover)
    const minutesAwake = (nowUtcMinutes - wakeUtcMinutes + 1440) % 1440;

    // Convert to hours with 1 decimal place
    const hours = minutesAwake / 60;
    return `${hours.toFixed(1)}h`;
}

/**
 * Update all duration displays on the page
 */
function updateAllDurations() {
    const durationElements = document.querySelectorAll('[data-wake-time]');
    
    durationElements.forEach(element => {
        const wakeTime = element.getAttribute('data-wake-time');
        const timezoneOffset = parseFloat(element.getAttribute('data-timezone-offset'));
        
        if (wakeTime && !isNaN(timezoneOffset)) {
            const duration = calculateAwakeDuration(wakeTime, timezoneOffset);
            element.textContent = duration;
            if (parseFloat(duration) >= 16 && parseFloat(duration) < 17){
                element.style.color = "#c48600ff";
            }
            else if (parseFloat(duration) >= 17){
                element.style.color = "#b60000ff";
            }
        }
    });
}

// Initialize real-time duration updates
document.addEventListener('DOMContentLoaded', () => {
    // Update immediately on page load
    updateAllDurations();
    
    // Update every 30 seconds (you can adjust this)
    setInterval(updateAllDurations, 30000);
});


