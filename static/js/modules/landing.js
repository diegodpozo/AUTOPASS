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

    // Agregar Botón de Mi Ubicación en el mapa (Top-Right para evitar conflicto con Zoom)
    const locationBtn = L.control({ position: 'topright' });
    locationBtn.onAdd = function() {
        const div = L.DomUtil.create('div', 'leaflet-control-geolocation');
        div.innerHTML = `
            <button title="Buscar sucursal más cercana" 
                    style="background: #111; border: 1px solid #C5A059; color: #C5A059; 
                           width: 38px; height: 38px; cursor: pointer; display: flex; 
                           align-items: center; justify-content: center; font-size: 1.1rem; 
                           border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.8);
                           transition: all 0.3s ease; outline: none;">
                <i class="fas fa-location-crosshairs"></i>
            </button>`;
        
        div.onmouseover = () => { 
            const btn = div.querySelector('button');
            if (btn) { btn.style.background = '#C5A059'; btn.style.color = '#000'; }
        };
        div.onmouseout = () => { 
            const btn = div.querySelector('button');
            if (btn) { btn.style.background = '#111'; btn.style.color = '#C5A059'; }
        };
        
        div.onclick = function(e) {
            e.stopPropagation();
            findNearestBranch();
        };
        return div;
    };
    locationBtn.addTo(mapInstance);

    // Cargar sucursales desde la API
    fetch('/v1/parking/branches')
        .then(res => res.json())
        .then(branches => {
            window.allBranchesMap = branches; // Guardar para geolocalización
            branches.forEach(p => {
                if (!p.latitude || !p.longitude) return;
                
                // Determinar color y mensaje por disponibilidad
                const pct = (p.ocupacion_actual / p.capacidad_total) * 100;
                let statusColor = '#C5A059'; // Disponible (Dorado)
                let statusText = 'Disponible';
                let statusDesc = '¡Hay muchas plazas disponibles!';
                
                if (pct >= 100) {
                    statusColor = '#ff4444'; // Lleno (Rojo)
                    statusText = 'Lleno';
                    statusDesc = 'No hay lugares disponibles en este momento.';
                } else if (pct >= 85) {
                    statusColor = '#ffbb33'; // Casi lleno (Naranja)
                    statusText = 'Últimos lugares';
                    statusDesc = 'Quedan pocas plazas. ¡Reservá pronto!';
                } else if (pct > 50) {
                    statusDesc = 'Disponibilidad moderada.';
                }

                const branchIcon = L.divIcon({
                    className: 'branch-icon',
                    html: `<div id="marker-branch-${p.id}" style="background-color: ${statusColor}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${statusColor}; transition: all 0.3s ease;"></div>`,
                    iconSize: [14, 14],
                    iconAnchor: [7, 7]
                });
                
                const popupContent = `
                    <div style="text-align: center; min-width: 180px; padding: 5px;">
                        <img src="${p.logo_url || '/static/images/logo.png'}" style="width: 50px; height: 50px; border-radius: 50%; margin-bottom: 8px; border: 2px solid ${statusColor};">
                        <br><b style="font-size: 1.1rem; color: #fff;">${p.nombre}</b>
                        <br><span style="color: #aaa; font-size: 0.8rem;">${p.direccion}</span>
                        <div style="margin: 12px 0; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);">
                            <b style="color: ${statusColor}; font-size: 0.9rem; display: block; margin-bottom: 4px;">${statusText.toUpperCase()}</b>
                            <span style="color: #eee; font-size: 0.8rem; display: block; margin-bottom: 5px;">${statusDesc}</span>
                            <div style="height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden; margin: 8px 0;">
                                <div style="width: ${pct}%; height: 100%; background: ${statusColor};"></div>
                            </div>
                            <small style="color: #888;">${p.capacidad_total - p.ocupacion_actual} de ${p.capacidad_total} plazas libres</small>
                        </div>
                        <a href="javascript:void(0)" onclick="irAReserva('${p.nombre}')" class="btn btn-primary" style="padding: 8px 15px; font-size: 0.75rem; width: 100%; display: block; margin-top: 5px; border-radius: 8px;">RESERVÁ AQUÍ</a>
                    </div>
                `;
                
                const marker = L.marker([p.latitude, p.longitude], { icon: branchIcon })
                    .addTo(mapInstance)
                    .bindPopup(popupContent);
                
                // Guardar referencia al marcador para poder abrirlo programáticamente
                p.marker = marker;
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

// --- GEOLOCALIZACIÓN Y DISTANCIA ---

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radio de la Tierra en km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

export function findNearestBranch() {
    if (!navigator.geolocation) {
        return alert('Tu navegador no soporta geolocalización.');
    }

    // Usar showToast si está disponible
    const toast = (msg) => {
        if (window.showToast) window.showToast(msg);
        else console.log(msg);
    };

    toast('Buscando tu ubicación...');

    navigator.geolocation.getCurrentPosition((pos) => {
        const myLat = pos.coords.latitude;
        const myLng = pos.coords.longitude;

        if (!window.allBranchesMap || window.allBranchesMap.length === 0) return;

        let nearest = null;
        let minDistance = Infinity;

        window.allBranchesMap.forEach(p => {
            if (!p.latitude || !p.longitude) return;
            const dist = calculateDistance(myLat, myLng, p.latitude, p.longitude);
            if (dist < minDistance) {
                minDistance = dist;
                nearest = p;
            }
        });

        if (nearest && mapInstance) {
            mapInstance.setView([nearest.latitude, nearest.longitude], 15);
            
            // Efecto visual: Resaltar marcador
            const markerDiv = document.getElementById(`marker-branch-${nearest.id}`);
            if (markerDiv) {
                markerDiv.style.width = '24px';
                markerDiv.style.height = '24px';
                markerDiv.style.boxShadow = '0 0 20px 5px #fff';
                setTimeout(() => {
                    markerDiv.style.width = '14px';
                    markerDiv.style.height = '14px';
                    markerDiv.style.boxShadow = '';
                }, 3000);
            }

            nearest.marker.openPopup();
            toast(`Sucursal más cercana: ${nearest.nombre} (a ${(minDistance).toFixed(1)} km)`);
        }
    }, (err) => {
        console.warn('Error de geolocalización:', err);
        toast('No se pudo obtener tu ubicación.');
    });
}
