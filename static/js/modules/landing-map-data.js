/**
 * AUTOPASS - DATOS Y UTILIDADES DEL MAPA DE LA LANDING
 * Submodulo de landing-map.js: helpers de normalizacion de direcciones,
 * cache de POIs y apertura de rutas en Google Maps / Waze.
 */

import { POI_CACHE_KEY, POI_CACHE_TTL } from './landing-data.js';

export function extractLocality(branch) {
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

export function formatAddress(addr) {
    if (!addr) return '';
    // SI NO TIENE COMA, INTENTAMOS PONER UNA DESPUES DEL NUMERO DE LA CALLE
    if (!addr.includes(',')) {
        return addr.replace(/(\d+)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)$/, '$1, $2');
    }
    return addr;
}

export function formatPoiAddress(t) {
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

export function getDirectionsTo(branchLat, branchLng, mode) {
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

export function getPoiCache() {
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

export function setPoiCache(items) {
    try {
        localStorage.setItem(POI_CACHE_KEY, JSON.stringify({ ts: Date.now(), items }));
    } catch (_) {}
}