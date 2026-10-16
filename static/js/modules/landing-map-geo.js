/**
 * AUTOPASS - GEOLOCALIZACION Y SUCURSAL MAS CERCANA
 * Submodulo de landing-map.js: calculo de distancia, localizacion del usuario
 * y resaltado de la sucursal mas cercana.
 */

import { lmState } from './landing-map-state.js';
import { mapMotionOptions } from './utils.js';

let _userMarker = null;
let _userCircle = null;

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
    const activeMap = targetMap || lmState.mapInstance;
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

        if (!lmState.allBranchesMap || lmState.allBranchesMap.length === 0) return;

        // LIMPIAR MARCADOR Y CIRCULO ANTERIOR DEL USUARIO
        if (_userMarker && activeMap) activeMap.removeLayer(_userMarker);
        if (_userCircle && activeMap) activeMap.removeLayer(_userCircle);

        // MARCADOR DE UBICACION REAL DEL USUARIO
        const userIcon = L.divIcon({
            className: 'user-location-marker',
            html: `<div style="width:22px;height:22px;background:#4285F4;border:3px solid #fff;border-radius:50%;box-shadow:0 0 20px rgba(66,133,244,0.8);display:flex;align-items:center;justify-content:center;"><div style="width:8px;height:8px;background:#fff;border-radius:50%;"></div></div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11]
        });
        _userMarker = L.marker([myLat, myLng], { icon: userIcon, zIndexOffset: 1000 })
            .addTo(activeMap)
            .bindPopup(`<div style="text-align:center;padding:5px;color:#fff;"><b>📍 Tu ubicación</b></div>`);

        // CIRCULO DE PRECISION ALREDEDOR DEL USUARIO
        _userCircle = L.circle([myLat, myLng], {
            radius: pos.coords.accuracy || 50,
            color: '#4285F4',
            fillColor: '#4285F4',
            fillOpacity: 0.1,
            weight: 2,
            opacity: 0.4
        }).addTo(activeMap);

        let nearest = null;
        let minDistance = Infinity;

        lmState.allBranchesMap.forEach(p => {
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
            activeMap.fitBounds(bounds, mapMotionOptions({ padding: [60, 60], maxZoom: 16 }));

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