import * as ui from './modules/dashboard-ui.js';
import * as stats from './modules/dashboard-stats.js';
import * as admin from './modules/dashboard-admin.js';
import * as promos from './modules/dashboard-promotions.js';
import * as baseUi from './modules/ui.js';
import api from './modules/api.js';
import * as utils from './modules/utils.js';
import { initVirtualTime, getVirtualNow } from './modules/virtual-time.js';
const { formatNum } = utils;

/**
 * PUENTE: DASHBOARD.JS
 * MANTIENE LA INTERFAZ OPERATIVA CENTRALIZANDO LA LOGICA MODULAR.
 */

//UI & NAVEGACION
window.switchTab = ui.switchTab;
window.switchMonitorTab = (tabId, element) => {
    //BOTONES
    element.parentElement.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');
    
    //CONTENIDOS & BUSQUEDA CAJAS
    document.querySelectorAll('.monitor-tab-content').forEach(content => content.classList.remove('active'));
    
    const targetTable = document.getElementById(`monitor-tab-${tabId}`);
    const targetSearch = document.getElementById(`search-container-${tabId}`);
    
    if (targetTable) targetTable.classList.add('active');
    if (targetSearch) targetSearch.classList.add('active');
};
window.toggleMobileNav = ui.toggleMobileNav;

//GLOBAL UI MODALS
window.openModal = baseUi.openModal;
window.closeModal = baseUi.closeModal;

// UTILITIES
window.filterTable = utils.filterTable;
window.formatDate = utils.formatDate;

//ADMIN ACTIONS & AJUSTES
window.openBarrier = admin.openBarrier;
window.loadUsers = admin.loadUsers;
window.filterUserList = admin.filterUserList;
window.prevUserPage = admin.prevUserPage;
window.nextUserPage = admin.nextUserPage;
window.toggleBranchSelection = admin.toggleBranchSelection;
window.toggleUserBlock = admin.toggleUserBlock;
window.showCreateUserModal = admin.showCreateUserModal;
window.deleteUserAdmin = admin.deleteUserAdmin;
window.handleAdminCreateUser = admin.handleAdminCreateUser;
window.openPasswordModal = admin.openPasswordModal;
window.handleAdminChangePassword = admin.handleAdminChangePassword;
window.openEditUserModal = admin.openEditUserModal;
window.toggleEditBranchSelection = admin.toggleEditBranchSelection;
window.handleAdminEditUser = admin.handleAdminEditUser;

//AJUSTES & NAVEGACION
window.switchSettingsTab = admin.switchSettingsTab;
window.switchRatesTab = admin.switchRatesTab;
window.refreshSystemDiagnostics = admin.refreshSystemDiagnostics;

// BRANCHES
window.loadBranches = admin.loadBranches;
window.handleCreateBranch = admin.handleCreateBranch;
window.deleteBranch = admin.deleteBranch;
window.toggleBranchHorario = admin.toggleBranchHorario;
window.editBranch = admin.editBranch;
window.showBranchFloors = admin.showBranchFloors;
window.toggleBranch = admin.toggleBranch;
window.previewBranchLogo = admin.previewBranchLogo;
window.clearBranchLogo = admin.clearBranchLogo;
window.searchAddress = admin.searchAddress;

// PROMOTIONS
window.loadPromotionsAdmin = promos.loadPromotionsAdmin;
window.showCreatePromotionModal = promos.showCreatePromotionModal;
window.handleCreatePromotion = promos.handleCreatePromotion;
window.togglePromotion = promos.togglePromotion;
window.deletePromotion = promos.deletePromotion;
window.selectPromoIcon = promos.selectPromoIcon;

window.loadTabData = async (tabId) => {
    switch (tabId) {
        case 'live':
            stats.loadLiveStats();
            stats.loadRecentLogs();
            stats.loadOccupancy();
            break;
        case 'admin-reservations':
            window.loadAdminReservations();
            break;
        case 'users':
            admin.loadUsers();
            break;
        case 'finance':
            window.loadFinanceData();
            break;
        case 'promotions':
            promos.loadPromotionsAdmin();
            break;
        case 'branches':
            admin.loadBranches();
            break;
        case 'settings':
            admin.loadSettings();
            break;
    }
};

