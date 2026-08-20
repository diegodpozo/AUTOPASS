import { ESTADIOS_FIJOS, POI_CACHE_KEY, POI_CACHE_TTL } from './landing-data.js';

let mapInstance = null;

function formatAddress(addr) {
    if (!addr) return '';
    // SI NO TIENE COMA, INTENTAMOS PONER UNA DESPUES DEL NUMERO DE LA CALLE
    if (!addr.includes(',')) {
        return addr.replace(/(\d+)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)$/, '$1, $2');
    }
    return addr;
}

function formatPoiAddress(t) {
    if (!t) return '';
    const street = t['addr:street'] || t['street'] || '';
    const number = t['addr:housenumber'] || t['housenumber'] || '';
    const suburb = t['addr:suburb'] || t['addr:district'] || t['addr:city'] || t['city'] || '';
    
    let parts = [];
    if (street) {
        parts.push(`${street}${number ? ' ' + number : ''}`);
    }
    if (suburb && !street.toLowerCase().includes(suburb.toLowerCase())) {
        parts.push(suburb);
    }
    
    if (parts.length > 0) return parts.join(', ');
    return t['address'] || t['addr:full'] || '';
}

function getVehicleAvailability(ocupacion, capacidad) {
    const totalCap = parseInt(capacidad) || 0;
    const totalOcc = parseInt(ocupacion) || 0;
    const disp = Math.max(0, totalCap - totalOcc);
    const pctFree = totalCap > 0 ? (disp / totalCap) * 100 : 0;

    let color = '#22c55e'; // Verde = Alta (>40% disponible)
    let label = 'Alta';

    if (totalCap === 0 || disp === 0) {
        color = '#ef4444'; // Rojo = Agotado
        label = 'Agotado';
    } else if (pctFree <= 15) {
        color = '#f97316'; // Naranja = Baja (<=15% disponible)
        label = 'Baja';
    } else if (pctFree <= 40) {
        color = '#eab308'; // Amarillo = Media (15%-40% disponible)
        label = 'Media';
    }

    return { disp, totalCap, color, label, pctFree };
}

window.getDirectionsTo = function(branchLat, branchLng, mode) {
    const googleUrl = (lat, lng) => `https://www.google.com/maps/dir/${lat},${lng}/${branchLat},${branchLng}`;
    const wazeUrl = (lat, lng) => `https://www.waze.com/ul?ll=${branchLat},${branchLng}&navigate=yes&to=${branchLat},${branchLng}&from=${lat},${lng}`;
    const openFallback = () => {
        if (mode === 'waze') window.open(`https://www.waze.com/ul?ll=${branchLat},${branchLng}&navigate=yes`, '_blank');
        else window.open(`https://www.google.com/maps/dir//${branchLat},${branchLng}`, '_blank');
    };
    if (!navigator.geolocation) return openFallback();
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const url = mode === 'waze'
                ? wazeUrl(pos.coords.latitude, pos.coords.longitude)
                : googleUrl(pos.coords.latitude, pos.coords.longitude);
            window.open(url, '_blank');
        },
        openFallback,
        { timeout: 5000, enableHighAccuracy: false }
    );
};

function getPoiCache() {
    try {
        const raw = localStorage.getItem(POI_CACHE_KEY);
        if (!raw) return null;
        const data = JSON.parse(raw);
        if (Date.now() - data.ts > POI_CACHE_TTL) {
            localStorage.removeItem(POI_CACHE_KEY);
            return null;
        }
        return data.items;
    } catch (_) {
        return null;
    }
}

function setPoiCache(items) {
    try {
        localStorage.setItem(POI_CACHE_KEY, JSON.stringify({ ts: Date.now(), items }));
    } catch (_) {}
}

