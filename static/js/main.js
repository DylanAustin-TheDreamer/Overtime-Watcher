const navbarToggler = document.querySelector('.navbar-toggler');
const navBarLinks = document.querySelector('.dropdownNav');

if (navbarToggler && navBarLinks) {
        navbarToggler.addEventListener('click', () => {
                navBarLinks.classList.toggle('dropdownNav-show');
        });
}

// Helper to read CSRF token from cookies (Django default)
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

async function setWakeNow(teamId) {
    const url = `/teams/${teamId}/set-wake/`;
    const csrftoken = getCookie('csrftoken');
    try {
        const resp = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken || ''
            },
            body: JSON.stringify({ wake_time: 'now' }),
        });
        const data = await resp.json();
        if (!resp.ok) throw data;
        // Update the UI: find the awake display for this team and current user
        const display = document.querySelector(`#awake-display-${teamId}`);
        if (display) {
            display.textContent = data.awake_hours + ' h';
            if (data.over_limit) display.classList.add('warning'); else display.classList.remove('warning');
        }
        const btn = document.querySelector(`#wake-btn-${teamId}`);
        if (btn) btn.textContent = 'Set (now) ✓';
    } catch (err) {
        console.error('Failed to set wake time', err);
        alert((err && err.error) ? err.error : 'Failed to set wake time');
    }
}

// expose to global for inline onclick handlers
window.setWakeNow = setWakeNow;

// Live awake timers: find all elements with data-wake and update every second.
(() => {
    const MAX_AWAKE_SECONDS = 17 * 3600; // cap at 17 hours
    // select all elements that have a data-wake attribute (team displays and member spans)
    const elements = Array.from(document.querySelectorAll('[data-wake]'))
        .map(el => ({ el, wake: el.getAttribute('data-wake') }))
        .filter(o => o.wake && o.wake.trim() !== '');

    if (!elements.length) return;

    function updateOnce() {
        const now = new Date();
        elements.forEach(({ el, wake }) => {
            try {
                const wakeDate = new Date(wake);
                if (isNaN(wakeDate)) return;
                let secs = Math.floor((now - wakeDate) / 1000);
                if (secs < 0) secs = 0;
                if (secs > MAX_AWAKE_SECONDS) secs = MAX_AWAKE_SECONDS;
                const hours = (secs / 3600);
                // display with two decimal places
                el.textContent = hours.toFixed(2) + ' h';
                // add warning class if over limit
                if (secs >= MAX_AWAKE_SECONDS) el.classList.add('warning'); else el.classList.remove('warning');
            } catch (e) {
                // ignore
            }
        });
    }

    // initial update
    updateOnce();
    // update every 30 seconds for smoothness (no need to update every second)
    setInterval(updateOnce, 30 * 1000);
})();

