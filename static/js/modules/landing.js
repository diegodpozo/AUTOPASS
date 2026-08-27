import { initMap, findNearestBranch, filterMapByLocality } from './landing-map.js';
import { InicializarCarrusel } from './landing-carousel.js';

export function handleHeaderScroll() {
    const header = document.querySelector('header.header-landing');
    if (!header) return;
    header.classList.toggle('scrolled', window.scrollY > 50);
}

export function checkAuthState() {
    const guestActions = document.getElementById('auth-guest-actions');
    const userActions = document.getElementById('auth-user-actions');
    const token = localStorage.getItem('token');

    if (token) {
        if (guestActions) guestActions.style.display = 'none';
        if (userActions) userActions.style.display = 'flex';
    } else {
        if (guestActions) guestActions.style.display = 'flex';
        if (userActions) userActions.style.display = 'none';
    }
}

export { initMap, findNearestBranch, filterMapByLocality, InicializarCarrusel };