window.manualEntry = async () => {
    const plateInput = document.getElementById('manual-plate');
    let plate = plateInput.value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
    let type = document.getElementById('manual-type')?.value || 'Auto';
    const floorId = document.getElementById('manual-floor')?.value;
    
    if (!plate) return utils.showToast('Ingresá una patente');

    // DETECCION AUTOMATICA DE MOTO (FORMATO: 1 LETRA, 3 NUMEROS, 3 LETRAS)
    const isMoto = /^[A-Z]{1}[0-9]{3}[A-Z]{3}$/.test(plate);
    if (isMoto) {
        type = 'Moto';
    }

    // CONFIRMACION MEDIANTE ALERTA PREMIUM (ESTILO UNIFICADO)
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div style="text-transform: uppercase;">
                TIPO: ${isMoto ? 'MOTO' : 'AUTO'}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar el registro?
            </div>
        </div>`
    );
    
    if (!confirmed) return;

    let url = `/admin/manual-entry?plate=${plate}&tipo_vehiculo=${type}`;
    if (floorId) url += `&floor_id=${floorId}`;

    const res = await api.post(url);
    if (res.ok) {
        utils.showToast('Ingreso registrado con éxito', 'success');
        plateInput.value = '';
        stats.loadOccupancy();
        stats.loadLiveStats();
    } else {
        utils.showToast(res.error || 'Error al registrar ingreso', 'error');
    }
};

window.loadAdminReservations = async () => {
    const status = document.getElementById('admin-res-filter-status')?.value || '';
    const res = await api.get(`/admin/reservations?estado=${status}`);
    
    if (res.ok) {
        const tbody = document.getElementById('admin-res-list');
        if (!tbody) return;
        
        // GUARDAMOS GLOBALMENTE PARA CONSULTA DE DETALLE SIN RE-PETICION SI ES NECESARIO
        window.allReservations = res.data;

        tbody.innerHTML = res.data.map(r => `
            <tr class="row-premium">
                <td data-label="Cliente"><div class="user-name">${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}</div></td>
                <td data-label="Patente"><span class="plate-style">${r.patente}</span></td>
                <td data-label="Fecha">
                    <div class="flex-col items-center gap-8">
                        <div class="text-small text-light">${utils.formatDate(r.fecha_inicio)}</div>
                        <div class="text-xs text-muted" style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px;">${utils.formatDate(r.fecha_fin)}</div>
                    </div>
                </td>
                <td data-label="Tipo">
                    <div class="flex-col items-center gap-8">
                        <div class="text-small text-dorado font-bold uppercase" style="letter-spacing: 1px;">${utils.toTitle(r.tipo_estadia)}</div>
                    </div>
                </td>
                <td data-label="Monto" class="text-bold text-white">$${formatNum(r.monto_total)}</td>
                <td data-label="Estado Pago"><span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span></td>
                <td data-label="Estado Reserva"><span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span></td>
                <td data-label="Acciones">
                    <div class="flex-row gap-8 justify-center actions-reveal">
                        <button class="btn-icon-premium sm" onclick="openEditReservationModal(${r.id})" title="Editar Reserva">
                            <i class="fas fa-pen-to-square"></i>
                        </button>
                        <button class="btn-icon-premium sm danger" onclick="cancelReservationAdmin(${r.id})" title="Cancelar Reserva">
                            <i class="fas fa-xmark"></i>
                        </button>
                    </div>
                </td>
            </tr>`).join('') || '<tr><td colspan="8" class="text-center py-20">No hay reservas.</td></tr>';
        
        const statTotal = document.getElementById('admin-res-stat-total');
        const statPending = document.getElementById('admin-res-stat-pending');
        if (statTotal) statTotal.innerText = formatNum(res.data.length);
        if (statPending) statPending.innerText = formatNum(res.data.filter(r => r.estado_reserva === 'Pendiente').length);
    }
};

window.updateEditReservationPrice = async () => {
    const type = document.getElementById('edit-res-tipo').value;
    const resId = document.getElementById('edit-res-id').value;
    const r = window.allReservations?.find(x => x.id == resId);
    if (!r) return;

    let inicio, fin;
    try {
        if (type === 'hora') {
            const fecha = document.getElementById('edit-res-date-only').value;
            const hora = document.getElementById('edit-res-time-only').value;
            const qty = parseInt(document.getElementById('edit-res-hours-qty').value) || 1;
            if (fecha && hora) {
                inicio = new Date(`${fecha}T${hora}`);
                fin = new Date(inicio.getTime() + qty * 3600000);
            }
        } else if (type === 'dia') {
            const fecha = document.getElementById('edit-res-day-only').value;
            if (fecha) {
                inicio = new Date(`${fecha}T00:00`);
                fin = new Date(`${fecha}T23:59`);
            }
        } else if (['semana', 'quincena', 'mes'].includes(type)) {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const startMap = { 'semana': 'edit-res-week-start', 'quincena': 'edit-res-fortnight-start', 'mes': 'edit-res-month-start' };
            const startVal = document.getElementById(startMap[type]).value;
            
            //SI NO HAY FECHA, NO MOSTRAR PRECIO TODAVIA
            if (!startVal) {
                const elMonto = document.getElementById('edit-res-monto-total');
                if (elMonto) elMonto.innerText = `$ ---`;
                return;
            }

            inicio = new Date(startVal.replace(/-/g, "/"));
            fin = new Date(inicio.getTime() + (periods[type] - 1) * 24 * 60 * 60 * 1000);
            fin.setHours(23, 59, 59);
        } else {
            const sVal = document.getElementById('edit-res-inicio').value;
            const fVal = document.getElementById('edit-res-fin').value;
            if (sVal && fVal) {
                inicio = new Date(sVal);
                fin = new Date(fVal);
            }
        }

        if (inicio && fin && !isNaN(inicio.getTime()) && !isNaN(fin.getTime())) {
            // LOGICA ESPECIFICA: PARA 'HORA', SOLO MOSTRAR SI HAY CANTIDAD DE HORAS VALIDA
            if (type === 'hora') {
                const qty = parseInt(document.getElementById('edit-res-hours-qty').value);
                if (isNaN(qty) || qty <= 0) {
                    const elMonto = document.getElementById('edit-res-monto-total');
                    if (elMonto) elMonto.innerText = `$ ---`;
                    return;
                }
            }

            const durationHours = (fin - inicio) / 3600000;
            
            // USAR API PARA OBTENER TARIFAS ACTUALIZADAS DE LA SUCURSAL
            const resRates = await api.get(`/admin/branches`);
            let rates = { hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };
            
            if (resRates.ok && Array.isArray(resRates.data)) {
                const branch = resRates.data.find(b => b.nombre.trim() === r.sucursal_nombre.trim());
                if (branch) {
                    rates = {
                        hora: branch.tarifa_hora || 1500,
                        dia: branch.tarifa_dia || 15000,
                        semana: branch.tarifa_semana || 70000,
                        quincena: branch.tarifa_quincena || 120000,
                        mes: branch.tarifa_mes || 200000
                    };
                }
            }

            let total = 0;
            if (type === 'hora') total = Math.ceil(durationHours) * rates.hora;
            else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rates.dia;
            else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rates.semana;
            else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rates.quincena;
            else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rates.mes;
            else total = Math.ceil(durationHours) * rates.hora;

            const elMonto = document.getElementById('edit-res-monto-total');
            if (elMonto) elMonto.innerText = `$ ${formatNum(total)}`;
        } else {
            const elMonto = document.getElementById('edit-res-monto-total');
            if (elMonto) elMonto.innerText = `$ ---`;
        }
    } catch (e) { 
        console.error("Error recalc price:", e);
        const elMonto = document.getElementById('edit-res-monto-total');
        if (elMonto) elMonto.innerText = `$ 0`;
    }
};

window.updateEditFormGroups = (type) => {
    const sections = {
        'hora': document.getElementById('edit-hourly-fields'),
        'dia': document.getElementById('edit-daily-fields'),
        'semana': document.getElementById('edit-weekly-fields'),
        'quincena': document.getElementById('edit-fortnight-fields'),
        'mes': document.getElementById('edit-month-fields'),
        'standard': document.getElementById('edit-standard-fields')
    };

    Object.values(sections).forEach(s => { if(s) s.style.display = 'none'; });
    const activeSection = sections[type] || sections['standard'];
    if (activeSection) {
        // USAR EL ATRIBUTO DATA-DISPLAY SI EXISTE, SINO GRID POR DEFECTO
        activeSection.style.display = activeSection.dataset.display || 'grid';
    }
    window.updateEditReservationPrice();
};

const updateEditPeriodEnd = (startDateStr, days, targetSelector) => {
    if (!startDateStr) return;
    const endInput = document.querySelector(targetSelector);
    if (!endInput) return;
    
    const start = new Date(startDateStr.replace(/-/g, "/"));
    const end = new Date(start.getTime() + (days - 1) * 24 * 60 * 60 * 1000);
    const day = end.getDate().toString().padStart(2, '0');
    const month = (end.getMonth() + 1).toString().padStart(2, '0');
    const year = end.getFullYear().toString().slice(-2);
    endInput.value = `${day}-${month}-${year} 23:59`;
    window.updateEditReservationPrice();
};

window.openEditReservationModal = (resId) => {
    const r = window.allReservations?.find(x => x.id === resId);
    if (!r) return;

    // INICIALIZAR FLATPICKRS SI ES NECESARIO
    if (window.flatpickr && !window.editPickersInitialized) {
        const now = getVirtualNow();
        const maxDate = new Date(now.getFullYear(), now.getMonth() + 3, now.getDate());
        const common = { 
            disableMobile: "true", 
            altInput: true,
            altFormat: "d-m-y",
            dateFormat: "Y-m-d",
            minDate: "today",
            maxDate: maxDate,
            defaultDate: now,
            onChange: () => window.updateEditReservationPrice() 
        };
        flatpickr("#edit-res-date-only", common);
        flatpickr("#edit-res-day-only", common);
        flatpickr("#edit-res-time-only", { 
            enableTime: true, 
            noCalendar: true, 
            dateFormat: "H:i",
            defaultDate: now,
            disableMobile: "true",
            onChange: () => window.updateEditReservationPrice() 
        });
        flatpickr("#edit-res-week-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 7, '#edit-res-week-end') });
        flatpickr("#edit-res-fortnight-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 15, '#edit-res-fortnight-end') });
        flatpickr("#edit-res-month-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 30, '#edit-res-month-end') });
        
        // CALCULAR FECHAS DE FIN PARA PERIODOS CON LA FECHA POR DEFECTO
        const todayYmd = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
        updateEditPeriodEnd(todayYmd, 7, '#edit-res-week-end');
        updateEditPeriodEnd(todayYmd, 15, '#edit-res-fortnight-end');
        updateEditPeriodEnd(todayYmd, 30, '#edit-res-month-end');
        
        document.getElementById('edit-res-hours-qty')?.addEventListener('input', () => window.updateEditReservationPrice());
        
        // FLECHAS CUSTOM PARA CANTIDAD DE HORAS (ADMIN)
        const editQtyWrapper = document.querySelector('#edit-hourly-fields .num-input-wrapper');
        if (editQtyWrapper) {
            const inp = editQtyWrapper.querySelector('#edit-res-hours-qty');
            const up = editQtyWrapper.querySelector('.num-btn.up');
            const down = editQtyWrapper.querySelector('.num-btn.down');
            if (inp && up) up.addEventListener('click', () => {
                const max = parseInt(inp.max) || 24;
                const val = parseInt(inp.value) || 0;
                if (val < max) { inp.value = val + 1; inp.dispatchEvent(new Event('input', { bubbles: true })); }
            });
            if (inp && down) down.addEventListener('click', () => {
                const min = parseInt(inp.min) || 1;
                const val = parseInt(inp.value) || 0;
                if (val > min) { inp.value = val - 1; inp.dispatchEvent(new Event('input', { bubbles: true })); }
            });
        }
        
        window.editPickersInitialized = true;
    }

    document.getElementById('edit-res-id').value = r.id;
    document.getElementById('edit-res-sucursal').value = r.sucursal_nombre || '';
    document.getElementById('edit-res-title').innerText = `EDITAR RESERVA #${r.id}`;
    document.getElementById('edit-res-patente').value = r.patente;
    document.getElementById('edit-res-tipo').value = r.tipo_estadia;
    document.getElementById('edit-res-pago').value = r.estado_pago;
    document.getElementById('edit-res-reserva').value = r.estado_reserva;

    window.updateEditFormGroups(r.tipo_estadia);

    // POBLAR CAMPOS DINAMICOS
    const startParts = r.fecha_inicio.split(' ');
    const dateOnly = startParts[0];
    const timeOnly = startParts[1] ? startParts[1].substring(0, 5) : "00:00";

    if (r.tipo_estadia === 'hora') {
        document.getElementById('edit-res-date-only').value = dateOnly;
        document.getElementById('edit-res-time-only').value = timeOnly;
        const s = new Date(r.fecha_inicio.replace(/-/g, "/"));
        const e = new Date(r.fecha_fin.replace(/-/g, "/"));
        const hours = Math.ceil((e - s) / 3600000);
        document.getElementById('edit-res-hours-qty').value = hours || 1;
    } else if (r.tipo_estadia === 'dia') {
        document.getElementById('edit-res-day-only').value = dateOnly;
    } else if (r.tipo_estadia === 'semana') {
        document.getElementById('edit-res-week-start').value = dateOnly;
        updateEditPeriodEnd(dateOnly, 7, '#edit-res-week-end');
    } else if (r.tipo_estadia === 'quincena') {
        document.getElementById('edit-res-fortnight-start').value = dateOnly;
        updateEditPeriodEnd(dateOnly, 15, '#edit-res-fortnight-end');
    } else if (r.tipo_estadia === 'mes') {
        document.getElementById('edit-res-month-start').value = dateOnly;
        updateEditPeriodEnd(dateOnly, 30, '#edit-res-month-end');
    } else {
        const formatForInput = (dateStr) => {
            if (!dateStr) return '';
            const d = new Date(dateStr.replace(/-/g, "/"));
            if (isNaN(d.getTime())) return dateStr.replace(' ', 'T').substring(0, 16);
            return d.toISOString().substring(0, 16);
        };
        document.getElementById('edit-res-inicio').value = formatForInput(r.fecha_inicio);
        document.getElementById('edit-res-fin').value = formatForInput(r.fecha_fin);
    }

    const elMonto = document.getElementById('edit-res-monto-total');
    if (elMonto) elMonto.innerText = `$ ${formatNum(r.monto_total)}`;

    if (window.openModal) window.openModal('modal-edit-reservation');
};

