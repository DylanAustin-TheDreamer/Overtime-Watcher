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
