import * as land from './modules/landing.js';

/**
 * BRIDGE: landing.js
 */

window.irAReserva = function(branchName = null) {
    console.log(`[irAReserva] Iniciando para: ${branchName}`);
    if (!localStorage.getItem('token')) {
        if (window.openModal) window.openModal('loginModal');
        return;
    }

    // Si YA estamos en el portal, no recargar, actuar directamente sobre la UI
    if (window.location.pathname.includes('/perfil') && window.fillReservationForm) {
        window.fillReservationForm(branchName);
        return;
    }

    // Si estamos fuera, redirigir normalmente
    let url = '/perfil';
    if (branchName) {
        url += `?reserva_sucursal=${encodeURIComponent(branchName)}`;
    }
    window.location.href = url;
};

/**
 * Función de utilidad para llenar el formulario de reserva sin recargar la página.
 * Se expone globalmente para ser usada por el mapa integrado.
 */
window.fillReservationForm = async function(branchName) {
    console.log(`[fillReservationForm] Intentando auto-llenado local para: ${branchName}`);
    
    // 1. Asegurar sección de inicio
    if (window.showSection) {
        window.showSection('inicio', document.querySelector('.nav-item[onclick*="inicio"]'));
    }

    const container = document.getElementById('reserva-form-container');
    if (!container) {
        console.error("[fillReservationForm] No se encontró el contenedor del formulario.");
        return;
    }

    // 2. Abrir formulario si está cerrado
    if (!container.classList.contains('open') && window.toggleReservaForm) {
        console.log("[fillReservationForm] Abriendo formulario...");
        await window.toggleReservaForm();
    }

    // 3. Secuencia de llenado con reintentos (por carga asíncrona de sucursales)
    let attempts = 0;
    const maxAttempts = 15;
    
    const fillFields = () => {
        const sucursalSelect = document.querySelector('.res-sucursal');
        const vehicleSelect = document.querySelector('.res-vehicle');
        
        if (sucursalSelect && sucursalSelect.options.length > 1 && sucursalSelect.options[0].value === "") {
            console.log(`[fillReservationForm] Llenando campos para ${branchName}`);
            const targetOption = Array.from(sucursalSelect.options).find(opt => opt.value === branchName);
            
            if (targetOption) {
                sucursalSelect.value = branchName;
                sucursalSelect.dispatchEvent(new Event('change'));
            }

            if (vehicleSelect && vehicleSelect.options.length === 2) {
                vehicleSelect.selectedIndex = 1;
            }

            container.scrollIntoView({ behavior: 'smooth' });
            if (window.showToast) window.showToast(`Preparado para reservar en ${branchName}`);
            return true;
        }
        
        attempts++;
        if (attempts < maxAttempts) {
            setTimeout(fillFields, 300);
        } else {
            console.warn("[fillReservationForm] Tiempo de espera agotado.");
        }
        return false;
    };

    fillFields();
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
