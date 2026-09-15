import { ESTADIOS_FIJOS, POI_CACHE_KEY, POI_CACHE_TTL } from './landing-data.js';

let mapInstance = null;
const _mapInstances = {};
const _mapLocalityItems = {};

function extractLocality(branch) {
    if (branch.localidad && branch.localidad.trim()) return branch.localidad.trim();
    if (branch.nombre) {
        let clean = branch.nombre.replace(/autopass/gi, '').trim();
        clean = clean.replace(/^[-\s:]+/, '').trim();
        if (clean) return clean;
    }
    if (branch.direccion && branch.direccion.includes(',')) {
        const parts = branch.direccion.split(',');
        const candidate = parts[parts.length - 1].trim();
        if (candidate) return candidate;
    }
    return 'General';
}

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

    // MOSAICO BASE GOOGLE CALLES (100% GRATUITO)
    const googleStreets = L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
    });

    // Google Calles como única capa del mapa
    googleStreets.addTo(newMapInstance);

    // SI ES EL MAPA PRINCIPAL DE LA LANDING, GUARDAMOS LA INSTANCIA GLOBAL PARA GEOLOCALIZACION
    if (containerId === 'map') mapInstance = newMapInstance;

    _mapInstances[containerId] = newMapInstance;
    _mapLocalityItems[containerId] = [];

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

            const localitiesSet = new Set();

            branches.forEach(p => {
                if (!p.latitude || !p.longitude) return;
                
                const loc = extractLocality(p);
                localitiesSet.add(loc);
                p._locality = loc;

                // Color del marcador en el mapa basado en disponibilidad de autos
                const statusColor = '#22c55e';

                const formattedAddr = formatAddress(p.direccion);
                const horarioText = p.is_24h ? '24 HORAS' : (p.horario ? p.horario.replace(' UN ', ' a ') : 'Consultar');

                const popupContent = `
                    <div style="text-align: center; width: 250px; padding: 14px 16px; background: #0a0a0a; border-radius: 18px; box-sizing: border-box;">
                        <!-- LOGO Y TITULO -->
                        <img src="${p.logo_url || '/static/images/logo.png'}" style="width: 52px; height: 52px; border-radius: 50%; margin-bottom: 8px; border: 2px solid #C5A059; padding: 2px; background: #000; object-fit: cover;">
                        <br><b style="font-size: 1.08rem; color: #fff; font-family: 'Montserrat', sans-serif; letter-spacing: 0.4px; line-height: 1.3;">${p.nombre}</b>
                        <br><span style="color: #888; font-size: 0.78rem; display: block; margin-top: 3px; text-transform: capitalize; line-height: 1.3;">${formattedAddr}</span>
                        <span style="color: var(--dorado); font-size: 0.75rem; display: inline-block; margin-top: 5px; margin-bottom: 10px; font-weight: 600;"><i class="fas fa-clock" style="margin-right: 5px;"></i>${horarioText}</span>
                        
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

                if (_mapLocalityItems[containerId]) {
                    _mapLocalityItems[containerId].push({
                        marker,
                        locality: loc,
                        lat: p.latitude,
                        lng: p.longitude,
                        branch: p
                    });
                }
                
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

            // AGREGAR CONTROL FLOTANTE DE BUSCADOR CON AUTOCOMPLETADO POR LOCALIDAD (TOP-LEFT)
            const searchCtrl = L.control({ position: 'topleft' });
            searchCtrl.onAdd = function() {
                const div = L.DomUtil.create('div', 'leaflet-control-locality-search');
                div.innerHTML = `
                    <div class="locality-search-box" style="background: #090b0f !important; border: 2px solid #C5A059 !important; border-radius: 12px; padding: 0 12px; height: 38px; display: flex; align-items: center; gap: 8px; box-shadow: 0 8px 25px rgba(0,0,0,0.9); box-sizing: border-box;">
                        <i class="fas fa-search search-icon" style="color: #C5A059 !important; font-size: 0.9rem;"></i>
                        <input type="text" 
                               id="locality-search-input-${containerId}" 
                               placeholder="Escribí localidad o sucursal..." 
                               style="background: transparent !important; border: none !important; outline: none !important; color: #ffffff !important; font-size: 0.82rem !important; font-weight: 700 !important; width: 100% !important;"
                               autocomplete="off">
                        <button type="button" class="search-clear-btn" id="locality-clear-btn-${containerId}" style="display:none; background: transparent; border: none; color: #aaa; cursor: pointer; padding: 4px;" title="Limpiar búsqueda">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div id="locality-results-${containerId}" class="locality-results-dropdown" style="display:none; position: absolute; top: 46px; left: 0; width: 100%; max-height: 280px; overflow-y: auto; background: #090b0e !important; border: 2px solid #C5A059 !important; border-radius: 14px; box-shadow: 0 15px 45px rgba(0,0,0,0.98), 0 0 25px rgba(197,160,89,0.35); padding: 8px; z-index: 2000; box-sizing: border-box;"></div>
                `;

                div.onclick = (e) => e.stopPropagation();
                div.onmousedown = (e) => e.stopPropagation();
                div.ondblclick = (e) => e.stopPropagation();

                setTimeout(() => {
                    const inputEl = div.querySelector(`#locality-search-input-${containerId}`);
                    const clearBtn = div.querySelector(`#locality-clear-btn-${containerId}`);
                    const dropdownEl = div.querySelector(`#locality-results-${containerId}`);

                    if (inputEl && dropdownEl) {
                        const renderResults = (query) => {
                            const q = query.trim().toLowerCase();
                            if (!q) {
                                dropdownEl.style.display = 'none';
                                if (clearBtn) clearBtn.style.display = 'none';
                                filterMapByLocality('all', containerId, newMapInstance, hqCoords, defaultZoom);
                                return;
                            }

                            if (clearBtn) clearBtn.style.display = 'flex';

                            // FILTRAR SUCURSALES POR NOMBRE, LOCALIDAD O DIRECCION
                            const matchedBranches = branches.filter(b => {
                                if (!b.latitude || !b.longitude) return false;
                                const nombre = (b.nombre || '').toLowerCase();
                                const direccion = (b.direccion || '').toLowerCase();
                                const localidad = (b._locality || b.localidad || '').toLowerCase();
                                return nombre.includes(q) || direccion.includes(q) || localidad.includes(q);
                            });

                            if (matchedBranches.length === 0) {
                                dropdownEl.innerHTML = `
                                    <div class="locality-result-empty" style="background: #171b26 !important; border: 1.5px solid rgba(245, 158, 11, 0.5) !important; border-radius: 10px; padding: 14px; display: flex; align-items: flex-start; gap: 12px; color: #f59e0b;">
                                        <i class="fas fa-triangle-exclamation" style="font-size: 1.2rem; margin-top: 2px; color: #f59e0b !important;"></i>
                                        <div>
                                            <strong style="display: block; color: #ffffff !important; font-size: 0.86rem; font-weight: 800; margin-bottom: 3px;">No hay sucursales disponibles</strong>
                                            <span style="color: #cbd5e1 !important; font-size: 0.78rem;">No encontramos sucursales de AUTOPASS en la localidad ingresada.</span>
                                        </div>
                                    </div>
                                `;
                            } else {
                                dropdownEl.innerHTML = matchedBranches.map(b => {
                                    const formattedAddr = formatAddress(b.direccion);
                                    return `
                                        <div class="locality-result-item" data-lat="${b.latitude}" data-lng="${b.longitude}" data-nombre="${b.nombre}"
                                             style="background: #131622 !important; padding: 10px 12px; border-radius: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px; border: 1px solid rgba(197, 160, 89, 0.3) !important; margin-bottom: 6px; transition: all 0.2s ease;">
                                            <div class="result-item-header" style="display: flex; align-items: center; gap: 8px; color: #ffffff !important; font-size: 0.88rem; font-weight: 800;">
                                                <i class="fas fa-building-circle-check" style="color: #C5A059 !important; font-size: 0.85rem;"></i>
                                                <strong style="color: #ffffff !important;">${b.nombre}</strong>
                                            </div>
                                            <div class="result-item-address" style="font-size: 0.78rem; color: #e2e8f0 !important; display: flex; align-items: center; gap: 6px; font-weight: 500;">
                                                <i class="fas fa-location-dot" style="color: #C5A059 !important; font-size: 0.72rem;"></i> ${formattedAddr}
                                            </div>
                                        </div>
                                    `;
                                }).join('');

                                // ADJUNTAR EVENTOS DE HOVER Y CLICK A CADA ITEM DE RESULTADO
                                dropdownEl.querySelectorAll('.locality-result-item').forEach(item => {
                                    item.onmouseenter = () => {
                                        item.style.background = 'rgba(197, 160, 89, 0.3) !important';
                                        item.style.borderColor = '#C5A059 !important';
                                    };
                                    item.onmouseleave = () => {
                                        item.style.background = '#131622 !important';
                                        item.style.borderColor = 'rgba(197, 160, 89, 0.3) !important';
                                    };

                                    item.onclick = (e) => {
                                        e.stopPropagation();
                                        const lat = parseFloat(item.getAttribute('data-lat'));
                                        const lng = parseFloat(item.getAttribute('data-lng'));
                                        const nombre = item.getAttribute('data-nombre');

                                        inputEl.value = nombre;
                                        dropdownEl.style.display = 'none';

                                        // VOLAR AL PUNTO Y ABRIR POPUP
                                        newMapInstance.flyTo([lat, lng], 16, { animate: true, duration: 1.2 });
                                        
                                        const targetBranch = branches.find(b => b.nombre === nombre);
                                        if (targetBranch && targetBranch.markers && targetBranch.markers[containerId]) {
                                            setTimeout(() => {
                                                targetBranch.markers[containerId].openPopup();
                                            }, 700);
                                        }

                                        if (window.showToast) {
                                            window.showToast(`Navegando a ${nombre}`, 'info');
                                        }
                                    };
                                });
                            }

                            dropdownEl.style.display = 'block';
                        };

                        inputEl.addEventListener('input', (e) => renderResults(e.target.value));
                        inputEl.addEventListener('focus', () => {
                            if (inputEl.value.trim()) renderResults(inputEl.value);
                        });

                        if (clearBtn) {
                            clearBtn.onclick = (e) => {
                                e.stopPropagation();
                                inputEl.value = '';
                                dropdownEl.style.display = 'none';
                                clearBtn.style.display = 'none';
                                filterMapByLocality('all', containerId, newMapInstance, hqCoords, defaultZoom);
                            };
                        }

                        // CERRAR DESPLEGABLE AL HACER CLICK FUERA
                        document.addEventListener('click', (e) => {
                            if (!div.contains(e.target)) {
                                dropdownEl.style.display = 'none';
                            }
                        });
                    }
                }, 50);

                return div;
            };
            searchCtrl.addTo(newMapInstance);

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

