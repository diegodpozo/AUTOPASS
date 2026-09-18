// TOUR STEPS DATA: step arrays y helpers ensure* del tour guiado.
// Modulo de datos puro, consumido por tour.js (engine de recorrido).

// Tour for users who have 0 vehicles registered
export const noVehiclesTourSteps = [
    {
        selector: '#section-vehiculos .welcome-card',
        title: '¡Bienvenido a AutoPass!',
        text: 'Para comenzar a realizar reservas en nuestras sucursales, primero necesitamos registrar la patente de tu vehículo.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#vehicle-form-container',
        title: 'Registrá tu Vehículo',
        text: 'Desplegamos el formulario para que ingresés la patente y marca de tu vehículo. Pulsá CONTINUAR para darlo de alta.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
            const container = document.getElementById('vehicle-form-container');
            const trigger = document.getElementById('vehicle-form-trigger');
            if (container) {
                container.style.display = 'block';
                container.classList.add('open');
            }
            if (trigger) {
                trigger.style.display = 'none';
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa de Sucursales',
        text: 'Mientras registrás tu vehículo, podés explorar la ubicación exacta de nuestras sucursales en este mapa interactivo.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#section-puntos .points-main-card',
        title: 'Puntos AutoPass & Beneficios',
        text: 'En cada estadía que realicés acumulás puntos que podés canjear por cupones de descuento o estacionamientos gratis.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-puntos',
        title: '¡Listo para Empezar!',
        text: 'Una vez que registrés tu primer vehículo, el formulario de reservas quedará activo inmediatamente.',
        align: 'top',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    }
];

// Main tour post vehicle creation (used in initial onboarding after user adds their first vehicle)
export const mainTourSteps = [
    { 
        selector: '#reserva-form-container', 
        title: 'Formulario de Reserva', 
        text: '¡Excelente! Ahora que registraste tu vehículo, podés generar tu primera reserva: elegí sucursal y tipo de estadía.', 
        align: 'bottom', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
            const container = document.getElementById('reserva-form-container');
            if (container && !container.classList.contains('open') && window.toggleReservaForm) {
                try { window.toggleReservaForm(); } catch(e){}
            }
        }
    },
    { selector: '#reserva-form-content .res-vehicle', title: 'Seleccioná vehículo', text: 'Tu nuevo vehículo ya aparece seleccionado por defecto.', align: 'right', interactive: true },
    { selector: '.res-sucursal', title: 'Elegí punto', text: 'Seleccioná el punto AutoPass donde querés estacionar.', align: 'left', interactive: true },
    { selector: '.res-type', title: 'Tipo de estadía', text: 'Elegí si reservás por hora, día, semana, quincena o mes. Los campos cambiarán acorde al tipo.', align: 'left', interactive: true },
    { selector: '.reservation-footer-premium .btn-confirm-premium', title: 'Confirmar reserva', text: 'Revisá el total y pulsá "Continuar" para confirmar la reserva.', align: 'top', interactive: true },
    { selector: '#portal-map', title: 'Mapa y ubicación', text: 'En este mapa podés ver la ubicación de las sucursales y elegir una cercana.', align: 'left', interactive: false }
];

