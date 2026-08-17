import api from './api.js';
import { showToast, showConfirm, formatDate, formatPlate, formatNum } from './utils.js';
import { getVirtualNow } from './virtual-time.js';
import { loadFloors } from './dashboard-admin-branches.js';

/**
 * Módulo de Ajustes de Sistema, Tarifas, Diagnósticos, Barreras y Exportación
 */

export async function openBarrier(gateId, command = 'OPEN') {
    const actionText = command === 'CLOSE' ? 'Cerrar' : 'Abrir';
    const confirmed = await showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-secondary" style="letter-spacing: 1px; text-transform: uppercase;">
                BARRERA ${gateId}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Desea ${actionText.toLowerCase()} la barrera?
            </div>
        </div>`
    );
    if (!confirmed) return;

    const iconId = gateId === 'ENTRADA' ? 'icon-barrier-entry' : 'icon-barrier-exit';
    const iconEl = document.getElementById(iconId);
    if (iconEl) iconEl.src = command === 'CLOSE' ? '/static/images/barrera baja.png' : '/static/images/barrera alta.png';

    const res = await api.post(`/admin/open-barrier?gate_id=${gateId}&command=${command}`);
    if (res && res.ok) {
        showToast(`Barrera ${gateId} -> Comando: ${actionText}`, 'success');
        if (command === 'OPEN') {
            setTimeout(() => { if (iconEl) iconEl.src = '/static/images/barrera baja.png'; }, 5000);
        }
    } else {
        showToast(`Error: ${res?.error || 'Desconocido'}`, 'error');
        if (iconEl) iconEl.src = '/static/images/barrera baja.png';
    }
}

export async function refreshSystemDiagnostics() {
    try {
        const res = await api.get('/system/health');
        if (!res.ok) throw new Error("Health check failed");

        const data = res.data;
        const sucursal = (localStorage.getItem('sucursal') || '').replace('AUTOPASS ', '').toUpperCase().trim();

        const updateDot = (id, status) => {
            const dot = document.getElementById(`diag-${id}-dot`);
            if (!dot) return;
            dot.className = status === 'ONLINE' ? 'status-dot-mini online' : 'status-dot-mini offline';
        };

        updateDot('api', data.api);
        updateDot('db', data.database);
        updateDot('barrera-entrada', data.api);
        updateDot('barrera-salida', data.api);

        const updateALPRDot = (type, status) => {
            const dot = document.getElementById(`diag-cam-${type}-dot`);
            if (!dot) return;
            dot.className = status === 'ONLINE' ? 'status-dot-mini online' : 'status-dot-mini offline';
        };

        const entryKey = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA';
        const exitKey = sucursal ? `${sucursal}_SALIDA` : 'SALIDA';

        updateALPRDot('entrada', data.alpr[entryKey] || 'OFFLINE');
        updateALPRDot('salida', data.alpr[exitKey] || 'OFFLINE');

        const overall = document.getElementById('sys-overall-status');
        if (overall) {
            const allOk = data.api === 'ONLINE' && data.database === 'ONLINE';
            overall.innerText = allOk ? 'ESTABLE' : 'ALERTA';
            overall.className = `badge-status ${allOk ? 'badge-success-light' : 'badge-danger-light'}`;
        }
    } catch (err) {
        console.warn("Error en diagnóstico:", err);
    }
}

export async function loadSettings() {
    const res = await api.get('/admin/settings');
    if (res.ok) {
        const cfg = res.data;
        Object.keys(cfg).forEach(key => {
            const el = document.getElementById(`cfg-${key}`);
            if (el) el.value = cfg[key];
        });
        loadFloors();
        refreshSystemDiagnostics();
    }
}

export function switchSettingsTab(tabId, btn) {
    document.querySelectorAll('.settings-section').forEach(s => s.style.display = 'none');
    const target = document.getElementById(`set-section-${tabId}`);
    if (target) target.style.display = 'block';

    document.querySelectorAll('.btn-tab-mini').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    if (tabId === 'monitoring' && window.loadCameraSettings) {
        window.loadCameraSettings();
    }
}

export function switchRatesTab(type, btn) {
    document.querySelectorAll('.rate-group').forEach(g => g.style.display = 'none');
    const target = document.getElementById(`rate-group-${type}`);
    if (target) target.style.display = 'block';

    document.querySelectorAll('.btn-tab-sub').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
}

export async function saveAllRates() {
    const keys = [
        'precio_hora', 'precio_dia', 'precio_semana', 'precio_mes',
        'precio_hora_moto', 'precio_dia_moto', 'precio_semana_moto', 'precio_mes_moto',
        'precio_hora_camioneta', 'precio_dia_camioneta', 'precio_semana_camioneta', 'precio_mes_camioneta'
    ];
    
    const labels = {
        'precio_hora': 'Hora', 'precio_dia': 'Día', 'precio_semana': 'Semana', 'precio_mes': 'Mes',
        'precio_hora_moto': 'Hora', 'precio_dia_moto': 'Día', 'precio_semana_moto': 'Semana', 'precio_mes_moto': 'Mes',
        'precio_hora_camioneta': 'Hora', 'precio_dia_camioneta': 'Día', 'precio_semana_camioneta': 'Semana', 'precio_mes_camioneta': 'Mes'
    };

    let summary = '<div style="text-align: left; margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; max-height: 200px; overflow-y: auto;">';
    keys.forEach(key => {
        const val = document.getElementById(`cfg-${key}`)?.value || 0;
        summary += `<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #fff; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">${labels[key]}:</span>
                        <b style="color: var(--dorado); font-size: 0.75rem;">$${formatNum(parseFloat(val))}</b>
                    </div>`;
    });
    summary += '</div>';

    if (!await showConfirm('Confirmar Tarifario', summary)) return;

    let success = true;
    for (const key of keys) {
        const input = document.getElementById(`cfg-${key}`);
        if (!input) continue;
        const val = parseFloat(input.value) || 0;
        const res = await api.post(`/admin/settings/prices?clave=${key}&valor=${val}`);
        if (!res.ok) success = false;
    }

    if (success) {
        showToast('Tarifas actualizadas correctamente.', 'success');
        document.querySelectorAll('.rate-group').forEach(g => {
            g.classList.remove('editing');
            g.querySelectorAll('input').forEach(i => i.disabled = true);
        });
        document.querySelectorAll('[id^="btn-save-rates-"]').forEach(b => b.style.display = 'none');
        document.querySelectorAll('[id^="btn-edit-rates-"]').forEach(b => b.style.display = 'inline-flex');
    } else {
        showToast('Error al actualizar algunas tarifas.', 'error');
    }
}

export function toggleRateEdit(type) {
    const group = document.getElementById(`rate-group-${type}`);
    const btn = document.getElementById(`btn-edit-rates-${type}`);
    if (!group || !btn) return;
    const inputs = group.querySelectorAll('input');

    const isEditing = group.classList.contains('editing');

    if (!isEditing) {
        inputs.forEach(input => input.disabled = false);
        group.classList.add('editing');
        btn.innerHTML = '<i class="fas fa-check mr-8"></i> APLICAR';
        btn.style.borderColor = '#4CAF50';
        btn.style.color = '#4CAF50';
        if (inputs.length > 0) inputs[0].focus();
    } else {
        saveRateGroup(type);
    }
}

export async function saveRateGroup(type) {
    const group = document.getElementById(`rate-group-${type}`);
    const btn = document.getElementById(`btn-edit-rates-${type}`);
    if (!group || !btn) return;
    const inputs = group.querySelectorAll('input');

    const isAutos = type === 'autos';
    const isMotos = type === 'motos';
    const keys = isAutos ? 
        ['precio_hora', 'precio_dia', 'precio_semana', 'precio_mes'] :
        (isMotos ? 
            ['precio_hora_moto', 'precio_dia_moto', 'precio_semana_moto', 'precio_mes_moto'] :
            ['precio_hora_camioneta', 'precio_dia_camioneta', 'precio_semana_camioneta', 'precio_mes_camioneta']);

    const labels = {
        'precio_hora': 'Hora', 'precio_dia': 'Día', 'precio_semana': 'Semana', 'precio_mes': 'Mes',
        'precio_hora_moto': 'Hora', 'precio_dia_moto': 'Día', 'precio_semana_moto': 'Semana', 'precio_mes_moto': 'Mes',
        'precio_hora_camioneta': 'Hora', 'precio_dia_camioneta': 'Día', 'precio_semana_camioneta': 'Semana', 'precio_mes_camioneta': 'Mes'
    };

    let summary = '<div style="text-align: left; margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; max-height: 200px; overflow-y: auto;">';
    keys.forEach(key => {
        const val = document.getElementById(`cfg-${key}`)?.value || 0;
        summary += `<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #fff; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">${labels[key]}:</span>
                        <b style="color: var(--dorado); font-size: 0.75rem;">$${formatNum(parseFloat(val))}</b>
                    </div>`;
    });
    summary += '</div>';

    const resetUI = () => {
        inputs.forEach(input => input.disabled = true);
        group.classList.remove('editing');
        btn.innerHTML = '<i class="fas fa-edit mr-8"></i> EDITAR';
        btn.style.borderColor = 'var(--dorado)';
        btn.style.color = '#aaa';
    };

    if (!await showConfirm(`Confirmar Tarifas ${type.toUpperCase()}`, summary)) {
        resetUI();
        return;
    }

    let success = true;
    for (const key of keys) {
        const input = document.getElementById(`cfg-${key}`);
        if (!input) continue;
        const val = parseFloat(input.value) || 0;
        const res = await api.post(`/admin/settings/prices?clave=${key}&valor=${val}`);
        if (!res.ok) success = false;
    }

    if (success) {
        showToast(`Tarifas de ${type} actualizadas correctamente.`, 'success');
    } else {
        showToast('Error al actualizar algunas tarifas.', 'error');
    }
    
    resetUI();
}

export async function saveSystemParam(param) {
    const val = document.getElementById(`cfg-${param}`)?.value;
    if (val === undefined) return;
    const res = await api.post(`/admin/settings/prices?clave=${param}&valor=${val}`);
    if (res.ok) showToast('Configuración guardada.', 'success');
    else showToast(res.error, 'error');
}

export async function saveCapacities() {
    const capAutos = document.getElementById('cfg-capacidad_total')?.value;
    const capMotos = document.getElementById('cfg-capacidad_motos')?.value;

    if (!capAutos || !capMotos) return showToast('Completá ambos valores de plazas', 'error');

    let success = true;
    const resAutos = await api.post(`/admin/settings/prices?clave=capacidad_total&valor=${capAutos}`);
    if (!resAutos.ok) success = false;

    const resMotos = await api.post(`/admin/settings/prices?clave=capacidad_motos&valor=${capMotos}`);
    if (!resMotos.ok) success = false;

    if (success) showToast('Plazas actualizadas correctamente.', 'success');
    else showToast('Error al actualizar plazas.', 'error');
}

export async function resetSys() {
    if (!await showConfirm('REINICIAR SISTEMA', 'Esto eliminará logs de acceso y ocupación actual. ¿Continuar?')) return;
    const res = await api.post('/system/reset');
    if (res && res.ok) {
        showToast('Sistema reiniciado.', 'success');
        window.location.reload();
    } else showToast(res?.error || 'Error', 'error');
}

export async function exportFinanceData() {
    const period = document.getElementById('fin-period')?.value || 'month';
    showToast('Generando reporte...', 'info');
    
    const res = await api.get(`/reports/payment-history?period=${period}&limit=0`);
    if (!res || !res.ok) {
        showToast('Error al obtener datos para exportar', 'error');
        return;
    }
    
    const data = res.data;
    if (data.length === 0) {
        showToast('No hay transacciones para exportar en este período', 'info');
        return;
    }
    
    const headers = ['Fecha y Hora', 'Vehículo / Patente', 'Monto Abonado', 'Método de Pago', 'Estado/Tipo'];
    const rows = data.map(p => {
        const dateStr = formatDate(p.fecha_pago);
        const amount = p.costo_estadia;
        const method = (p.tipo === 'Reserva' || p.tipo === 'Reembolso') ? 'MERCADO PAGO / ABONO' : 'SISTEMA DIGITAL';
        const type = p.tipo;
        return [
            `"${dateStr}"`,
            `"${formatPlate(p.patente_detectada)}"`,
            amount,
            `"${method}"`,
            `"${type}"`
        ];
    });
    
    const csvContent = "\uFEFF" + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    
    const branchName = localStorage.getItem('sucursal') || 'global';
    const cleanBranch = branchName.replace('AUTOPASS ', '').toLowerCase().replace(/\s+/g, '_');
    link.setAttribute("download", `reporte_financiero_${cleanBranch}_${period}_${getVirtualNow().toISOString().split('T')[0]}.csv`);
    
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('Reporte descargado correctamente.', 'success');
}