window.handleAdminEditReservation = async (event) => {
    event.preventDefault();
    const resId = document.getElementById('edit-res-id').value;
    const btn = event.target.querySelector('button[type="submit"]');
    const tipo = document.getElementById('edit-res-tipo').value;

    let inicio, fin;
    try {
        if (tipo === 'hora') {
            const fecha = document.getElementById('edit-res-date-only').value;
            const hora = document.getElementById('edit-res-time-only').value;
            const qty = parseInt(document.getElementById('edit-res-hours-qty').value) || 1;
            if (!fecha || !hora) throw new Error("Seleccioná fecha y hora");
            inicio = `${fecha} ${hora}`;
            const s = new Date(`${fecha}T${hora}`);
            const f = new Date(s.getTime() + qty * 3600000);
            fin = `${f.getFullYear()}-${(f.getMonth()+1).toString().padStart(2,'0')}-${f.getDate().toString().padStart(2,'0')} ${f.getHours().toString().padStart(2,'0')}:${f.getMinutes().toString().padStart(2,'0')}`;
        } else if (tipo === 'dia') {
            const fecha = document.getElementById('edit-res-day-only').value;
            if (!fecha) throw new Error("Seleccioná un día");
            inicio = `${fecha} 00:00`;
            fin = `${fecha} 23:59`;
        } else if (['semana', 'quincena', 'mes'].includes(tipo)) {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const startMap = { 'semana': 'edit-res-week-start', 'quincena': 'edit-res-fortnight-start', 'mes': 'edit-res-month-start' };
            const startVal = document.getElementById(startMap[tipo]).value;
            if (!startVal) throw new Error("Seleccioná fecha de inicio");
            inicio = `${startVal} 00:00`;
            const s = new Date(startVal.replace(/-/g, "/"));
            const f = new Date(s.getTime() + (periods[tipo] - 1) * 24 * 60 * 60 * 1000);
            fin = `${f.getFullYear()}-${(f.getMonth()+1).toString().padStart(2,'0')}-${f.getDate().toString().padStart(2,'0')} 23:59`;
        } else {
            inicio = document.getElementById('edit-res-inicio').value.replace('T', ' ');
            fin = document.getElementById('edit-res-fin').value.replace('T', ' ');
        }
    } catch (e) {
        return utils.showToast(e.message);
    }

    const payload = {
        patente: document.getElementById('edit-res-patente').value.toUpperCase(),
        tipo_estadia: tipo,
        fecha_inicio: inicio,
        fecha_fin: fin,
        estado_pago: document.getElementById('edit-res-pago').value,
        estado_reserva: document.getElementById('edit-res-reserva').value
    };

    // VERIFICAR DISPONIBILIDAD
    const sucursal = document.getElementById('edit-res-sucursal')?.value;
    if (sucursal) {
        const av = await api.get('/user/reservations/check-availability', {
            params: {
                sucursal_nombre: sucursal,
                fecha_inicio: inicio,
                fecha_fin: fin,
                exclude_id: parseInt(resId) || undefined
            }
        });
        if (av.ok && av.data && !av.data.disponible) {
            btn.disabled = false;
            return utils.showToast(av.data.mensaje || 'No hay disponibilidad para el horario solicitado.');
        }
    }

    btn.disabled = true;
    const res = await api.patch(`/admin/reservations/${resId}`, payload);
    if (res.ok) {
        utils.showToast('Reserva actualizada correctamente');
        if (window.closeModal) window.closeModal('modal-edit-reservation');
        window.loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al actualizar reserva');
    }
    btn.disabled = false;
};

