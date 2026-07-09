import * as land from './modules/landing.js?v=9.3.0';

/**
 * PUENTE: LANDING.JS
 */

window.irAReserva = function(branchName = null) {
    console.log(`[irAReserva] Iniciando para: ${branchName}`);
    if (!localStorage.getItem('token')) {
        if (window.openModal) window.openModal('loginModal');
        return;
    }

    //SI YA ESTAMOS EN EL PORTAL, NO RECARGAR, ACTUAR DIRECTAMENTE SOBRE LA UI
    if (window.location.pathname.includes('/perfil') && window.fillReservationForm) {
        window.fillReservationForm(branchName);
        return;
    }

    // SI ESTAMOS FUERA, REDIRIGIR NORMALMENTE
    let url = '/perfil';
    if (branchName) {
        url += `?reserva_sucursal=${encodeURIComponent(branchName)}`;
    }
    window.location.href = url;
};

/**
 * FUNCION DE UTILIDAD PARA LLENAR EL FORMULARIO DE RESERVA SIN RECARGAR LA PAGINA.
 * SE EXPONE GLOBALMENTE PARA SER USADA POR EL MAPA INTEGRADO.
 */
window.fillReservationForm = async function(branchName) {
    console.log(`[fillReservationForm] Intentando auto-llenado local para: ${branchName}`);

    // 0. CERRAR MAPA FULLSCREEN SI ESTA ABIERTO
    if (window.closeFullMap) {
        window.closeFullMap();
    }

    // 1. ASEGURAR SECCION DE INICIO
    if (window.showSection) {
        window.showSection('inicio', document.querySelector('.nav-item[onclick*="inicio"]'));
    }

    const container = document.getElementById('reserva-form-container');
    if (!container) {
        console.error("[fillReservationForm] No se encontró el contenedor del formulario.");
        return;
    }

    // 2. ABRIR FORMULARIO SI ESTA CERRADO
    if (!container.classList.contains('open') && window.toggleReservaForm) {
        console.log("[fillReservationForm] Abriendo formulario...");
        await window.toggleReservaForm();
    }

    // 3. SECUENCIA DE LLENADO CON REINTENTOS (POR CARGA ASINCRONA DE SUCURSALES)
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
            if (window.showToast) window.showToast(`Preparado para reservar en ${branchName}`, 'info');
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
    
    if (document.getElementById('map')) land.initMap('map', null, true);
    if (document.getElementById('contenedorCarrusel')) land.InicializarCarrusel();

    // MENU MOVIL EVENTS
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