// Steps that run specifically inside 'Mis Reservas' after reservation is created
export const reservationsTourSteps = [
    { 
        selector: '#reservation-featured-list, #reservation-list-active, #reservation-list-history', 
        title: 'Mis Reservas', 
        text: 'Acá verás tus reservas recientes y activas. Podés ver el pase digital, editar o cancelar según corresponda.', 
        align: 'top', 
        interactive: true, 
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    { selector: '.reserva-actions-ultra .btn-ultra.btn-ultra-primary, .reserva-card-ultra .btn-ultra.btn-ultra-primary', title: 'Acciones principales', text: 'Aquí podés ver tu Pase Digital QR o abonar la reserva con el saldo de tu billetera.', align: 'left', interactive: true, waitForEnabled: true },
    { selector: '.reserva-actions-ultra .btn-ultra-mp, .reserva-card-ultra .btn-ultra-mp', title: 'Pago con Mercado Pago', text: 'También podés abonar tu reserva o estadía directamente con Mercado Pago (Checkout Pro) sin consumir tu saldo.', align: 'left', interactive: true },
    { selector: '.reserva-actions-ultra .btn-ultra.btn-ultra-secondary, .reserva-card-ultra .btn-ultra.btn-ultra-secondary', title: 'Editar reserva', text: 'Usá este botón para editar la reserva si necesitás cambiar fecha o sucursal.', align: 'left', interactive: true },
    { selector: '.reserva-actions-ultra .btn-ultra.btn-ultra-danger, .reserva-card-ultra .btn-ultra.btn-ultra-danger', title: 'Eliminar / Cancelar', text: 'Si querés cancelar la reserva, usá este botón. Te mostraremos la confirmación y posibles reembolsos.', align: 'left', interactive: true },
    { 
        selector: '#section-puntos .points-main-card', 
        title: 'Tus Puntos', 
        text: 'Acá podés ver tus puntos AutoPass disponibles. ¡Acumulás 10 puntos por cada $1000 abonados en estadías!', 
        align: 'bottom', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    { 
        selector: '#section-puntos #promotions-grid', 
        title: 'Promociones y Canjes', 
        text: 'En esta sección tenés el catálogo de beneficios. Podés canjear tus puntos por cupones de descuento o estadías gratuitas.', 
        align: 'top', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    { 
        selector: '#section-puntos #pts-history-container', 
        title: 'Historial de Puntos', 
        text: 'Revisá los detalles de tus puntos ganados y canjeados en esta lista.', 
        align: 'top', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    { 
        selector: '#section-puntos', 
        title: '¡Felicitaciones!', 
        text: 'Completaste el recorrido por tu portal de cliente de AutoPass. ¡Ya estás listo para empezar a reservar!', 
        align: 'top', 
        interactive: false, 
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    }
];

// Steps that run for users who already have 1 or more vehicles added
export const existingVehiclesTourSteps = [
    {
        selector: '#section-vehiculos .welcome-card',
        title: 'Mis Vehículos',
        text: '¡Aquí tenés registrada tu flota! Podés administrar tus autos, motos o camionetas y elegir tu vehículo favorito.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#vehicle-form-container',
        title: '¿Agregar un Nuevo Vehículo?',
        text: 'Desplegamos el formulario por si querés agregar un nuevo vehículo a tu flota en este momento. Podés cargarlo ahora o pulsar "Continuar" para avanzar con el recorrido.',
        align: 'bottom',
        interactive: true,
        nextText: 'Continuar',
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
            const container = document.getElementById('vehicle-form-container');
            const trigger = document.getElementById('vehicle-form-trigger');
            if (container) {
                container.style.display = 'block';
                container.classList.add('open');
            }
            if (trigger) {
                trigger.style.display = 'none';
            }
        }
    },
    {
        selector: '#reserva-form-container',
        title: 'Reserva de Estacionamiento',
        text: 'En el menú Inicio podés generar reservas en cualquiera de las sucursales del sistema.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
            const container = document.getElementById('reserva-form-container');
            if (container && !container.classList.contains('open') && window.toggleReservaForm) {
                try { window.toggleReservaForm(); } catch(e){}
            }
        }
    },
    {
        selector: '#reserva-form-content .res-vehicle',
        title: 'Selección de Vehículo',
        text: 'Tu vehículo favorito ya estará seleccionado por defecto. Solo indicá la sucursal y el tipo de estadía.',
        align: 'right',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa de Sucursales',
        text: 'Visualizá la ubicación geográfica exacta de nuestras sedes y consultá su disponibilidad en tiempo real.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#reservation-featured-list, #reservation-list-active, #reservation-list-history, #section-reservas',
        title: 'Mis Reservas & Pase QR',
        text: 'Obtené tu Pase Digital QR para escanear en las barreras, editar datos o cancelar tu estadía.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    {
        selector: '#section-puntos .points-main-card',
        title: 'Puntos AutoPass & Beneficios',
        text: 'Sumás 10 puntos por cada $1000 abonados. Canjealos por cupones de descuento o estadías gratuitas.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-puntos',
        title: '¡Recorrido Completado!',
        text: '¡Excelente! Ya conocés todas las secciones principales de tu portal AutoPass.',
        align: 'top',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    }
];

// Manual tour steps for users with 0 vehicles (launched manually from Ayuda y Soporte)
export const noVehiclesHelpTourSteps = [
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Bienvenido al Tour de la App!',
        text: 'Te guiaremos paso a paso por todas las funciones de AutoPass: Alta de vehículo, Reservas, Mapa, Saldo, Puntos, Notificaciones y Soporte.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#quick-add-form-container, #reserva-no-vehicles, #section-inicio',
        title: '1. Registrá tu Primer Vehículo',
        text: 'Como aún no tenés vehículos vinculados, desde este formulario en Inicio podés dar de alta tu primer auto, moto o camioneta ingresando patente y marca.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
            if (window.showQuickAddVehicle) {
                try { window.showQuickAddVehicle(); } catch(e){}
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa Interactivo & Disponibilidad',
        text: 'Ubicá nuestras sucursales en el mapa y fijate si tienen lugar disponible mirando el color de cada sede.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#section-vehiculos .welcome-card, #section-vehiculos',
        title: '2. Sección Mis Vehículos',
        text: 'En esta pestaña podrás administrar toda tu flota registrada, modificar patentes y elegir tu vehículo favorito.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#section-reservas',
        title: '3. Mis Reservas & Pase Digital QR',
        text: 'Consultá tus reservas activas e historial. Cada reserva genera un Pase Digital con Código QR para mostrar en la entrada si la cámara no lee bien tu patente.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    {
        selector: '.balance-badge',
        title: '4. Billetera Virtual & Saldo',
        text: 'Mantené saldo disponible en tu Billetera Virtual AutoPass para agilizar tus ingresos y pagar estadías sin ingresar tarjetas cada vez.',
        align: 'bottom',
        interactive: true
    },
    {
        selector: '#section-puntos .points-main-card, #section-puntos .points-overview-grid',
        title: '5. Puntos AutoPass & Beneficios',
        text: 'Acumulás 10 puntos por cada $1000 abonados. Canjealos en esta sección por cupones de descuento o estadías 100% gratuitas.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-notificaciones',
        title: '6. Centro de Notificaciones',
        text: 'Acá recibirás avisos en tiempo real sobre confirmaciones de pago, recordatorios previos a tu reserva y respuestas de soporte.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="notificaciones"]');
                window.showSection('notificaciones', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda #soporte-section, #section-ayuda .help-ticket-card, #section-ayuda',
        title: '7. Atención & Tickets de Soporte',
        text: 'Si tenés alguna duda o inconveniente en una sucursal, podés enviarnos un Ticket de Soporte directo a la administración o buscar en las FAQ.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Recorrido Completado!',
        text: '¡Excelente! Ya conocés todas las secciones de tu portal AutoPass. Al registrar tu primer vehículo, el formulario de reservas quedará completamente activo.',
        align: 'bottom',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    }
];

// Manual tour steps for users with 1+ vehicles (launched manually from Ayuda y Soporte)
export const existingVehiclesHelpTourSteps = [
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Bienvenido al Tour de la App!',
        text: 'Te guiaremos paso a paso por todas las funciones de AutoPass: Vehículos, Reservas, Pase QR, Saldo, Puntos, Notificaciones y Soporte.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#section-vehiculos .welcome-card, #section-vehiculos',
        title: '1. Mis Vehículos & Flota',
        text: 'Como ya tenés vehículos registrados, acá podés administrar tu flota de Autos, Motos y Camionetas y seleccionar tu vehículo favorito.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#vehicle-form-container, #section-vehiculos',
        title: 'Alta de Nuevos Vehículos',
        text: 'Desplegando este formulario podés agregar nuevos vehículos a tu flota ingresando la patente y marca.',
        align: 'bottom',
        interactive: true,
        nextText: 'Continuar',
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
            const container = document.getElementById('vehicle-form-container');
            const trigger = document.getElementById('vehicle-form-trigger');
            if (container) {
                container.style.display = 'block';
                container.classList.add('open');
            }
            if (trigger) {
                trigger.style.display = 'none';
            }
        }
    },
    {
        selector: '#reserva-form-content, #reserva-form-container, #section-inicio',
        title: '2. Formulario de Reserva',
        text: 'En la sección Inicio podés seleccionar tu vehículo y generar reservas por Hora, Día, Semana, Quincena o Mes cotizando en tiempo real.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa Interactivo & Disponibilidad',
        text: 'Ubicá nuestras sucursales en el mapa y fijate si tienen lugar disponible mirando el color de cada sede.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#section-reservas',
        title: '3. Mis Reservas & Pase Digital QR',
        text: 'Consultá tus reservas activas e historial. Cada reserva te da un Pase Digital con Código QR para mostrar en la entrada si la cámara no reconoce tu patente.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    {
        selector: '.balance-badge',
        title: '4. Billetera Virtual & Saldo',
        text: 'Mantené saldo disponible en tu Billetera Virtual AutoPass para agilizar tus ingresos y pagar estadías sin ingresar tarjetas cada vez.',
        align: 'bottom',
        interactive: true
    },
    {
        selector: '#section-puntos .points-main-card, #section-puntos .points-overview-grid',
        title: '5. Puntos AutoPass & Beneficios',
        text: 'Acumulás 10 puntos por cada $1000 abonados. Canjealos en esta sección por cupones de descuento o estadías 100% gratuitas.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-notificaciones',
        title: '6. Centro de Notificaciones',
        text: 'Acá recibirás avisos en tiempo real sobre confirmaciones de pago, recordatorios previos a tu reserva y respuestas de soporte.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="notificaciones"]');
                window.showSection('notificaciones', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda #soporte-section, #section-ayuda .help-ticket-card, #section-ayuda',
        title: '7. Atención & Tickets de Soporte',
        text: 'Si tenés alguna duda o inconveniente en una sucursal, podés enviarnos un Ticket de Soporte directo a la administración o buscar en las FAQ.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Recorrido Completado!',
        text: '¡Felicitaciones! Ya conocés todas las herramientas del portal AutoPass. Podés volver a realizar este tour cuando lo necesites.',
        align: 'bottom',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    }
];