window.cancelReservationAdmin = async (resId) => {
    if (!await utils.showConfirm('Cancelar Reserva', '¿Estás seguro de cancelar esta reserva?')) return;
    
    const res = await api.post(`/admin/reservations/${resId}/cancel`);
    if (res.ok) {
        utils.showToast(res.data.message || 'Reserva cancelada');
        window.loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al cancelar reserva');
    }
};

window.showReservationDetail = (resId) => {
    const r = window.allReservations?.find(x => x.id === resId);
    if (!r) return;

    document.getElementById('res-detail-id').innerText = `#${r.id}`;
    document.getElementById('res-detail-user').innerText = `${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}`;
    document.getElementById('res-detail-plate').innerText = r.patente;
    document.getElementById('res-detail-start').innerText = utils.formatDate(r.fecha_inicio);
    document.getElementById('res-detail-end').innerText = utils.formatDate(r.fecha_fin);
    document.getElementById('res-detail-sucursal').innerText = r.sucursal_nombre;
    document.getElementById('res-detail-type').innerText = utils.toTitle(r.tipo_estadia);
    document.getElementById('res-detail-amount').innerText = `$${formatNum(r.monto_total)}`;

    const badgeContainer = document.getElementById('res-detail-status-badges');
    badgeContainer.innerHTML = `
        <span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span>
        <span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span>
    `;

    if (window.openModal) window.openModal('modal-res-detail');
};

