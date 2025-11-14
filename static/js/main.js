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