export function filterMapByLocality(selectedLocality, containerId = 'map', targetMap = null, defaultCoords = [-34.5888, -58.3900], defaultZoom = 12) {
    const mapObj = targetMap || _mapInstances[containerId] || mapInstance;
    const items = _mapLocalityItems[containerId];
    if (!mapObj || !items) return;

    const matchingItems = [];
    const bounds = L.latLngBounds();

    items.forEach(item => {
        const isMatch = (selectedLocality === 'all' || item.locality.toLowerCase() === selectedLocality.toLowerCase());
        if (isMatch) {
            if (!mapObj.hasLayer(item.marker)) {
                item.marker.addTo(mapObj);
            }
            matchingItems.push(item);
            bounds.extend([item.lat, item.lng]);
        } else {
            if (mapObj.hasLayer(item.marker)) {
                mapObj.removeLayer(item.marker);
            }
        }
    });

    if (matchingItems.length === 1) {
        const target = matchingItems[0];
        mapObj.flyTo([target.lat, target.lng], 16, { animate: true, duration: 1.2 });
        setTimeout(() => {
            target.marker.openPopup();
        }, 600);
    } else if (matchingItems.length > 1) {
        mapObj.flyToBounds(bounds, { padding: [60, 60], animate: true, duration: 1.2 });
    } else if (selectedLocality === 'all') {
        mapObj.flyTo(defaultCoords, defaultZoom, { animate: true, duration: 1.2 });
    }

    if (window.showToast && selectedLocality !== 'all') {
        window.showToast(`Mapa filtrado por localidad: ${selectedLocality} (${matchingItems.length} sucursal${matchingItems.length !== 1 ? 'es' : ''})`, 'info');
    }
}
window.filterMapByLocality = filterMapByLocality;