window.showLogDetail = async (logId) => {
    // SI NO TENEMOS LOS LOGS CARGADOS O NECESITAMOS REFRESCAR, PEDIMOS
    const res = await api.get('/reports/access');
    if (!res.ok) return;
    
    const log = res.data.find(l => l.id === logId);
    if (!log) return;

    document.getElementById('audit-plate').innerText = log.patente_detectada;
    document.getElementById('audit-plate-overlay').innerText = log.patente_detectada;
    const d = new Date(log.fecha_hora);
    document.getElementById('audit-time').innerText = `${String(d.getDate()).padStart(2,'0')}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getFullYear()).slice(-2)} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    document.getElementById('audit-type').innerText = log.tipo_evento;
    document.getElementById('audit-payment').innerText = log.pago_confirmado ? 'PAGADO' : 'PENDIENTE';
    document.getElementById('audit-res-id').innerText = log.reserva_id ? `#${log.reserva_id}` : 'SIN RESERVA';

    const imgEl = document.getElementById('audit-image');
    if (imgEl) {
        imgEl.src = `/v1/system/capture/${logId}?t=${Date.now()}`;
        //OCULTAR OVERLAY SI NO HAY CAPTURA REAL
        document.getElementById('audit-overlay-container').style.display = 'block';
    }
    
    if (window.openModal) window.openModal('modal-log-detail');
};