// --- INTERACTIVE FEATURE TOURS FOR SPECIFIC MODULES ---

export const ensureVehicleFormOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
        window.showSection('vehiculos', navItem);
    }
    const container = document.getElementById('vehicle-form-container');
    const trigger = document.getElementById('vehicle-form-trigger');
    if (container) {
        container.style.display = 'block';
        container.classList.add('open');
    }
    if (trigger) trigger.style.display = 'none';
};

export const addVehicleTourSteps = [
    {
        selector: '#section-vehiculos .welcome-card, #section-vehiculos',
        title: '¡Alta de Vehículo!',
        text: 'En esta sección podés administrar tu flota. Te guiaremos paso a paso para dar de alta tu auto, moto o camioneta en tiempo real.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#vehicle-form-container, #add-vehicle-form, #section-vehiculos',
        title: '1. Formulario de Registro',
        text: 'Desplegamos el formulario para que ingresés los datos de tu vehículo.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form select[name="tipo"], #quick-add-vehicle-form select[name="tipo"], select[name="tipo"]',
        title: '2. Categoría de Vehículo',
        text: 'Elegí la categoría de tu vehículo: Auto, Moto o Camioneta. Así se calcula la tarifa correcta.',
        align: 'right',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form input[name="patente"], #quick-add-vehicle-form input[name="patente"], input[name="patente"]',
        title: '3. Ingresá la Patente',
        text: 'Escribí la patente de tu vehículo. Usá el formato oficial (ej: ABC 123 o AB 123 CD).',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form input[name="marca_modelo"], #quick-add-vehicle-form input[name="marca_modelo"], input[name="marca_modelo"]',
        title: '4. Marca y Modelo',
        text: 'Escribí la marca y modelo para identificarlo en tu lista de flota.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form button[type="submit"], #quick-add-vehicle-form button[type="submit"]',
        title: '5. Confirmá el Alta',
        text: 'Hacé click en "CONTINUAR" para registrar tu vehículo en vivo. Al completar la acción aparecerá en tu flota.',
        align: 'top',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    }
];

