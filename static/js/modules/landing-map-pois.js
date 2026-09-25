/**
 * AUTOPASS - PUNTOS DE INTERES DEL MAPA DE LA LANDING
 * Submodulo de landing-map.js: cines, teatros, museos (Overpass API con cache
 * en localStorage) y estadios fijos, mas indicadores de carga y leyenda.
 */

import { ESTADIOS_FIJOS } from './landing-data.js';
import { formatPoiAddress, getPoiCache, setPoiCache } from './landing-map-data.js';

const _poiControllers = {};
const _poiLayers = {};
let _stadiumsLoaded = false;

export function loadTheaters(mapObj, containerId) {
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
                    <div style="font-size:0.65rem; color:#dfba6b; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; font-weight:800;">
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

export function loadStadiums(mapObj, containerId) {
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