let revenueChart = null;
let currentFinancePage = 1;
const financeLimit = 15;

window.toggleFinanceDateFilter = () => {
    const period = document.getElementById('fin-period').value;
    const dateGroup = document.getElementById('fin-date-group');
    const dateInput = document.getElementById('fin-date');
    
    if (period === 'specific') {
        dateGroup.style.display = 'flex';
        if (!dateInput.value) {
            dateInput.value = getVirtualNow().toISOString().split('T')[0];
        }
    } else {
        dateGroup.style.display = 'none';
    }
    window.loadFinanceData();
};

window.loadFinanceData = async (resetPage = true) => {
    if (resetPage) currentFinancePage = 1;
    const period = document.getElementById('fin-period')?.value || 'month';
    const specificDate = document.getElementById('fin-date')?.value;
    const vehicleType = document.getElementById('fin-vehicle-type')?.value || 'all';
    const paymentMethod = document.getElementById('fin-payment-method')?.value || 'all';
    
    let urlParams = `period=${period}&vehicle_type=${vehicleType}&payment_method=${paymentMethod}`;
    if (period === 'specific' && specificDate) {
        urlParams = `period=day&start=${specificDate}T00:00:00&end=${specificDate}T23:59:59&vehicle_type=${vehicleType}&payment_method=${paymentMethod}`;
    }
    
    // 1. CARGAR RESUMEN (KPIS)
    const resSum = await api.get(`/reports/financial-summary?${urlParams}`);
    if (resSum.ok) {
        const data = resSum.data;
        const elTotal = document.getElementById('fin-total');
        const elRefund = document.getElementById('fin-refunded');
        const elCount = document.getElementById('fin-count');
        const elAvg = document.getElementById('fin-avg');

        if (elTotal) elTotal.innerText = `$${formatNum(data.total_recaudado)}`;
        if (elRefund) elRefund.innerText = `$${formatNum(data.total_reembolsado)}`;
        if (elCount) elCount.innerText = formatNum(data.cantidad_pagos);
        if (elAvg) elAvg.innerText = `$${formatNum(data.ticket_promedio)}`;

        const elProy = document.getElementById('fin-proyectado');
        if (elProy) elProy.innerText = `$${formatNum(data.ingresos_proyectados)}`;

        const elCancel = document.getElementById('fin-cancel-rate');
        if (elCancel) elCancel.innerText = `${data.tasa_cancelacion || 0}%`;

        const elNoShow = document.getElementById('fin-noshow');
        if (elNoShow) elNoShow.innerText = `$${formatNum(data.ingresos_incumplimiento || 0)}`;

        // DESGLOSE POR CANAL
        const d = data.desglose;
        if (d) {
            document.getElementById('fin-stay-monto').innerText = `$${formatNum(d.estadias?.monto || 0)}`;
            document.getElementById('fin-stay-count').innerText = formatNum(d.estadias?.cantidad || 0);
            document.getElementById('fin-stay-avg').innerText = `$${formatNum(d.estadias?.promedio || 0)}`;

            document.getElementById('fin-res-monto').innerText = `$${formatNum(d.reservas?.monto || 0)}`;
            document.getElementById('fin-res-count').innerText = formatNum(d.reservas?.cantidad || 0);
            document.getElementById('fin-res-avg').innerText = `$${formatNum(d.reservas?.promedio || 0)}`;
        }
    }

    // 2. CARGAR HISTORIAL DE PAGOS (PAGINADO)
    const resHist = await api.get(`/reports/payment-history?${urlParams}&page=${currentFinancePage}&limit=${financeLimit}`);
    if (resHist.ok) {
        const tbody = document.getElementById('payment-list');
        if (tbody) {
            tbody.innerHTML = resHist.data.map(p => {
                const isRefund = p.tipo === 'Reembolso';
                const rowClass = isRefund ? 'row-refund' : '';
                const amountClass = isRefund ? 'text-danger' : 'text-secondary';
                const badgeClass = isRefund ? 'badge-danger-light' : 'badge-success-light';
                
                let metodoPago = 'PAGO DIGITAL';
                if (p.metodo === 'CAJA') {
                    metodoPago = 'PAGO EN CAJA';
                }

                return `
                <tr class="${rowClass}">
                    <td><span class="text-light">${utils.formatDate(p.fecha_pago)}</span></td>
                    <td><span class="plate-style">${p.patente_detectada}</span>${isRefund ? ' <i class="fas fa-undo text-xs"></i>' : ''}</td>
                    <td class="text-bold ${amountClass}">$${formatNum(p.costo_estadia)}</td>
                    <td><span class="text-small">${metodoPago}</span></td>
                    <td><span class="${badgeClass}">${p.tipo.toUpperCase()}</span></td>
                </tr>
            `}).join('') || '<tr><td colspan="5" class="text-center py-20">No hay transacciones en este período.</td></tr>';
        }

        //3. ACTUALIZAR UI PAGINACION
        const prevBtn = document.getElementById('prev-fin-btn');
        const nextBtn = document.getElementById('next-fin-btn');
        const pageInfo = document.getElementById('fin-page-info');

        if (prevBtn) prevBtn.disabled = currentFinancePage === 1;
        if (nextBtn) nextBtn.disabled = resHist.data.length < financeLimit;
        if (pageInfo) pageInfo.innerText = `Página ${currentFinancePage}`;

        // 4. RENDERIZAR GRAFICO CON EL TOTAL DE TRANSACCIONES (SIN PAGINACION) PARA MOSTRAR LA TENDENCIA REAL
        const resChart = await api.get(`/reports/payment-history?${urlParams}&limit=0`);
        if (resChart.ok) {
            renderRevenueChart(resChart.data, period);
        }
    }
};