export const ensureReservationFormOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
        window.showSection('inicio', navItem);
    }
    const container = document.getElementById('reserva-form-container');
    if (container && !container.classList.contains('open') && window.toggleReservaForm) {
        try { window.toggleReservaForm(); } catch(e){}
    }
};

export const createReservationTourSteps = [
    {
        selector: '#section-inicio .welcome-card, #section-inicio',
        title: '¡Crear una Reserva!',
        text: 'En el menú Inicio podés generar reservas en cualquiera de las sucursales de AutoPass cotizando en tiempo real.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '#reserva-form-container, #section-inicio',
        title: '1. Formulario de Reserva',
        text: 'Acá tenés el formulario interactivo. Elegí tu vehículo, la sucursal y el tipo de estadía.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '#reserva-form-content .res-vehicle, .res-vehicle',
        title: '2. Seleccioná tu Vehículo',
        text: 'Elegí con qué patente de tu flota vas a realizar la reserva.',
        align: 'right',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '.res-sucursal',
        title: '3. Elegí la Sucursal',
        text: 'Seleccioná la sede AutoPass donde querés estacionar.',
        align: 'left',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '.res-type',
        title: '4. Tipo de Estadía',
        text: 'Elegí si reservás por Hora, Día, Semana, Quincena o Mes. Verás cómo la tarifa estimada se actualiza al instante.',
        align: 'left',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '.reservation-footer-premium .btn-confirm-premium, #reserva-form-content button[type="submit"]',
        title: '5. Confirmar Reserva',
        text: 'Revisá la cotización y pulsá "CONTINUAR" para generar tu reserva y obtener tu Pase QR.',
        align: 'top',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    }
];

