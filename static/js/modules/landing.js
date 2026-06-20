/**
 * LANDING MODULO
 * LOGICA PARA EL CARRUSEL, MAPA Y NAVEGACION DE LA LANDING PAGE.
 */

let mapInstance = null;
let IndiceCarruselActual = 0;
let IntervaloCarrusel = null;
let IndiceFraseActual = 0;
let IntervaloFrase = null;

function formatAddress(addr) {
    if (!addr) return '';
    // SI NO TIENE COMA, INTENTAMOS PONER UNA DESPUES DEL NUMERO DE LA CALLE
    if (!addr.includes(',')) {
        return addr.replace(/(\d+)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)$/, '$1, $2');
    }
    return addr;
}

export function initMap(containerId = 'map') {
    const mapEl = document.getElementById(containerId);
    if (!mapEl || !window.L) return;

    const hqCoords = [-34.5888, -58.3900];
    const newMapInstance = L.map(containerId).setView(hqCoords, 14);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(newMapInstance);

    // SI ES EL MAPA PRINCIPAL DE LA LANDING, GUARDAMOS LA INSTANCIA GLOBAL PARA GEOLOCALIZACION
    if (containerId === 'map') mapInstance = newMapInstance;

    // AGREGAR BOTON DE MI UBICACION EN EL MAPA (TOP-RIGHT PARA EVITAR CONFLICTO CON ZOOM)
    const locationBtn = L.control({ position: 'topright' });
    locationBtn.onAdd = function() {
        const div = L.DomUtil.create('div', 'leaflet-control-geolocation');
        div.innerHTML = `
            <button title="Buscar sucursal más cercana" 
                    style="background: #000; border: 1.5px solid #C5A059; color: #C5A059; 
                           width: 34px; height: 34px; cursor: pointer; display: flex; 
                           align-items: center; justify-content: center; 
                           border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.8);
                           transition: all 0.3s ease; outline: none; font-size: 0.9rem;">
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
            findNearestBranch(newMapInstance);
        };
        return div;
    };
    locationBtn.addTo(newMapInstance);

    //CARGAR SUCURSALES DESDE LA API
    fetch('/v1/parking/branches')
        .then(res => res.json())
        .then(branches => {
            window.allBranchesMap = branches; // GUARDAR PARA GEOLOCALIZACION
            branches.forEach(p => {
                if (!p.latitude || !p.longitude) return;
                
                // DETERMINAR COLOR Y MENSAJE POR DISPONIBILIDAD
                const pct = (p.ocupacion_actual / p.capacidad_total) * 100;
                let statusColor = '#C5A059'; // DISPONIBLE (DORADO)
                let statusText = 'Alta disponibilidad';
                let statusDesc = 'Hay lugares disponibles para vos.';
                
                if (pct >= 100) {
                    statusColor = '#ff4444'; // LLENO (ROJO)
                    statusText = 'Sucursal Completa';
                    statusDesc = 'No hay disponibilidad en este momento.';
                } else if (pct >= 85) {
                    statusColor = '#ffbb33'; // CASI LLENO (NARANJA)
                    statusText = 'Lugares limitados';
                    statusDesc = 'Quedan pocas plazas. ¡Reservá ahora!';
                } else if (pct > 50) {
                    statusText = 'Disponibilidad moderada';
                    statusDesc = 'Disponibilidad moderada.';
                }

                const branchIcon = L.divIcon({
                    className: 'branch-icon',
                    html: `<div id="marker-${containerId}-${p.id}" style="background-color: ${statusColor}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${statusColor}; transition: all 0.3s ease;"></div>`,
                    iconSize: [14, 14],
                    iconAnchor: [7, 7]
                });
                
                const formattedAddr = formatAddress(p.direccion);

                const popupContent = `
                    <div style="text-align: center; min-width: 200px; padding: 10px; background: #0a0a0a; border-radius: 15px;">
                        <img src="${p.logo_url || '/static/images/logo.png'}" style="width: 55px; height: 55px; border-radius: 50%; margin-bottom: 10px; border: 2px solid #C5A059; padding: 3px; background: #000;">
                        <br><b style="font-size: 1.15rem; color: #fff; font-family: 'Montserrat'; letter-spacing: 0.5px;">${p.nombre}</b>
                        <br><span style="color: #888; font-size: 0.8rem; display: block; margin-top: 2px; text-transform: capitalize;">${formattedAddr}</span>
                        
                        <div style="margin: 15px 0; padding: 12px; background: rgba(197, 160, 89, 0.03); border-radius: 12px; border: 1px solid rgba(197, 160, 89, 0.15);">
                            <b style="color: ${statusColor}; font-size: 0.85rem; display: block; margin-bottom: 6px; letter-spacing: 1px;">${statusText.toUpperCase()}</b>
                            <span style="color: #ddd; font-size: 0.75rem; display: block; margin-bottom: 8px; line-height: 1.4;">${statusDesc}</span>
                            
                            <div style="height: 5px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; margin: 10px 0;">
                                <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, ${statusColor} 0%, #fff 200%);"></div>
                            </div>
                        </div>
                        
                        <a href="javascript:void(0)" onclick="irAReserva('${p.nombre}')" 
                           style="background: #C5A059; color: #000; padding: 10px 20px; font-size: 0.75rem; 
                                  font-weight: 900; text-transform: uppercase; letter-spacing: 1px;
                                  width: 100%; display: block; margin-top: 5px; border-radius: 10px;
                                  text-decoration: none; transition: 0.3s; box-shadow: 0 4px 15px rgba(197, 160, 89, 0.2);">
                           RESERVÁ AQUÍ
                        </a>
                    </div>
                `;
                
                const marker = L.marker([p.latitude, p.longitude], { icon: branchIcon })
                    .addTo(newMapInstance)
                    .bindPopup(popupContent);
                
                // ACTUALIZAR OVERLAY DINAMICO AL ABRIR/CERRAR SUCURSAL
                marker.on('popupopen', () => {
                    const overlay = document.querySelector('.map-overlay');
                    if (overlay) {
                        overlay.querySelector('h4').innerHTML = `<i class="fas fa-building"></i> ${p.nombre}`;
                        overlay.querySelector('p').innerText = formattedAddr;
                        overlay.classList.add('active');
                    }
                });

                marker.on('popupclose', () => {
                    const overlay = document.querySelector('.map-overlay');
                    if (overlay) overlay.classList.remove('active');
                });

                // GUARDAR REFERENCIA AL MARCADOR (ESPECIFICO POR CONTAINERID)
                if (!p.markers) p.markers = {};
                p.markers[containerId] = marker;
            });

            // LOGICA PARA LOCALIZACION AUTOMATICA (VIA URL PARAM) - SOLO EN EL MAPA PRINCIPAL
            if (containerId === 'map') {
                const urlParams = new URLSearchParams(window.location.search);
                const branchToFind = urlParams.get('branch');
                if (branchToFind) {
                    const found = branches.find(b => b.nombre.toLowerCase() === branchToFind.toLowerCase());
                    if (found && found.markers && found.markers[containerId]) {
                        newMapInstance.setView([found.latitude, found.longitude], 16);
                        setTimeout(() => {
                            found.markers[containerId].openPopup();
                        }, 500);
                    }
                }
            }
        })
        .catch(err => console.error('Error al cargar sucursales para el mapa:', err));
}

const DatosCarrusel = [
    { imagen: '/static/images/inicio/trafico1.webp', leyenda: '¿Te agota tanto embotellamiento en Buenos Aires?' },
    { imagen: '/static/images/inicio/trafico2.webp', leyenda: '¿Sentís que el tráfico continuo te consume la energía?' },
    { imagen: '/static/images/inicio/trafico3.webp', leyenda: '¿Es frustrante perder horas en la autopista?' },
    { imagen: '/static/images/inicio/estacionamiento1.webp', leyenda: '¿Te fastidia buscar lugar en la calle siempre?' },
    { imagen: '/static/images/inicio/estacionamiento2.webp', leyenda: '¿Te molesta llegar y que no haya lugar?' },
    { imagen: '/static/images/inicio/estacionamiento3.webp', leyenda: 'AUTOPASS elimina el estrés del estacionamiento en la ciudad.' },
    { imagen: '/static/images/inicio/estacionamiento4.webp', leyenda: 'Reserva tu cochera online en segundos con AUTOPASS.' }
];

export function InicializarCarrusel() {
    const Contenedor = document.getElementById('contenedorCarrusel');
    if (!Contenedor || Contenedor.children.length > 0) return;

    DatosCarrusel.forEach((dato, i) => {
        const Item = document.createElement('div');
        Item.className = `item-carrusel ${i === 0 ? 'activo' : ''}`;
        Item.style.backgroundImage = `url('${dato.imagen}')`;
        //REMOVED INNERHTML CON LEGEND
        Contenedor.appendChild(Item);
    });

    IniciarTemporizadores();
}

function RotarCarrusel(Direccion) {
    const Items = document.querySelectorAll('.item-carrusel');
    if (Items.length === 0) return;

    Items[IndiceCarruselActual].classList.remove('activo');
    IndiceCarruselActual = (IndiceCarruselActual + Direccion + Items.length) % Items.length;
    Items[IndiceCarruselActual].classList.add('activo');
    
    // SINCRONIZAR FRASE CON CARRUSEL
    IndiceFraseActual = IndiceCarruselActual;
    const contenedor = document.getElementById('frase-animada');
    if (contenedor) {
        contenedor.innerText = DatosCarrusel[IndiceFraseActual].leyenda;
    }
}

function IniciarTemporizadores() {
    if (IntervaloCarrusel) clearInterval(IntervaloCarrusel);
    
    IntervaloCarrusel = setInterval(() => RotarCarrusel(1), 5000);
    
    // INICIALIZAR PRIMERA FRASE
    const contenedor = document.getElementById('frase-animada');
    if (contenedor) contenedor.innerText = DatosCarrusel[0].leyenda;
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

// --- GEOLOCALIZACION Y DISTANCIA ---

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // RADIO DE LA TIERRA EN KM
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

export function findNearestBranch(targetMap = null) {
    const activeMap = targetMap || mapInstance;
    if (!navigator.geolocation) {
        return alert('Tu navegador no soporta geolocalización.');
    }

    // USAR SHOWTOAST SI ESTA DISPONIBLE
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

        if (nearest && activeMap) {
            activeMap.setView([nearest.latitude, nearest.longitude], 15);
            
            // EFECTO VISUAL: RESALTAR MARCADOR (INTENTAR ENCONTRAR EL DIV POR ID SI EXISTE)
            // NOTA: EN MULTI-MAPA EL ID PODRIA REPETIRSE SI NO SE MANEJA BIEN, 
            // PERO LEAFLET MANEJA SUS PROPIOS ESTADOS.
            
            nearest.markers && Object.values(nearest.markers).forEach(m => {
                if (m._map === activeMap) m.openPopup();
            });

            toast(`Sucursal más cercana: ${nearest.nombre} (a ${(minDistance).toFixed(1)} km)`);
        }
    }, (err) => {
        console.warn('Error de geolocalización:', err);
        toast('No se pudo obtener tu ubicación.');
    });
}