export function initMap(containerId = 'map', overlaySelector = null, loadPOIs = true) {
    const mapEl = document.getElementById(containerId);
    if (!mapEl || !window.L) return;

    const hqCoords = [-34.5888, -58.3900];
    const defaultZoom = (containerId === 'portal-map' || containerId === 'portal-map-fullscreen') ? 12 : 14;
    const newMapInstance = L.map(containerId).setView(hqCoords, defaultZoom);

    // MOSAICOS BASE ESTILO GOOGLE MAPS & CARTO (100% GRATUITOS)
    const googleStreets = L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
    });

    const googleHybrid = L.tileLayer('https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
    });

    const googleSat = L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
    });

    const cartoDark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        subdomains: 'abcd',
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
    });

    // Google Calles como capa predeterminada
    googleStreets.addTo(newMapInstance);

    // Selector de capas para cambiar entre Google Calles, Google Satélite, Híbrido y Oscuro
    const baseMaps = {
        "🗺️ Google Calles": googleStreets,
        "🛰️ Google Satélite": googleSat,
        "🌍 Google Híbrido": googleHybrid,
        "🌙 CartoDB Oscuro": cartoDark
    };
    L.control.layers(baseMaps, null, { position: 'topleft' }).addTo(newMapInstance);

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

    // BOTON DE PANTALLA COMPLETA (SOLO EN MAPA DE PERFIL)
    if (containerId === 'portal-map') {
        const fullscreenBtn = L.control({ position: 'topright' });
        fullscreenBtn.onAdd = function() {
            const div = L.DomUtil.create('div', 'leaflet-control-fullscreen');
            div.innerHTML = `
                <button title="Ver mapa completo" 
                        style="background: #000; border: 1.5px solid #C5A059; color: #C5A059; 
                               width: 34px; height: 34px; cursor: pointer; display: flex; 
                               align-items: center; justify-content: center; 
                               border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.8);
                               transition: all 0.3s ease; outline: none; font-size: 0.9rem;">
                    <i class="fas fa-expand"></i>
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
                if (window.openFullMap) window.openFullMap();
            };
            return div;
        };
        fullscreenBtn.addTo(newMapInstance);
    }

    //CARGAR SUCURSALES DESDE LA API
    fetch('/v1/parking/branches')
        .then(res => res.json())
        .then(branches => {
            window.allBranchesMap = branches; // GUARDAR PARA GEOLOCALIZACION
            const branchMarkers = [];

            const zoomSizer = (zoom) => Math.round((12 + zoom * 0.6) * 3);

            const makeBranchIcon = (zoom, color) => L.divIcon({
                className: 'branch-marker-logo',
                html: `<div style="width:100%;height:100%;background:url('/static/images/logo.png') center/contain no-repeat;border-color:${color};"></div>`,
                iconSize: [zoomSizer(zoom), zoomSizer(zoom)],
                iconAnchor: [zoomSizer(zoom) / 2, zoomSizer(zoom) / 2]
            });

            newMapInstance.on('zoomend', () => {
                const z = newMapInstance.getZoom();
                branchMarkers.forEach(m => {
                    const col = m.options.color || '#C5A059';
                    m.setIcon(makeBranchIcon(z, col));
                });
            });

            branches.forEach(p => {
                if (!p.latitude || !p.longitude) return;
                
                // DISPONIBILIDAD DISCRIMINADA POR TIPO DE VEHÍCULO
                const autoStats = getVehicleAvailability(p.ocupacion_actual, p.capacidad_total);
                const motoStats = getVehicleAvailability(p.ocupacion_motos, p.capacidad_motos);
                const camionetaStats = getVehicleAvailability(p.ocupacion_camionetas, p.capacidad_camionetas);

                // Color del marcador en el mapa basado en disponibilidad de autos
                const statusColor = autoStats.color;

                const formattedAddr = formatAddress(p.direccion);
                const horarioText = p.is_24h ? '24 HORAS' : (p.horario ? p.horario.replace(' UN ', ' a ') : 'Consultar');

                const popupContent = `
                    <div style="text-align: center; width: 250px; padding: 14px 16px; background: #0a0a0a; border-radius: 18px; box-sizing: border-box;">
                        <!-- LOGO Y TITULO -->
                        <img src="${p.logo_url || '/static/images/logo.png'}" style="width: 52px; height: 52px; border-radius: 50%; margin-bottom: 8px; border: 2px solid #C5A059; padding: 2px; background: #000; object-fit: cover;">
                        <br><b style="font-size: 1.08rem; color: #fff; font-family: 'Montserrat', sans-serif; letter-spacing: 0.4px; line-height: 1.3;">${p.nombre}</b>
                        <br><span style="color: #888; font-size: 0.78rem; display: block; margin-top: 3px; text-transform: capitalize; line-height: 1.3;">${formattedAddr}</span>
                        <span style="color: var(--dorado); font-size: 0.75rem; display: inline-block; margin-top: 5px; margin-bottom: 10px; font-weight: 600;"><i class="fas fa-clock" style="margin-right: 5px;"></i>${horarioText}</span>
                        
                        <!-- DISPONIBILIDAD DISCRIMINADA POR VEHÍCULO -->
                        <div style="margin: 8px 0 12px; padding: 10px 12px; background: rgba(255, 255, 255, 0.03); border-radius: 14px; border: 1px solid rgba(197, 160, 89, 0.2); text-align: left;">
                            <div style="font-size: 0.65rem; font-weight: 800; color: #C5A059; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; text-align: center;">
                                Estado de Disponibilidad
                            </div>

                            <!-- Auto -->
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; padding: 7px 10px; background: rgba(0,0,0,0.45); border-radius: 8px; border-left: 3.5px solid ${autoStats.color};">
                                <span style="color: #eee; font-size: 0.78rem; font-weight: 600; display: flex; align-items: center; gap: 7px;">
                                    <i class="fas fa-car" style="color: #888; font-size: 0.85rem; width: 14px;"></i> Auto
                                </span>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="font-size: 0.7rem; font-weight: 800; color: ${autoStats.color}; text-transform: uppercase; letter-spacing: 0.5px;">${autoStats.label}</span>
                                    <span style="width: 10px; height: 10px; border-radius: 50%; background: ${autoStats.color}; box-shadow: 0 0 8px ${autoStats.color}; display: inline-block;"></span>
                                </div>
                            </div>

                            <!-- Moto -->
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; padding: 7px 10px; background: rgba(0,0,0,0.45); border-radius: 8px; border-left: 3.5px solid ${motoStats.color};">
                                <span style="color: #eee; font-size: 0.78rem; font-weight: 600; display: flex; align-items: center; gap: 7px;">
                                    <i class="fas fa-motorcycle" style="color: #888; font-size: 0.85rem; width: 14px;"></i> Moto
                                </span>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="font-size: 0.7rem; font-weight: 800; color: ${motoStats.color}; text-transform: uppercase; letter-spacing: 0.5px;">${motoStats.label}</span>
                                    <span style="width: 10px; height: 10px; border-radius: 50%; background: ${motoStats.color}; box-shadow: 0 0 8px ${motoStats.color}; display: inline-block;"></span>
                                </div>
                            </div>

                            <!-- Camioneta -->
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 7px 10px; background: rgba(0,0,0,0.45); border-radius: 8px; border-left: 3.5px solid ${camionetaStats.color};">
                                <span style="color: #eee; font-size: 0.78rem; font-weight: 600; display: flex; align-items: center; gap: 7px;">
                                    <i class="fas fa-truck-pickup" style="color: #888; font-size: 0.85rem; width: 14px;"></i> Camioneta
                                </span>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="font-size: 0.7rem; font-weight: 800; color: ${camionetaStats.color}; text-transform: uppercase; letter-spacing: 0.5px;">${camionetaStats.label}</span>
                                    <span style="width: 10px; height: 10px; border-radius: 50%; background: ${camionetaStats.color}; box-shadow: 0 0 8px ${camionetaStats.color}; display: inline-block;"></span>
                                </div>
                            </div>
                        </div>

                        <!-- BOTON RESERVAR -->
                        <a href="javascript:void(0)" onclick="irAReserva('${p.nombre}')" 
                           style="background: #C5A059; color: #000; padding: 10px 18px; font-size: 0.72rem; 
                                  font-weight: 900; text-transform: uppercase; letter-spacing: 1px;
                                  width: 100%; display: block; border-radius: 10px;
                                  text-decoration: none; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(197, 160, 89, 0.25); box-sizing: border-box;">
                           RESERVÁ AQUÍ
                        </a>

                        <!-- COMO LLEGAR -->
                        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.08);">
                            <div style="color: #888; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 7px; font-weight: 600;">CÓMO LLEGAR</div>
                            <div style="display: flex; gap: 6px; justify-content: center;">
                                <a href="javascript:void(0)" onclick="getDirectionsTo(${p.latitude}, ${p.longitude})" style="flex: 1; background: #4285F4; color: #fff; padding: 7px 6px; border-radius: 8px; text-decoration: none; font-size: 0.68rem; font-weight: 700; text-align: center; letter-spacing: 0.3px; display: flex; align-items: center; justify-content: center; gap: 4px; transition: 0.3s;">
                                    <i class="fab fa-google" style="font-size: 0.8rem;"></i> Google Maps
                                </a>
                                <a href="javascript:void(0)" onclick="getDirectionsTo(${p.latitude}, ${p.longitude}, 'waze')" style="flex: 1; background: #33CCFF; color: #000; padding: 7px 6px; border-radius: 8px; text-decoration: none; font-size: 0.68rem; font-weight: 700; text-align: center; letter-spacing: 0.3px; display: flex; align-items: center; justify-content: center; gap: 4px; transition: 0.3s;">
                                    <i class="fab fa-waze" style="font-size: 0.8rem;"></i> Waze
                                </a>
                            </div>
                        </div>
                    </div>
                `;
                
                const marker = L.marker([p.latitude, p.longitude], {
                    icon: makeBranchIcon(newMapInstance.getZoom(), statusColor),
                    color: statusColor
                })
                    .addTo(newMapInstance)
                    .bindPopup(popupContent);
                branchMarkers.push(marker);
                
                // ACTUALIZAR OVERLAY DINAMICO AL ABRIR/CERRAR SUCURSAL
                marker.on('popupopen', () => {
                    if (overlaySelector) {
                        const overlay = document.querySelector(overlaySelector);
                        if (overlay) {
                            overlay.querySelector('h4').innerHTML = `<i class="fas fa-building"></i> ${p.nombre}`;
                            overlay.querySelector('p').innerText = formattedAddr;
                            overlay.classList.add('active');
                        }
                    }
                });

                marker.on('popupclose', () => {
                    if (overlaySelector) {
                        const overlay = document.querySelector(overlaySelector);
                        if (overlay) overlay.classList.remove('active');
                    }
                });

                // GUARDAR REFERENCIA AL MARCADOR (ESPECIFICO POR CONTAINERID)
                if (!p.markers) p.markers = {};
                p.markers[containerId] = marker;
            });

            // LOGICA PARA LOCALIZACION AUTOMATICA (VIA URL PARAM)
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

            // CENTRAR MAPA EN SUCURSAL ITUZAINGO (PORTAL DE USUARIO)
            if (containerId === 'portal-map' || containerId === 'portal-map-fullscreen') {
                const ituzaingo = branches.find(b =>
                    b.nombre && b.nombre.toLowerCase().includes('ituzaing')
                );
                if (ituzaingo && ituzaingo.latitude && ituzaingo.longitude) {
                    newMapInstance.setView([ituzaingo.latitude, ituzaingo.longitude], 14);
                }
            }
        })
        .catch(err => console.error('Error al cargar sucursales para el mapa:', err));

    // CARGAR PUNTOS DE INTERES (SOLO SI SE SOLICITA, EJ: MAPA DE LANDING)
    if (loadPOIs) {
        loadTheaters(newMapInstance, containerId);
        loadStadiums(newMapInstance, containerId);
    }
}

const _poiControllers = {};
const _poiLayers = {};

function loadTheaters(mapObj, containerId) {
    if (!_poiLayers[containerId]) _poiLayers[containerId] = {};
    const layers = _poiLayers[containerId];
    layers.theatre = L.layerGroup().addTo(mapObj);
    layers.cinema = L.layerGroup().addTo(mapObj);

    const makeMarker = function(lat, lng, t, cfg, group) {
        const name = t.name || t.operator || t['short_name'] || '(Sin nombre)';
        const addressStr = formatPoiAddress(t);
        return L.marker([lat, lng], { icon: cfg.icon })
            .bindPopup(`
                <div style="text-align:center; min-width:170px; padding:10px 12px; background:#0a0a0a; border-radius:14px; box-sizing:border-box;">
                    <div style="font-size:0.65rem; color:#C5A059; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; font-weight:800;">
                        ${cfg.label}
                    </div>
                    <b style="font-size:0.92rem; color:#fff; font-family:'Montserrat',sans-serif; display:block; line-height:1.3;">
                        ${name}
                    </b>
                    ${addressStr ? `<span style="color:#aaa; font-size:0.75rem; display:block; margin-top:4px; line-height:1.3;">${addressStr}</span>` : ''}
                </div>
            `)
            .addTo(group);
    };

    const icons = {
        theatre: L.divIcon({
            className: 'poi-marker',
            html: `<div style="width:28px;height:28px;background:#9B59B6;border:2px solid #fff;border-radius:8px;box-shadow:0 2px 10px rgba(155,89,182,0.6);display:flex;align-items:center;justify-content:center;font-size:0.8rem;color:#fff;"><i class="fas fa-theater-masks"></i></div>`,
            iconSize: [28, 28], iconAnchor: [14, 14]
        }),
        cinema: L.divIcon({
            className: 'poi-marker',
            html: `<div style="width:28px;height:28px;background:#E74C3C;border:2px solid #fff;border-radius:8px;box-shadow:0 2px 10px rgba(231,76,60,0.6);display:flex;align-items:center;justify-content:center;font-size:0.8rem;color:#fff;"><i class="fas fa-film"></i></div>`,
            iconSize: [28, 28], iconAnchor: [14, 14]
        })
    };

    function createCfg(type) {
        if (type === 'theatre' || type === 'museum') return { icon: icons.theatre, label: type === 'theatre' ? 'Teatro' : 'Museo', type: type };
        if (type === 'cinema') return { icon: icons.cinema, label: 'Cine', type: type };
        return null;
    }

    const poiTypes = { theatre: 'theatre', museum: 'museum', cinema: 'cinema' };

    function loadCachedPoi(d) {
        const cfg = createCfg(d.type);
        const group = d.type === 'cinema' ? layers.cinema : layers.theatre;
        if (cfg) makeMarker(d.lat, d.lng, d.tags, cfg, group);
    }

    // CHECK CACHE LOCALSTORAGE
    const cached = getPoiCache();
    if (cached) {
        cached.forEach(loadCachedPoi);
        addPoiLegend(mapObj, containerId);
        return;
    }

    // ABORT PREVIO SI EXISTE
    if (_poiControllers[containerId]) {
        _poiControllers[containerId].abort();
    }
    const controller = new AbortController();
    _poiControllers[containerId] = controller;

    // LOADING INDICATOR
    const loadingEl = showPoiLoading(mapObj, containerId);

    const OVERPASS_URL = 'https://overpass-api.de/api/interpreter';
    const bbox = '-34.80,-58.90,-34.50,-58.30';

    const query = `[out:json][timeout:60];(node["amenity"="theatre"](${bbox});way["amenity"="theatre"](${bbox});node["tourism"="museum"](${bbox});node["amenity"="cinema"](${bbox});way["amenity"="cinema"](${bbox}););out center 100;`;

    function doFetch(retries, delay) {
        const d = delay || 2000;
        return fetch(OVERPASS_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'data=' + encodeURIComponent(query),
            signal: controller.signal
        })
        .then(res => {
            if ((res.status === 429 || res.status === 504) && retries > 0) {
                console.warn(`[OVERPASS] HTTP ${res.status}, reintentando en ${d}ms... (${retries} restantes)`);
                return new Promise(r => setTimeout(r, d)).then(() => doFetch(retries - 1, Math.min(d * 2, 60000)));
            }
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
        });
    }

    doFetch(6, 3000).then(data => {
        hidePoiLoading(loadingEl);
        if (!data.elements || data.elements.length === 0) return;
        const items = [];
        let teatro = 0, cinema = 0;
        data.elements.forEach(el => {
            const lat = el.lat || (el.center && el.center.lat);
            const lng = el.lon || (el.center && el.center.lon);
            if (!lat || !lng) return;
            const t = el.tags || {};
            let poiType = null;
            if (t.amenity === 'theatre' || t.tourism === 'museum') { poiType = t.amenity === 'theatre' ? 'theatre' : 'museum'; teatro++; }
            else if (t.amenity === 'cinema') { poiType = 'cinema'; cinema++; }
            if (!poiType) return;
            const cfg = createCfg(poiType);
            if (!cfg) return;
            const group = poiType === 'cinema' ? layers.cinema : layers.theatre;
            items.push({ lat, lng, tags: t, type: poiType });
            makeMarker(lat, lng, t, cfg, group);
        });
        if (items.length === 0) return;
        setPoiCache(items);
        addPoiLegend(mapObj, containerId);
    })
    .catch(err => {
        hidePoiLoading(loadingEl);
        if (err.name === 'AbortError') return;
        console.error('[OVERPASS] Error:', err);
        // MOSTRAR TOAST DE ERROR SI EXISTE
        const msg = 'No se pudieron cargar los puntos de interés.';
        if (window.showToast) window.showToast(msg, 'error');
    });
}

function loadStadiums(mapObj, containerId) {
    if (!_poiLayers[containerId]) _poiLayers[containerId] = {};
    const layers = _poiLayers[containerId];
    layers.stadium = L.layerGroup().addTo(mapObj);

    const stadiumIcon = L.divIcon({
        className: 'poi-marker',
        html: `<div style="width:28px;height:28px;background:#27AE60;border:2px solid #fff;border-radius:8px;box-shadow:0 2px 10px rgba(39,174,96,0.6);display:flex;align-items:center;justify-content:center;font-size:0.8rem;color:#fff;"><i class="fas fa-futbol"></i></div>`,
        iconSize: [28, 28], iconAnchor: [14, 14]
    });

    ESTADIOS_FIJOS.forEach(d => {
        L.marker([d.lat, d.lng], { icon: stadiumIcon })
            .bindPopup(`
                <div style="text-align:center; min-width:170px; padding:10px 12px; background:#0a0a0a; border-radius:14px; box-sizing:border-box;">
                    <div style="font-size:0.65rem; color:#27AE60; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; font-weight:800;">
                        Estadio
                    </div>
                    <b style="font-size:0.92rem; color:#fff; font-family:'Montserrat',sans-serif; display:block; line-height:1.3;">
                        ${d.name}
                    </b>
                    ${d.address ? `<span style="color:#aaa; font-size:0.75rem; display:block; margin-top:4px; line-height:1.3;">${d.address}</span>` : ''}
                </div>
            `)
            .addTo(layers.stadium);
    });

    _stadiumsLoaded = true;
    addPoiLegend(mapObj, containerId);
}

let _stadiumsLoaded = false;

function showPoiLoading(mapObj, containerId) {
    const id = `poi-loading-${containerId}`;
    // EVITAR DUPLICADOS
    if (document.getElementById(id)) return { el: document.getElementById(id), id };
    const ctrl = L.control({ position: 'bottomleft' });
    ctrl.onAdd = function() {
        const div = L.DomUtil.create('div', 'poi-loading');
        div.id = id;
        div.innerHTML = `<div style="background:rgba(10,10,10,0.9);padding:6px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.06);font-size:0.65rem;color:var(--dorado);display:flex;align-items:center;gap:6px;"><i class="fas fa-spinner fa-pulse"></i> Cargando puntos de interés...</div>`;
        return div;
    };
    ctrl.addTo(mapObj);
    return { el: ctrl, id };
}

function hidePoiLoading(ctrl) {
    if (!ctrl || !ctrl.el) return;
    try {
        const el = document.getElementById(ctrl.id);
        if (el) el.remove();
    } catch (_) {}
    try {
        if (typeof ctrl.el.remove === 'function') ctrl.el.remove();
    } catch (_) {}
}

function addPoiLegend(mapObj, containerId) {
    // REMOVER LEGEND ANTERIOR SI EXISTE
    const oldLegend = document.querySelector('.map-poi-legend');
    if (oldLegend) {
        const parent = oldLegend.closest('.leaflet-control');
        if (parent) parent.remove();
        else oldLegend.remove();
    }

    const layers = _poiLayers[containerId] || {};

    const toggleLayer = (name, btnEl) => {
        const g = layers[name];
        if (!g) return;
        if (mapObj.hasLayer(g)) {
            mapObj.removeLayer(g);
            btnEl.style.opacity = '0.4';
            btnEl.style.textDecoration = 'line-through';
        } else {
            g.addTo(mapObj);
            btnEl.style.opacity = '1';
            btnEl.style.textDecoration = 'none';
        }
    };

    const legend = L.control({ position: 'bottomleft' });
    legend.onAdd = function() {
        const div = L.DomUtil.create('div', 'map-poi-legend');
        const stadiumHtml = _stadiumsLoaded ? `<span id="legend-stadium" style="display:flex;align-items:center;gap:4px;color:#ccc;cursor:pointer;"><span style="width:18px;height:18px;background:#27AE60;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;font-size:0.5rem;color:#fff;"><i class="fas fa-futbol"></i></span> Estadio</span>` : '';
        div.innerHTML = `
            <div style="background:rgba(10,10,10,0.9);padding:8px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.06);font-size:0.65rem;">
                <div style="color:#fff;font-weight:700;margin-bottom:5px;display:flex;align-items:center;gap:6px;letter-spacing:0.5px;">
                    <i class="fas fa-map-pin" style="color:var(--dorado);"></i> PUNTOS DE INTERÉS
                </div>
                <div style="display:flex;gap:10px;flex-wrap:wrap;">
                    <span id="legend-theatre" style="display:flex;align-items:center;gap:4px;color:#ccc;cursor:pointer;">
                        <span style="width:18px;height:18px;background:#9B59B6;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;font-size:0.5rem;color:#fff;"><i class="fas fa-theater-masks"></i></span> Teatro/Museo
                    </span>
                    <span id="legend-cinema" style="display:flex;align-items:center;gap:4px;color:#ccc;cursor:pointer;">
                        <span style="width:18px;height:18px;background:#E74C3C;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;font-size:0.5rem;color:#fff;"><i class="fas fa-film"></i></span> Cine
                    </span>
                    ${stadiumHtml}
                </div>
            </div>`;
        return div;
    };
    legend.addTo(mapObj);

    // ASIGNAR EVENTOS POST-AGREGADO
    setTimeout(() => {
        const el = document.querySelector('.map-poi-legend');
        if (!el) return;
        const th = el.querySelector('#legend-theatre');
        const ci = el.querySelector('#legend-cinema');
        const st = el.querySelector('#legend-stadium');
        if (th) th.onclick = () => toggleLayer('theatre', th);
        if (ci) ci.onclick = () => toggleLayer('cinema', ci);
        if (st) st.onclick = () => toggleLayer('stadium', st);
    }, 50);
}

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
    const toast = (msg, type) => {
        if (window.showToast) window.showToast(msg, type);
    };

    toast('Buscando tu ubicación...', 'info');

    navigator.geolocation.getCurrentPosition((pos) => {
        const myLat = pos.coords.latitude;
        const myLng = pos.coords.longitude;

        if (!window.allBranchesMap || window.allBranchesMap.length === 0) return;

        // LIMPIAR MARCADOR Y CIRCULO ANTERIOR DEL USUARIO
        if (window._userMarker && activeMap) activeMap.removeLayer(window._userMarker);
        if (window._userCircle && activeMap) activeMap.removeLayer(window._userCircle);

        // MARCADOR DE UBICACION REAL DEL USUARIO
        const userIcon = L.divIcon({
            className: 'user-location-marker',
            html: `<div style="width:22px;height:22px;background:#4285F4;border:3px solid #fff;border-radius:50%;box-shadow:0 0 20px rgba(66,133,244,0.8);display:flex;align-items:center;justify-content:center;"><div style="width:8px;height:8px;background:#fff;border-radius:50%;"></div></div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11]
        });
        window._userMarker = L.marker([myLat, myLng], { icon: userIcon, zIndexOffset: 1000 })
            .addTo(activeMap)
            .bindPopup(`<div style="text-align:center;padding:5px;color:#fff;"><b>📍 Tu ubicación</b></div>`);

        // CIRCULO DE PRECISION ALREDEDOR DEL USUARIO
        window._userCircle = L.circle([myLat, myLng], {
            radius: pos.coords.accuracy || 50,
            color: '#4285F4',
            fillColor: '#4285F4',
            fillOpacity: 0.1,
            weight: 2,
            opacity: 0.4
        }).addTo(activeMap);

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
            // AJUSTAR VISTA PARA MOSTRAR AMBOS PUNTOS
            const bounds = L.latLngBounds(L.latLng(myLat, myLng), L.latLng(nearest.latitude, nearest.longitude));
            activeMap.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 });

            nearest.markers && Object.values(nearest.markers).forEach(m => {
                if (m._map === activeMap) {
                    m.openPopup();
                    setTimeout(() => {
                        if (activeMap) activeMap.invalidateSize();
                    }, 200);
                }
            });

            // ACTUALIZAR OVERLAY CON DISTANCIA
            const sel = document.querySelector('.map-overlay.active, .map-overlay-fullscreen.active');
            if (sel) {
                const distKm = minDistance < 1 ? `${(minDistance * 1000).toFixed(0)} m` : `${minDistance.toFixed(1)} km`;
                const distP = sel.querySelector('p');
                if (distP) distP.innerText = `${nearest.nombre} — ${distKm}`;
            }

            toast(`Sucursal más cercana: ${nearest.nombre} (a ${(minDistance).toFixed(1)} km)`);
        }
    }, (err) => {
        console.warn('Error de geolocalización:', err);
        toast('No se pudo obtener tu ubicación.');
    });
}
