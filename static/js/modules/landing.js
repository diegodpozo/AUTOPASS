/**
 * LANDING MODULE
 * Lógica para el carrusel, mapa y navegación de la landing page.
 */

let mapInstance = null;
let IndiceCarruselActual = 0;
let IntervaloCarrusel = null;

export function initMap() {
    const mapEl = document.getElementById('map');
    if (!mapEl || mapInstance || !window.L) return;

    const hqCoords = [-34.5888, -58.3900];
    mapInstance = L.map('map').setView(hqCoords, 14);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(mapInstance);

    const goldIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="background-color: #C5A059; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #C5A059;"></div>`,
        iconSize: [15, 15],
        iconAnchor: [7, 7]
    });

    L.marker(hqCoords, { icon: goldIcon }).addTo(mapInstance)
        .bindPopup('<b>AUTOPASS HQ</b><br>Av. del Libertador 1200, CABA').openPopup();

    // Cargar sucursales desde la API
    fetch('/v1/parking/branches')
        .then(res => res.json())
        .then(branches => {
            branches.forEach(p => {
                if (!p.latitude || !p.longitude) return;
                
                const branchIcon = L.divIcon({
                    className: 'branch-icon',
                    html: `<div style="background-color: #C5A059; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px #C5A059;"></div>`,
                    iconSize: [12, 12],
                    iconAnchor: [6, 6]
                });
                
                const popupContent = `
                    <div style="text-align: center;">
                        <img src="${p.logo_url || '/static/images/logo.png'}" style="width: 40px; height: 40px; border-radius: 50%; margin-bottom: 5px;">
                        <br><b>${p.nombre}</b><br>${p.direccion}<br>
                        <small>${p.is_24h ? 'Abierto 24hs' : p.horario}</small>
                    </div>
                `;
                
                L.marker([p.latitude, p.longitude], { icon: branchIcon })
                    .addTo(mapInstance)
                    .bindPopup(popupContent);
            });
        })
        .catch(err => console.error('Error al cargar sucursales para el mapa:', err));
}

const DatosCarrusel = [
    { imagen: '/static/images/INICIO/trafico1.webp', leyenda: '¿Te agota tanto embotellamiento en Buenos Aires?' },
    { imagen: '/static/images/INICIO/trafico2.webp', leyenda: '¿Sentís que el tráfico continuo te consume la energía?' },
    { imagen: '/static/images/INICIO/trafico3.webp', leyenda: '¿Es frustrante perder horas en la autopista?' },
    { imagen: '/static/images/INICIO/estacionamiento1.webp', leyenda: '¿Te fastidia buscar lugar en la calle siempre?' },
    { imagen: '/static/images/INICIO/estacionamiento2.webp', leyenda: '¿Te molesta llegar y que no haya lugar?' },
    { imagen: '/static/images/INICIO/estacionamiento3.webp', leyenda: 'AUTOPASS elimina el estrés del estacionamiento en la ciudad.' },
    { imagen: '/static/images/INICIO/estacionamiento4.webp', leyenda: 'Reserva tu cochera online en segundos con AUTOPASS.' }
];

export function InicializarCarrusel() {
    const Contenedor = document.getElementById('contenedorCarrusel');
    if (!Contenedor || Contenedor.children.length > 0) return;

    DatosCarrusel.forEach((dato, i) => {
        const Item = document.createElement('div');
        Item.className = `item-carrusel ${i === 0 ? 'activo' : ''}`;
        Item.style.backgroundImage = `url('${dato.imagen}')`;
        Item.innerHTML = `<div class="leyenda-carrusel">${dato.leyenda}</div>`;
        Contenedor.appendChild(Item);
    });

    IniciarTemporizadorCarrusel();
}

function IniciarTemporizadorCarrusel() {
    if (IntervaloCarrusel) clearInterval(IntervaloCarrusel);
    IntervaloCarrusel = setInterval(() => RotarCarrusel(1), 5000);
}

function RotarCarrusel(Direccion) {
    const Items = document.querySelectorAll('.item-carrusel');
    if (Items.length === 0) return;

    Items[IndiceCarruselActual].classList.remove('activo');
    IndiceCarruselActual = (IndiceCarruselActual + Direccion + Items.length) % Items.length;
    Items[IndiceCarruselActual].classList.add('activo');
}

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