window.nextFinancePage = () => {
    currentFinancePage++;
    window.loadFinanceData(false);
};

window.prevFinancePage = () => {
    if (currentFinancePage > 1) {
        currentFinancePage--;
        window.loadFinanceData(false);
    }
};

function renderRevenueChart(data, period) {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (revenueChart) {
        revenueChart.destroy();
        revenueChart = null;
    }

    // SI NO HAY DATOS, MOSTRAR MENSAJE O GRAFICO VACIO LIMPIO
    if (!data || data.length === 0) {
        // OPCIONAL: MOSTRAR UN MENSAJE EN EL CANVAS O SIMPLEMENTE UN GRAFICO VACIO
        console.warn("No hay datos para el gráfico financiero");
    }

    // AGRUPAR Y PROCESAR DATOS CRONOLOGICAMENTE
    const grouped = {};
    
    // FUNCION AUXILIAR PARA PARSEAR FECHAS DE FORMA SEGURA
    const parseDate = (str) => {
        if (!str) return new Date(NaN);
        // NORMALIZAR FORMATO: REEMPLAZA ESPACIOS POR T SI ES NECESARIO (PARA SAFARI/OTROS)
        return new Date(str.replace(' ', 'T'));
    };

    // CLONAMOS Y ORDENAMOS CRONOLOGICAMENTE (ANTIGUO A NUEVO)
    const sortedData = [...data].sort((a, b) => parseDate(a.fecha_pago) - parseDate(b.fecha_pago));

    sortedData.forEach(p => {
        const date = parseDate(p.fecha_pago);
        if (isNaN(date.getTime())) return;

        let label;
        if (period === 'day' || period === 'specific') {
            label = date.getHours() + ':00';
        } else if (period === 'week' || period === 'month') {
            label = date.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' });
        } else {
            label = date.toLocaleDateString('es-AR', { month: 'short' });
        }
        
        const monto = parseFloat(p.costo_estadia) || 0;
        grouped[label] = (grouped[label] || 0) + monto;
    });

    const labels = Object.keys(grouped);
    const values = Object.values(grouped);

    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.length > 0 ? labels : ['Sin datos'],
            datasets: [{
                label: 'Ingresos',
                data: values.length > 0 ? values : [0],
                borderColor: '#C5A059',
                backgroundColor: 'rgba(197, 160, 89, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#C5A059',
                pointBorderColor: '#000',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0a0a0a',
                    titleColor: '#C5A059',
                    bodyColor: '#fff',
                    borderColor: 'rgba(197, 160, 89, 0.3)',
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        label: (context) => {
                            const val = context.parsed.y || 0;
                            return ` Recaudado: $${formatNum(val)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { 
                        color: '#666',
                        font: { size: 10 },
                        callback: (value) => '$' + formatNum(value)
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#666', font: { size: 10 } }
                }
            }
        }
    });
}

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
    // 1. ACTUALIZAR INMEDIATAMENTE LA UI CON LO QUE TENGAMOS EN LOCALSTORAGE
    const rol = localStorage.getItem('rol');
    const sucursalRaw = localStorage.getItem('sucursal');
    
    // LIMPIEZA PROFUNDA DE LA SEDE
    let sucursalLimpia = '';
    if (sucursalRaw && sucursalRaw !== 'null' && sucursalRaw !== 'undefined') {
        sucursalLimpia = sucursalRaw.replace('AUTOPASS ', '').trim();
    }
    
    // LA CLASE DE ROL YA SE APLICA EN EL INLINE SCRIPT DE DASHBOARD.HTML PARA EVITAR FLICKER
    
    const roleNameEl = document.getElementById('role-name');
    const settingsTitleEl = document.getElementById('settings-title');

    if (roleNameEl) {
        let label = 'Personal Autorizado';
        if (rol === 'admin') label = 'Administrador Global';
        else if (rol === 'local_admin') label = `Administrador ${sucursalLimpia || 'Sucursal'}`;
        else if (rol === 'staff') label = `Empleado ${sucursalLimpia || 'Sucursal'}`;
        roleNameEl.innerText = label;
    }

    if (settingsTitleEl) {
        settingsTitleEl.innerText = 'CONFIGURACIÓN';
    }

    // 2. INICIAR SERVICIOS SECUNDARIOS
    try {
        await initVirtualTime();
        ui.initClock();
        ui.checkSystemHealth();
        // INICIAR WEBSOCKET DE AFORO
        stats.initOccupancyWS();
    } catch (e) { console.warn("Error en servicios UI:", e); }

    let lastTab = localStorage.getItem('activeAdminTab') || 'live';
    
    // REGLAS DE REDIRECCION POR ROL
    const restrictedStaff = ['users', 'finance', 'promotions', 'settings'];
    const restrictedAdmin = ['live', 'admin-reservations', 'finance', 'settings']; 

    if (rol === 'staff' && restrictedStaff.includes(lastTab)) {
        lastTab = 'live';
    } else if (rol === 'admin' && restrictedAdmin.includes(lastTab)) {
        lastTab = 'users'; 
    }

    const activeItem = document.querySelector(`.nav-item[onclick*="'${lastTab}'"]`);
    if (activeItem) ui.switchTab(lastTab, activeItem);

    // 3. LISTENERS DE FORMULARIOS
    document.getElementById('form-add-branch')?.addEventListener('submit', window.handleCreateBranch);
});

window.payOccupancy = async (plate, amount) => {
    // CONFIRMACION MEDIANTE ALERTA PREMIUM (ESTILO UNIFICADO)
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div>
                MONTO: $${formatNum(amount || 0)}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar el pago?
            </div>
        </div>`
    );

    if (!confirmed) return;

    const res = await api.post(`/access/pay-stay?plate=${plate}`);
    if (res.ok) { 
        utils.showToast('Pago procesado'); 
        stats.loadOccupancy(); 
        stats.loadLiveStats();
        if (document.getElementById('tab-finance').style.display !== 'none') {
            window.loadFinanceData();
        }
    }
    else utils.showToast(res.error);
};

window.cancelStay = stats.cancelStay;

window.manualExit = async (plate, type) => {
    // CONFIRMACION MEDIANTE ALERTA PREMIUM (ESTILO UNIFICADO)
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div style="text-transform: uppercase;">
                TIPO: ${type || 'AUTO'}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar la salida?
            </div>
        </div>`
    );

    if (!confirmed) return;
    
    const res = await api.post(`/admin/manual-exit?plate=${plate}`);
    if (res.ok) { 
        utils.showToast('Salida registrada'); 
        stats.loadOccupancy(); 
        stats.loadLiveStats();
    }
    else utils.showToast(res.error);
};

window.createBranch = admin.handleCreateBranch;
window.showCreateBranchModal = admin.showCreateBranchModal;
window.loadSettings = admin.loadSettings;
window.saveAllRates = admin.saveAllRates;
window.toggleRateEdit = admin.toggleRateEdit;
window.saveRateGroup = admin.saveRateGroup;
window.saveCapacities = admin.saveCapacities;
window.saveSystemParam = admin.saveSystemParam;
window.resetSys = admin.resetSys;
window.exportFinanceData = admin.exportFinanceData;

// FLOORS
window.openAddFloorModal = admin.openAddFloorModal;
window.openEditFloorModal = admin.openEditFloorModal;
window.handleCreateFloor = admin.handleCreateFloor;
window.deleteFloor = admin.deleteFloor;
window.updatePBCapacity = admin.updatePBCapacity;
window.savePBCapacity = admin.savePBCapacity;
window.toggleLevelEdit = admin.toggleLevelEdit;

// CAMERAS
window.loadCameraSettings = ui.loadCameraSettings;
window.showCreateCameraModal = ui.showCreateCameraModal;
window.showEditCameraModal = ui.showEditCameraModal;
window.handleSaveCameraConfig = ui.handleSaveCameraConfig;
window.deleteCamera = ui.deleteCamera;
window.toggleDynamicCameraService = ui.toggleDynamicCameraService;


