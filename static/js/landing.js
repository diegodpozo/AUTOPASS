import * as land from './modules/landing.js';

/**
 * BRIDGE: landing.js
 */

window.irAReserva = function(branchName = null) {
    if (localStorage.getItem('token')) {
        let url = '/perfil';
        if (branchName) {
            url += `?reserva_sucursal=${encodeURIComponent(branchName)}`;
        }
        window.location.href = url;
    } else {
        if (window.openModal) window.openModal('loginModal');
    }
};

window.toggleMobileMenu = function() {
    const nav = document.getElementById('nav-menu');
    const btn = document.querySelector('.mobile-menu-btn');
    if (!nav) return;
    const isActive = nav.classList.toggle('active');
    if (btn) btn.classList.toggle('hidden', isActive);
};

document.addEventListener('DOMContentLoaded', () => {
    land.checkAuthState();
    land.handleHeaderScroll();
    
    window.addEventListener('scroll', land.handleHeaderScroll);
    
    if (document.getElementById('map')) land.initMap();
    if (document.getElementById('contenedorCarrusel')) land.InicializarCarrusel();

    // Menu móvil events
    const nav = document.getElementById('nav-menu');
    const btn = document.querySelector('.mobile-menu-btn');
    if (nav) {
        nav.querySelectorAll('a, button.btn-nav').forEach(link => {
            link.addEventListener('click', () => {
                nav.classList.remove('active');
                if (btn) btn.classList.remove('hidden');
            });
        });
    }
});

document.addEventListener('click', (e) => {
    const nav = document.getElementById('nav-menu');
    const btn = document.querySelector('.mobile-menu-btn');
    if (nav && nav.classList.contains('active')) {
        const isOverlayClick = e.clientX > 260;
        const isOutsideClick = !nav.contains(e.target);
        const isNotButton = btn && !btn.contains(e.target);
        if ((isOverlayClick || isOutsideClick) && isNotButton) {
            nav.classList.remove('active');
            if (btn) btn.classList.remove('hidden');
        }
    }
});
