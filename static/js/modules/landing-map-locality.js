/**
 * AUTOPASS - FILTRO POR LOCALIDAD DEL MAPA DE LA LANDING
 * Submodulo de landing-map.js: filtrar las sucursales visibles segun
 * la localidad seleccionada, volando a los limites del resultado.
 */

import { lmState } from './landing-map-state.js';
import { prefersReducedMotion, mapMotionOptions } from './utils.js';

export function filterMapByLocality(selectedLocality, containerId = 'map', targetMap = null, defaultCoords = [-34.5888, -58.3900], defaultZoom = 12) {
    const mapObj = targetMap || lmState.mapInstances[containerId] || lmState.mapInstance;
    const items = lmState.mapLocalityItems[containerId];
    if (!mapObj || !items) return;

    // El vuelo de Leaflet anima por requestAnimationFrame: el bloque CSS de
    // `prefers-reduced-motion` no lo puede frenar (WCAG 2.3.3). Las opciones las
    // decide `mapMotionOptions()`; aca solo se necesita saber si hay que esperar
    // el vuelo antes de abrir el popup.
    const quieto = prefersReducedMotion();
    const VUELO = { duration: 1.2 };

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
        mapObj.flyTo([target.lat, target.lng], 16, mapMotionOptions(VUELO));
        setTimeout(() => {
            target.marker.openPopup();
        }, quieto ? 0 : 600);
    } else if (matchingItems.length > 1) {
        mapObj.flyToBounds(bounds, mapMotionOptions({ ...VUELO, padding: [60, 60] }));
    } else if (selectedLocality === 'all') {
        mapObj.flyTo(defaultCoords, defaultZoom, mapMotionOptions(VUELO));
    }

    if (window.showToast && selectedLocality !== 'all') {
        window.showToast(`Mapa filtrado por localidad: ${selectedLocality} (${matchingItems.length} sucursal${matchingItems.length !== 1 ? 'es' : ''})`, 'info');
    }
}