export const ensureRechargeModalOpen = () => {
    if (window.openRechargeModal) window.openRechargeModal();
};

export const rechargeBalanceTourSteps = [
    {
        selector: '.balance-badge',
        title: '¡Billetera Virtual & Saldo!',
        text: 'Tu saldo te permite ingresar a las sucursales rápido y sin usar tarjetas. Te mostramos cómo cargar saldo.',
        align: 'bottom',
        interactive: true
    },
    {
        selector: '#rechargeModal .modal-content, #rechargeModal',
        title: '1. Modal de Carga de Saldo',
        text: 'Desplegamos el modal de recarga. Podés interactuar con los botones de monto predefinidos o ingresar un importe.',
        align: 'center',
        interactive: true,
        beforeShow: ensureRechargeModalOpen
    },
    {
        selector: '#recharge-amount, #rechargeModal .recharge-preset-btn',
        title: '2. Seleccioná o Ingresá el Monto',
        text: 'Hacé click en un monto sugerido (ej: $5.000) o escribí la cifra que querés cargar.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureRechargeModalOpen
    },
    {
        selector: '#rechargeModal button[type="submit"]',
        title: '3. Confirmá la Carga',
        text: 'Hacé click en "INGRESAR SALDO" y el dinero se acreditará en tu billetera al instante.',
        align: 'top',
        interactive: true,
        beforeShow: ensureRechargeModalOpen
    }
];

export const ensurePointsTabOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
        window.showSection('puntos', navItem);
    }
};

export const redeemPointsTourSteps = [
    {
        selector: '#section-puntos .points-main-card, #section-puntos',
        title: '¡Puntos AutoPass & Beneficios!',
        text: 'Acumulás 10 puntos por cada $1000 abonados. Te mostramos cómo ver tus puntos y canjear premios.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensurePointsTabOpen
    },
    {
        selector: '#points-progress-bar, #section-puntos .points-overview-grid, #section-puntos',
        title: '1. Tus Puntos & Progreso',
        text: 'Acá podés ver tus puntos acumulados y tu avance hacia el próximo beneficio.',
        align: 'bottom',
        interactive: false,
        beforeShow: ensurePointsTabOpen
    },
    {
        selector: '#section-puntos #promotions-grid, #promotions-grid, #section-puntos',
        title: '2. Catálogo de Promociones',
        text: 'Explorá los cupones activos. Podés canjear tus puntos por descuentos o estadías gratuitas.',
        align: 'top',
        interactive: true,
        beforeShow: ensurePointsTabOpen
    },
    {
        selector: '.promo-card .btn-redeem, #promotions-grid, #section-puntos',
        title: '3. Canjear Beneficio',
        text: 'Cuando tengas puntos suficientes, pulsá "CANJEAR" en el beneficio que prefieras.',
        align: 'top',
        interactive: true,
        beforeShow: ensurePointsTabOpen
    }
];

export const ensureReservationsTabOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
        window.showSection('reservas', navItem);
    }
};

