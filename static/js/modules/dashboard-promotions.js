import api from './api.js';
import { showToast, showConfirm } from './utils.js';

/**
 * PANEL PROMOTIONS MODULO
 * GESTION DE BENEFICIOS Y PROMOCIONES PARA EL SISTEMA DE FIDELIZACION.
 */

let promotionsCache = [];
let editingPromotionId = null;
let promoMap = null;
let promoMarker = null;
let reverseGeocodeTimer = null;

export function initPromoMap() {
    const mapEl = document.getElementById('promo-map-picker');
    if (!mapEl || promoMap || !window.L) return;

    promoMap = window.L.map('promo-map-picker').setView([-34.5888, -58.3900], 13);

    const googleStreets = window.L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
    });
    googleStreets.addTo(promoMap);

    promoMap.on('click', function(e) {
        updatePromoMarker(e.latlng.lat, e.latlng.lng);
    });
}

function updatePromoMarker(lat, lng) {
    if (!promoMap || !window.L) return;

    if (promoMarker) {
        promoMarker.setLatLng([lat, lng]);
    } else {
        const goldIcon = window.L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color: #dfba6b; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #dfba6b;"></div>`,
            iconSize: [15, 15],
            iconAnchor: [7, 7]
        });
        promoMarker = window.L.marker([lat, lng], { icon: goldIcon }).addTo(promoMap);
    }

    const elLat = document.getElementById('promo-latitude');
    const elLng = document.getElementById('promo-longitude');
    if (elLat) elLat.value = lat.toFixed(6);
    if (elLng) elLng.value = lng.toFixed(6);

    // REVERSE GEOCODING: AL MARCA R UN PUNTO EN EL MAPA, ACTUALIZAR EL CAMPO DE DIRECCION CON ESA CALLE
    const dirInput = document.getElementById('promo-direccion');
    if (dirInput && window.L) {
        if (reverseGeocodeTimer) clearTimeout(reverseGeocodeTimer);
        reverseGeocodeTimer = setTimeout(async () => {
            try {
                const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat.toFixed(6)}&lon=${lng.toFixed(6)}&addressdetails=1`);
                const data = await res.json();
                if (data && data.display_name) {
                    const a = data.address || {};
                    const calle = [a.road || a.pedestrian || a.suburb, a.house_number].filter(Boolean).join(' ');
                    const localidad = a.city || a.town || a.county || '';
                    dirInput.value = [calle, localidad].filter(Boolean).join(', ') || data.display_name;
                }
            } catch (err) {
                console.error('Error en reverse geocoding:', err);
            }
        }, 500);
    }
}

function _resetPromoMap() {
    if (promoMarker && promoMap) {
        promoMap.removeLayer(promoMarker);
        promoMarker = null;
    }
    if (promoMap) promoMap.setView([-34.5888, -58.3900], 13);
}

export async function searchPromoAddress() {
    const address = document.getElementById('promo-direccion')?.value;
    if (!address) return showToast('Ingresá una dirección para buscar');

    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`;
        const res = await fetch(url);
        const data = await res.json();

        if (data && data.length > 0) {
            const lat = parseFloat(data[0].lat);
            const lng = parseFloat(data[0].lon);

            initPromoMap();
            updatePromoMarker(lat, lng);
            if (promoMap) promoMap.setView([lat, lng], 16);
            showToast('Ubicación encontrada', 'success');
        } else {
            showToast('No se encontró la dirección. Intentá ser más específico.', 'error');
        }
    } catch (err) {
        console.error('Error en geocoding:', err);
        showToast('Error al buscar la dirección', 'error');
    }
}

export async function loadPromotionsAdmin() {
    const tbody = document.getElementById('promotions-admin-table-body');
    if (!tbody) return;

    const rol = localStorage.getItem('rol');
    const isAdmin = rol === 'admin';
    const isStaff = rol === 'staff';

    const thSucursal = document.getElementById('th-promo-sucursal');
    if (thSucursal) {
        thSucursal.style.display = isAdmin ? '' : 'none';
    }

    const colSpan = isAdmin ? 5 : 4;

    const res = await api.get('/admin/promotions');
    if (res.ok) {
        promotionsCache = res.data;
        tbody.innerHTML = res.data.map(p => {
            const branchLabel = p.sucursal ? p.sucursal.replace('AUTOPASS ', '') : 'Global';
            const branchClass = p.sucursal ? 'text-dorado' : 'text-success';

            const toggleControl = isStaff
                ? `<span class="badge ${p.activa ? 'badge-success' : 'badge-danger'}" style="font-size: 0.7rem; padding: 4px 10px; border-radius: 6px;">${p.activa ? 'ACTIVA' : 'INACTIVA'}</span>`
                : `<label class="switch-premium" title="${p.activa ? 'Promoción Activa' : 'Promoción Inactiva'}">
                        <input type="checkbox" ${p.activa ? 'checked' : ''} onchange="togglePromotion(${p.id})">
                        <span class="slider-premium"></span>
                   </label>`;

            const actionCell = isStaff
                ? `<span class="text-xs text-muted font-bold">SOLO LECTURA</span>`
                : `<div class="flex-row gap-8 justify-center actions-reveal">
                        <button class="btn-icon-premium sm btn-edit-promo" onclick="editPromotion(${p.id})" title="Editar">
                            <i class="fas fa-pen"></i>
                        </button>
                        <button class="btn-icon-premium sm danger btn-delete-promo" onclick="deletePromotion(${p.id})" title="Eliminar">
                            <i class="fas fa-xmark"></i>
                        </button>
                   </div>`;

            const typeBadge = p.tipo_canje === 'descuento_reserva'
                ? `<span class="badge" style="font-size:0.55rem;background:rgba(46,204,113,.15);color:#2ecc71;border:1px solid rgba(46,204,113,.3);padding:2px 7px;border-radius:5px;margin-top:4px;"><i class="fas fa-percent"></i> ${p.valor_descuento || 0}% DESC</span>`
                : `<span class="badge" style="font-size:0.55rem;background:rgba(52,152,219,.15);color:#3498db;border:1px solid rgba(52,152,219,.3);padding:2px 7px;border-radius:5px;margin-top:4px;"><i class="fas fa-ticket"></i> VOUCHER</span>`;

            const branchTd = isAdmin ? `
                <td data-label="Sucursal" class="text-center">
                    <span class="text-xs font-bold ${branchClass}">${branchLabel.toUpperCase()}</span>
                </td>` : '';

            return `
            <tr class="row-premium">
                <td data-label="Beneficio">
                    <div class="flex-row items-center gap-10">
                        <div class="header-icon-box xs" style="background: rgba(223, 186, 107, 0.1); border: 1px solid rgba(223, 186, 107, 0.2);">
                            <i class="${p.icono || 'fas fa-gift'} text-dorado" style="font-size: 0.8rem;"></i>
                        </div>
                        <div class="flex-col">
                            <b class="text-white text-small">${p.titulo}</b>
                            <span class="text-xs text-muted" style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${p.descripcion}</span>
                            ${typeBadge}
                        </div>
                    </div>
                </td>
                <td data-label="Puntos" class="text-center">
                    <div class="points-badge-sm mx-auto"><i class="fas fa-star"></i> ${p.costo_puntos}</div>
                </td>
                ${branchTd}
                <td data-label="Estado" class="text-center">
                    ${toggleControl}
                </td>
                <td data-label="Acciones" class="text-center">
                    ${actionCell}
                </td>
            </tr>`;
        }).join('') || `<tr><td colspan="${colSpan}" class="text-center py-20">No hay promociones registradas.</td></tr>`;
    } else {
        tbody.innerHTML = `<tr><td colspan="${colSpan}" class="text-center py-20 text-danger">Error: ${res.error}</td></tr>`;
    }
}

async function _cargarSucursalesPromo(selectedNombre) {
    const rol = localStorage.getItem('rol');
    const field = document.querySelector('.admin-only-field');
    const select = document.getElementById('promo-sucursal');

    if (rol === 'admin') {
        // ADMIN GLOBAL: MOSTRAR CAMPO SUCURSAL
        if (field) field.style.display = 'block';
        if (select) {
            const res = await api.get('/admin/branches');
            if (res.ok) {
                let options = '<option value="">Global (Todas)</option>';
                res.data.forEach(b => {
                    options += `<option value="${b.nombre}">${b.nombre.toUpperCase()}</option>`;
                });
                select.innerHTML = options;
                select.disabled = false;
                select.value = selectedNombre || "";
            }
        }
    } else {
        // ADMIN LOCAL / LOGUEADO POR SUCURSAL: OCULTAR CAMPO SUCURSAL
        const sucursal = localStorage.getItem('sucursal') || '';
        if (field) field.style.display = 'none';
        if (select) {
            select.innerHTML = `<option value="${sucursal}">${sucursal.toUpperCase()}</option>`;
            select.value = sucursal;
            select.disabled = true;
        }
    }
}

export async function showCreatePromotionModal() {
    const rol = localStorage.getItem('rol');
    if (rol === 'staff') return;
    editingPromotionId = null;
    const title = document.getElementById('promo-modal-title');
    if (title) title.textContent = 'NUEVA PROMOCIÓN';

    await _cargarSucursalesPromo("");

    // RESET ICON PICKER
    document.querySelectorAll('.icon-option').forEach(opt => opt.classList.remove('active'));
    const defaultOpt = document.querySelector('.icon-option[data-icon="fas fa-gift"]');
    if (defaultOpt) defaultOpt.classList.add('active');
    document.getElementById('promo-icono').value = 'fas fa-gift';

    // RESET FORMULARIO Y TIPO DE CANJE
    const promoForm = document.getElementById('form-create-promotion');
    if (promoForm) promoForm.reset();
    const tipoCanje = document.getElementById('promo-tipo-canje');
    if (tipoCanje) tipoCanje.value = 'voucher';
    const descField = document.getElementById('promo-descuento-field');
    if (descField) descField.style.display = 'none';
    const descInput = document.getElementById('promo-valor-descuento');
    if (descInput) descInput.value = '';

    // RESET UBICACIÓN Y MAPA
    const promoDir = document.getElementById('promo-direccion');
    if (promoDir) promoDir.value = '';
    const promoLat = document.getElementById('promo-latitude');
    const promoLng = document.getElementById('promo-longitude');
    if (promoLat) promoLat.value = '';
    if (promoLng) promoLng.value = '';

    if (window.openModal) window.openModal('modal-create-promotion');

    setTimeout(() => {
        initPromoMap();
        _resetPromoMap();
    }, 300);
}

export async function editPromotion(id) {
    const rol = localStorage.getItem('rol');
    if (rol === 'staff') return;
    const p = (promotionsCache || []).find(x => x.id === id);
    if (!p) {
        showToast('No se encontró la promoción', 'error');
        return;
    }

    await _cargarSucursalesPromo(p.sucursal || "");

    // RELLENAR CAMPOS CON LOS DATOS ACTUALES
    document.getElementById('promo-titulo').value = p.titulo || '';
    document.getElementById('promo-descripcion').value = p.descripcion || '';
    document.getElementById('promo-costo').value = p.costo_puntos || '';
    document.getElementById('promo-icono').value = p.icono || 'fas fa-gift';
    document.querySelectorAll('.icon-option').forEach(opt => opt.classList.toggle('active', opt.dataset.icon === (p.icono || 'fas fa-gift')));

    const tipoCanje = document.getElementById('promo-tipo-canje');
    if (tipoCanje) tipoCanje.value = p.tipo_canje || 'voucher';
    togglePromoTipoCanje(tipoCanje);
    const descInput = document.getElementById('promo-valor-descuento');
    if (descInput) descInput.value = p.valor_descuento || '';

    const title = document.getElementById('promo-modal-title');
    if (title) title.textContent = 'EDITAR PROMOCIÓN';
    editingPromotionId = id;

    // UBICACIÓN DONDE SE CANJEA
    const promoDir = document.getElementById('promo-direccion');
    if (promoDir) promoDir.value = p.direccion || '';
    const promoLat = document.getElementById('promo-latitude');
    const promoLng = document.getElementById('promo-longitude');
    if (promoLat) promoLat.value = p.latitude || '';
    if (promoLng) promoLng.value = p.longitude || '';

    if (window.openModal) window.openModal('modal-create-promotion');

    setTimeout(() => {
        initPromoMap();
        if (p.latitude && p.longitude) {
            updatePromoMarker(parseFloat(p.latitude), parseFloat(p.longitude));
            if (promoMap) promoMap.setView([parseFloat(p.latitude), parseFloat(p.longitude)], 15);
        } else {
            _resetPromoMap();
        }
    }, 300);
}

export function togglePromoTipoCanje(select) {
    const field = document.getElementById('promo-descuento-field');
    if (field) field.style.display = select && select.value === 'descuento_reserva' ? 'block' : 'none';
}

export function selectPromoIcon(element) {
    document.querySelectorAll('.icon-option').forEach(opt => opt.classList.remove('active'));
    element.classList.add('active');
    document.getElementById('promo-icono').value = element.dataset.icon;
}

export async function handleCreatePromotion() {
    if (localStorage.getItem('rol') === 'staff') return;
    const payload = {
        titulo: document.getElementById('promo-titulo').value,
        descripcion: document.getElementById('promo-descripcion').value,
        costo_puntos: parseInt(document.getElementById('promo-costo').value),
        icono: document.getElementById('promo-icono').value,
        sucursal: document.getElementById('promo-sucursal').value || null,
        tipo_canje: (document.getElementById('promo-tipo-canje') || {}).value || 'voucher',
        valor_descuento: document.getElementById('promo-valor-descuento').value
            ? parseInt(document.getElementById('promo-valor-descuento').value)
            : null,
        direccion: document.getElementById('promo-direccion')?.value || null,
        latitude: document.getElementById('promo-latitude')?.value
            ? parseFloat(document.getElementById('promo-latitude').value)
            : null,
        longitude: document.getElementById('promo-longitude')?.value
            ? parseFloat(document.getElementById('promo-longitude').value)
            : null
    };

    if (editingPromotionId) {
        const res = await api.put(`/admin/promotions/${editingPromotionId}`, payload);
        if (res.ok) {
            showToast('Promoción actualizada', 'success');
            if (window.closeModal) window.closeModal('modal-create-promotion');
            editingPromotionId = null;
            loadPromotionsAdmin();
        } else {
            showToast(res.error || 'Error al actualizar la promoción', 'error');
        }
        return;
    }

    const res = await api.post('/admin/promotions', payload);
    if (res.ok) {
        showToast('Promoción creada', 'success');
        if (window.closeModal) window.closeModal('modal-create-promotion');
        document.getElementById('form-create-promotion').reset();
        loadPromotionsAdmin();
    } else {
        showToast(res.error || 'Error al eliminar la promoción', 'error');
    }
}

export async function togglePromotion(id) {
    if (localStorage.getItem('rol') === 'staff') return;
    const res = await api.post(`/admin/promotions/${id}/toggle`);
    if (res.ok) {
        showToast(res.data.activa ? 'Promoción activada' : 'Promoción desactivada', 'success');
        loadPromotionsAdmin();
    } else {
        showToast(res.error, 'error');
    }
}

export async function deletePromotion(id) {
    if (localStorage.getItem('rol') === 'staff') return;
    if (!await showConfirm('Eliminar Promoción', '¿Estás seguro de eliminar este beneficio permanentemente?')) return;
    const res = await api.delete(`/admin/promotions/${id}`);
    if (res.ok) {
        showToast('Promoción eliminada', 'success');
        loadPromotionsAdmin();
    } else {
        showToast(res.error, 'error');
    }
}
