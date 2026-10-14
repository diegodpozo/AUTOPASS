/**
 * AUTOPASS - MAPA DE LA LANDING (FACHADA)
 * Repositorio de la instancia Leaflet de la landing y del perfil de usuario.
 * Fachada que orquesta los submodulos:
 *   - landing-map-state:   estado compartido (instancias, sucursales, localidades)
 *   - landing-map-data:    helpers de direccion, cache de POIs y rutas (Google/Waze)
 *   - landing-map-pois:    cargadores de puntos de interes (cines/teatros/estadios)
 *   - landing-map-geo:     geolocalizacion y sucursal mas cercana
 *   - landing-map-locality: filtro de sucursales por localidad
 */

import { getDirectionsTo, extractLocality, formatAddress } from './landing-map-data.js';
import { escapeHtml } from './utils.js';
import { loadTheaters, loadStadiums } from './landing-map-pois.js';
import { findNearestBranch } from './landing-map-geo.js';
import { filterMapByLocality } from './landing-map-locality.js';
import { lmState } from './landing-map-state.js';
import { THEME } from './theme.js';

export { getDirectionsTo };
export { findNearestBranch };
export { filterMapByLocality };

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
    if (containerId === 'map') lmState.mapInstance = newMapInstance;

    lmState.mapInstances[containerId] = newMapInstance;
    lmState.mapLocalityItems[containerId] = [];

    // AGREGAR BOTON DE MI UBICACION EN EL MAPA (TOP-RIGHT PARA EVITAR CONFLICTO CON ZOOM)
    const locationBtn = L.control({ position: 'topright' });
    locationBtn.onAdd = function() {
        const div = L.DomUtil.create('div', 'leaflet-control-geolocation');
        div.innerHTML = `
            <button title="Buscar sucursal más cercana" 
                    style="background: #000; border: 1.5px solid #dfba6b; color: #dfba6b; 
                           width: 34px; height: 34px; cursor: pointer; display: flex; 
                           align-items: center; justify-content: center; 
                           border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.8);
                           transition: all 0.3s ease; outline: none; font-size: 0.9rem;">
                <i class="fas fa-location-crosshairs"></i>
            </button>`;
        
        div.onmouseover = () => { 
            const btn = div.querySelector('button');
            if (btn) { btn.style.background = THEME.gold; btn.style.color = THEME.pointDark; }
        };
        div.onmouseout = () => { 
            const btn = div.querySelector('button');
            if (btn) { btn.style.background = '#111'; btn.style.color = THEME.gold; }
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
                        style="background: #000; border: 1.5px solid #dfba6b; color: #dfba6b; 
                               width: 34px; height: 34px; cursor: pointer; display: flex; 
                               align-items: center; justify-content: center; 
                               border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.8);
                               transition: all 0.3s ease; outline: none; font-size: 0.9rem;">
                    <i class="fas fa-expand"></i>
                </button>`;
            div.onmouseover = () => {
                const btn = div.querySelector('button');
                if (btn) { btn.style.background = THEME.gold; btn.style.color = THEME.pointDark; }
            };
            div.onmouseout = () => {
                const btn = div.querySelector('button');
                if (btn) { btn.style.background = '#111'; btn.style.color = THEME.gold; }
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
            lmState.allBranchesMap = branches; // GUARDAR PARA GEOLOCALIZACION
            const branchMarkers = [];

            const zoomSizer = (zoom) => Math.round((12 + zoom * 0.6) * 3);

            const makeBranchIcon = (zoom, color) => L.divIcon({
                className: 'branch-marker-logo',
                html: `<div style="width:100%;height:100%;border-color:${color};"></div>`,
                iconSize: [zoomSizer(zoom), zoomSizer(zoom)],
                iconAnchor: [zoomSizer(zoom) / 2, zoomSizer(zoom) / 2]
            });

            newMapInstance.on('zoomend', () => {
                const z = newMapInstance.getZoom();
                branchMarkers.forEach(m => {
                    const col = m.options.color || THEME.gold;
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
                        <img src="${p.logo_url || '/static/images/logo.png'}" style="width: 52px; height: 52px; border-radius: 50%; margin-bottom: 8px; border: 2px solid #dfba6b; padding: 2px; background: #000; object-fit: cover;">
                        <br><b style="font-size: 1.08rem; color: #fff; font-family: 'Montserrat', sans-serif; letter-spacing: 0.4px; line-height: 1.3;">${p.nombre}</b>
                        <br><span style="color: #888; font-size: 0.78rem; display: block; margin-top: 3px; text-transform: capitalize; line-height: 1.3;">${formattedAddr}</span>
                        <span style="color: var(--dorado); font-size: 0.75rem; display: inline-block; margin-top: 5px; margin-bottom: 10px; font-weight: 600;"><i class="fas fa-clock" style="margin-right: 5px;"></i>${horarioText}</span>
                        
                        <!-- BOTON RESERVAR -->
                        <a href="javascript:void(0)" onclick="irAReserva('${p.nombre}')" 
                           style="background: #dfba6b; color: #000; padding: 10px 18px; font-size: 0.72rem; 
                                  font-weight: 900; text-transform: uppercase; letter-spacing: 1px;
                                  width: 100%; display: block; border-radius: 10px;
                                  text-decoration: none; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(223, 186, 107, 0.25); box-sizing: border-box;">
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

                if (lmState.mapLocalityItems[containerId]) {
                    lmState.mapLocalityItems[containerId].push({
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
                            overlay.querySelector('h4').innerHTML = `<i class="fas fa-building"></i> ${escapeHtml(p.nombre)}`;
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
                    <div class="locality-search-box" style="background: #090b0f !important; border: 2px solid #dfba6b !important; border-radius: 12px; padding: 0 12px; height: 38px; display: flex; align-items: center; gap: 8px; box-shadow: 0 8px 25px rgba(0,0,0,0.9); box-sizing: border-box;">
                        <i class="fas fa-search search-icon" style="color: #dfba6b !important; font-size: 0.9rem;"></i>
                        <input type="text" 
                               id="locality-search-input-${containerId}" 
                               placeholder="Escribí localidad o sucursal..." 
                               style="background: transparent !important; border: none !important; outline: none !important; color: #ffffff !important; font-size: 0.82rem !important; font-weight: 700 !important; width: 100% !important;"
                               autocomplete="off">
                        <button type="button" class="search-clear-btn" id="locality-clear-btn-${containerId}" style="display:none; background: transparent; border: none; color: #aaa; cursor: pointer; padding: 4px;" title="Limpiar búsqueda">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div id="locality-results-${containerId}" class="locality-results-dropdown" style="display:none; position: absolute; top: 46px; left: 0; width: 100%; max-height: 280px; overflow-y: auto; background: #090b0e !important; border: 2px solid #dfba6b !important; border-radius: 14px; box-shadow: 0 15px 45px rgba(0,0,0,0.98), 0 0 25px rgba(223, 186, 107,0.35); padding: 8px; z-index: 2000; box-sizing: border-box;"></div>
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
                                             style="background: #131622 !important; padding: 10px 12px; border-radius: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px; border: 1px solid rgba(223, 186, 107, 0.3) !important; margin-bottom: 6px; transition: all 0.2s ease;">
                                            <div class="result-item-header" style="display: flex; align-items: center; gap: 8px; color: #ffffff !important; font-size: 0.88rem; font-weight: 800;">
                                                <i class="fas fa-building-circle-check" style="color: #dfba6b !important; font-size: 0.85rem;"></i>
                                                <strong style="color: #ffffff !important;">${b.nombre}</strong>
                                            </div>
                                            <div class="result-item-address" style="font-size: 0.78rem; color: #e2e8f0 !important; display: flex; align-items: center; gap: 6px; font-weight: 500;">
                                                <i class="fas fa-location-dot" style="color: #dfba6b !important; font-size: 0.72rem;"></i> ${formattedAddr}
                                            </div>
                                        </div>
                                    `;
                                }).join('');

                                // ADJUNTAR EVENTOS DE HOVER Y CLICK A CADA ITEM DE RESULTADO
                                dropdownEl.querySelectorAll('.locality-result-item').forEach(item => {
                                    item.onmouseenter = () => {
                                        item.style.background = THEME.goldGlow;
                                        item.style.borderColor = THEME.gold;
                                    };
                                    item.onmouseleave = () => {
                                        item.style.background = '#131622 !important';
                                        item.style.borderColor = THEME.goldBorder;
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