export const ensureDigitalPassModalOpen = async () => {
    ensureReservationsTabOpen();
    const modal = document.getElementById('modal-pase-digital');
    if (modal) {
        // Garantizar visibilidad inmediata en 0ms para evitar parpadeo o cierre/reapertura
        modal.style.display = 'flex';

        // 1. Buscar botón que invoque directamente showDigitalPass
        const passBtn = document.querySelector('button[onclick*="showDigitalPass"]');
        if (passBtn) {
            const match = passBtn.getAttribute('onclick')?.match(/\d+/);
            if (match && typeof window.showDigitalPass === 'function') {
                try { await window.showDigitalPass(parseInt(match[0], 10)); return; } catch(e){}
            }
        }

        // 2. Buscar si hay reservas en memoria
        if (window.userReservations && Array.isArray(window.userReservations) && window.userReservations.length > 0) {
            const firstRes = window.userReservations[0];
            if (typeof window.showDigitalPass === 'function') {
                try { await window.showDigitalPass(firstRes.id); return; } catch(e){}
            }
        }

        // 3. Fallback directo con QR listo
        const idDisp = document.getElementById('ticket-id-display');
        if (idDisp) idDisp.innerText = '#000001';
        const patenteDisp = document.getElementById('ticket-patente');
        if (patenteDisp) patenteDisp.innerText = 'AA 123 BB';
        const venceDisp = document.getElementById('ticket-vence');
        if (venceDisp) venceDisp.innerText = 'Hoy, 23:59hs';
        const sucursalDisp = document.getElementById('ticket-sucursal');
        if (sucursalDisp) sucursalDisp.innerText = 'AutoPass Central';
        const dirDisp = document.getElementById('ticket-direccion');
        if (dirDisp) dirDisp.innerText = 'Av. Corrientes 1234';

        const qrContainer = document.getElementById('ticket-qr');
        if (qrContainer && window.QRCode && qrContainer.children.length === 0) {
            qrContainer.innerHTML = '';
            try { new QRCode(qrContainer, { text: 'AUTOPASS|DEMO|PLATE:AA123BB', width: 180, height: 180 }); } catch(e){}
        }
    }
};

export const qrPassTourSteps = [
    {
        selector: 'button[onclick*="showDigitalPass"], #section-reservas .btn-ultra-primary, #section-reservas .reserva-card-ultra, #section-reservas',
        title: 'Pase Digital QR',
        text: 'Hacé click en "MI PASE DIGITAL" en tu reserva para desplegar el ticket de acceso.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            ensureReservationsTabOpen();
        }
    },
    {
        selector: '#modal-pase-digital .ticket-qr-section, #ticket-qr, #modal-pase-digital',
        title: '1. Código QR para Tótems',
        text: 'Este recuadro contiene tu código QR. Mostralo en la entrada si la cámara no reconoce tu patente.',
        align: 'right',
        interactive: true,
        beforeShow: ensureDigitalPassModalOpen
    },
    {
        selector: '#modal-pase-digital .ticket-info-grid, #modal-pase-digital',
        title: '2. Datos de la Estadía',
        text: 'Acá verificás los datos clave de tu reserva: Patente registrada, fecha de vencimiento, sucursal y dirección exacta.',
        align: 'left',
        interactive: true,
        beforeShow: ensureDigitalPassModalOpen
    },
    {
        selector: '#modal-pase-digital .btn-download, #modal-pase-digital .ticket-actions, #modal-pase-digital',
        title: '3. Compartir / Descargar Pase',
        text: 'Pulsá "COMPARTIR PASE" para generar una imagen PNG del ticket. Podés guardarla en tu celular o enviársela por WhatsApp a quien vaya a usar el vehículo.',
        align: 'top',
        interactive: true,
        beforeShow: ensureDigitalPassModalOpen
    }
];

// QUICK-ADD TOUR: steps to guide through add-vehicle form
export const quickAddSteps = [
    { selector: '#quick-add-form-container .select-wrapper-premium select[name="tipo"]', title: 'Tipo de vehículo', text: 'Seleccioná si es Auto, Moto o Camioneta. Así se calcula la tarifa correcta.', align: 'right', interactive: true },
    { selector: '#quick-add-vehicle-form input[name="patente"]', title: 'Patente', text: 'Ingresá la patente de tu vehículo. Usá el formato correcto (ej: ABC 123).', align: 'bottom', interactive: true },
    { selector: '#quick-add-vehicle-form input[name="marca_modelo"]', title: 'Marca / Modelo', text: 'Escribí la marca y modelo para identificar tu vehículo fácilmente.', align: 'bottom', interactive: true },
    { selector: '#quick-add-vehicle-form button[type="submit"]', title: 'Continuar', text: 'Cuando completes los datos, pulsá CONTINUAR para registrar el vehículo.', align: 'top', interactive: true }
];



