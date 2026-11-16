import api from './api.js';
import { formatNum, formatDate, formatDateTime, parseFecha } from './utils.js';
import { THEME } from './theme.js';
import { WindowedChart } from './chart-window.js';

/**
 * Módulo de Informes del Dashboard (Métricas)
 * MAPA DE CALOR DE TRÁFICO, OCUPACIÓN Y RESERVAS, RECAUDACIÓN y TIEMPOS OCR & ALPR.
 * Recae sobre: /reports/metrics/traffic-heatmap, /reports/metrics/occupancy-summary,
 *              /reports/financial-summary, /reports/ocr-stats y /reports/ocr-activity.
 */

const filtros = {
    heatmap: { sucursal: '', desde: '', hasta: '' },
    ocupacion: { sucursal: '', desde: '', hasta: '' },
    recaudacion: { sucursal: '', desde: '', hasta: '' }
};

let branchesLoaded = false;

// Vista del mapa de calor: mensual ('mes')
let heatmapView = 'mes';
let heatmapCache = null;
let hmBarrasChart = null;
let currentMonthIndex = -1;

const DOW_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const DOW_SHORT = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM'];

// Colores fijos por tramo horario (indicación de horario en el gráfico de barras)
const HM_TRAMO_COLORS = [
    'rgba(223,186,107,0.25)',
    'rgba(223,186,107,0.45)',
    'rgba(223,186,107,0.65)',
    'rgba(223,186,107,0.85)',
    THEME.gold
];

/**
 * Paleta Glassmorphism Dark Mode:
 * ratio === 0: celda neutra translúcida
 * ratio > 0: Dorado suave → Ámbar → Coral/Rojo → Carmesí pico
 */
function _hmCellColor(ratio, v) {
    if (!v || ratio <= 0) return 'rgba(255, 255, 255, 0.02)';
    const t = Math.min(1, Math.max(0.02, ratio));
    if (t < 0.25) {
        const alpha = 0.16 + (t / 0.25) * 0.24;
        return `rgba(223, 186, 107, ${alpha.toFixed(2)})`;
    } else if (t < 0.6) {
        const p = (t - 0.25) / 0.35;
        const r = Math.round(223 + (245 - 223) * p);
        const g = Math.round(186 + (158 - 186) * p);
        const b = Math.round(107 + (11 - 107) * p);
        const alpha = 0.45 + p * 0.3;
        return `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(2)})`;
    } else if (t < 0.85) {
        const p = (t - 0.6) / 0.25;
        const r = Math.round(245 + (239 - 245) * p);
        const g = Math.round(158 + (68 - 158) * p);
        const b = Math.round(11 + (68 - 11) * p);
        const alpha = 0.75 + p * 0.2;
        return `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(2)})`;
    } else {
        const p = (t - 0.85) / 0.15;
        const r = Math.round(239 + (220 - 239) * p);
        const g = Math.round(68 + (38 - 68) * p);
        const b = Math.round(68 + (38 - 68) * p);
        return `rgba(${r}, ${g}, ${b}, 0.98)`;
    }
}

function _hmCellText(ratio, v) {
    if (!v || ratio <= 0) return 'rgba(255, 255, 255, 0.2)';
    if (ratio < 0.25) return 'rgba(255, 255, 255, 0.9)';
    return '#ffffff';
}

async function cargarBranches() {
    if (branchesLoaded) return;
    const res = await api.get('/parking/branches');
    if (!res.ok || !Array.isArray(res.data)) return;
    const opts = ['<option value="">TODAS</option>']
        .concat(res.data.map(b => `<option value="${b.nombre}">${b.nombre}</option>`));
    ['hm-sucursal', 'occ-sucursal', 'fin-sucursal'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = opts.join('');
    });
    branchesLoaded = true;
}

export async function cargarInforme(key) {
    if (key === 'heatmap' || key === 'ocupacion' || key === 'recaudacion') await cargarBranches();
    if (key === 'heatmap') return cargarHeatmap();
    if (key === 'ocupacion') return cargarOcupacion();
    if (key === 'recaudacion') return cargarRecaudacion();
    if (key === 'ocr') return cargarOcr();
}

export function aplicarInforme(key) {
    if (key === 'heatmap') filtros.heatmap = _leerFiltros('hm');
    if (key === 'ocupacion') filtros.ocupacion = _leerFiltros('occ');
    if (key === 'recaudacion') filtros.recaudacion = _leerFiltros('fin');
    cargarInforme(key);
}

export function limpiarInforme(key) {
    if (key === 'heatmap') filtros.heatmap = _limpiar('hm');
    if (key === 'ocupacion') filtros.ocupacion = _limpiar('occ');
    if (key === 'recaudacion') filtros.recaudacion = _limpiar('fin');
    cargarInforme(key);
}

export function alternarHeatmapVista(vista) {
    heatmapView = 'mes';
    _pintarLeyenda();
    if (heatmapCache) _renderHeatmap();
}
window.alternarHeatmapVista = alternarHeatmapVista;

function _leerFiltros(prefix) {
    return {
        sucursal: document.getElementById(`${prefix}-sucursal`)?.value || '',
        desde: document.getElementById(`${prefix}-desde`)?.value || '',
        hasta: document.getElementById(`${prefix}-hasta`)?.value || ''
    };
}

function _limpiar(prefix) {
    const ids = ['sucursal', 'desde', 'hasta'];
    ids.forEach(k => {
        const el = document.getElementById(`${prefix}-${k}`);
        if (el) el.value = '';
    });
    return { sucursal: '', desde: '', hasta: '' };
}

function _params(f) {
    const p = new URLSearchParams();
    if (f.sucursal) p.set('sucursal', f.sucursal);
    if (f.desde) p.set('desde', f.desde);
    if (f.hasta) p.set('hasta', f.hasta);
    const s = p.toString();
    return s ? `?${s}` : '';
}

// ==========================================================================
// 1) MAPA DE CALOR DE TRÁFICO
// ==========================================================================
async function cargarHeatmap() {
    const container = document.getElementById('hm-contenido');
    if (!container) return;
    container.innerHTML = '<div class="heatmap-vacio"><i class="fas fa-fire" style="opacity:0.4;"></i> Cargando mapa de calor…</div>';

    const res = await api.get(`/reports/metrics/traffic-heatmap${_params(filtros.heatmap)}`);
    heatmapCache = null;
    if (!res.ok) return _err(container, res.error);
    const data = res.data;

    if (!data.total_entradas) {
        container.innerHTML = '<div class="heatmap-vacio"><i class="fas fa-database" style="opacity:0.4;"></i> No hay entradas registradas en el rango seleccionado.</div>';
        return;
    }

    heatmapCache = data;
    currentMonthIndex = data.meses && data.meses.length ? data.meses.length - 1 : 0;
    _pintarLeyenda();
    _renderHeatmap();
}

export function navegarHeatmapMes(delta) {
    if (!heatmapCache || !heatmapCache.meses || !heatmapCache.meses.length) return;
    const d = parseInt(delta, 10);
    const nextIdx = currentMonthIndex + d;
    if (nextIdx >= 0 && nextIdx < heatmapCache.meses.length) {
        currentMonthIndex = nextIdx;
        _renderHeatmap();
    }
}
window.navegarHeatmapMes = navegarHeatmapMes;

export function seleccionarHeatmapMes(idx) {
    if (!heatmapCache || !heatmapCache.meses || !heatmapCache.meses.length) return;
    const n = parseInt(idx, 10);
    if (!isNaN(n) && n >= 0 && n < heatmapCache.meses.length) {
        currentMonthIndex = n;
        _renderHeatmap();
    }
}
window.seleccionarHeatmapMes = seleccionarHeatmapMes;

if (typeof document !== 'undefined') {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.heatmap-nav-btn');
        if (!btn || btn.disabled) return;
        const delta = parseInt(btn.dataset.delta, 10);
        if (!isNaN(delta)) {
            e.preventDefault();
            navegarHeatmapMes(delta);
        }
    });
}

function _renderHeatmap() {
    const container = document.getElementById('hm-contenido');
    if (!container || !heatmapCache) return;
    try {
        return _renderHeatmapMes(container);
    } catch (err) {
        console.error('Error al renderizar heatmap mensual:', err);
    }
}

function _renderHeatmapKPIs(data) {
    const { horas_labels, totals_per_hour, total_entradas, dias, matrix, contextLabel } = data;

    // 1. Hora pico global o del mes
    let maxHourIdx = 0;
    let maxHourVal = 0;
    (totals_per_hour || []).forEach((tot, idx) => {
        if (tot > maxHourVal) {
            maxHourVal = tot;
            maxHourIdx = idx;
        }
    });
    const peakHourLabel = horas_labels && horas_labels[maxHourIdx] ? horas_labels[maxHourIdx] : '—';

    // 2. Día de la semana con mayor flujo acumulado
    const dowTotals = [0, 0, 0, 0, 0, 0, 0];
    dias.forEach((fecha, c) => {
        const parts = fecha.split('-');
        const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        const dow = (dt.getDay() + 6) % 7;
        for (let r = 0; r < (horas_labels || []).length; r++) {
            dowTotals[dow] += matrix[r] ? (matrix[r][c] || 0) : 0;
        }
    });
    let maxDowIdx = 0;
    let maxDowVal = 0;
    dowTotals.forEach((tot, idx) => {
        if (tot > maxDowVal) {
            maxDowVal = tot;
            maxDowIdx = idx;
        }
    });
    const peakDayLabel = maxDowVal > 0 ? DOW_NAMES[maxDowIdx] : '—';

    // 3. Promedio diario
    const nDias = Math.max(1, dias.length);
    const avgDaily = Math.round(total_entradas / nDias);

    const labelHora = contextLabel ? `HORA PICO (${contextLabel})` : 'HORA PICO GLOBAL';

    return `
        <div class="heatmap-kpis-grid">
            <div class="heatmap-kpi-card">
                <div class="heatmap-kpi-icon-wrap heatmap-kpi-icon-wrap--peak">
                    <i class="fas fa-fire" aria-hidden="true"></i>
                </div>
                <div class="heatmap-kpi-content">
                    <span class="heatmap-kpi-label">${labelHora}</span>
                    <div class="heatmap-kpi-val">${peakHourLabel}</div>
                    <span class="heatmap-kpi-sub">${formatNum(maxHourVal)} vehículos en total</span>
                </div>
            </div>
            <div class="heatmap-kpi-card">
                <div class="heatmap-kpi-icon-wrap heatmap-kpi-icon-wrap--day">
                    <i class="fas fa-calendar-check" aria-hidden="true"></i>
                </div>
                <div class="heatmap-kpi-content">
                    <span class="heatmap-kpi-label">DÍA CON MÁS FLUJO</span>
                    <div class="heatmap-kpi-val">${peakDayLabel}</div>
                    <span class="heatmap-kpi-sub">${formatNum(maxDowVal)} vehículos acumulados</span>
                </div>
            </div>
            <div class="heatmap-kpi-card">
                <div class="heatmap-kpi-icon-wrap heatmap-kpi-icon-wrap--avg">
                    <i class="fas fa-chart-line" aria-hidden="true"></i>
                </div>
                <div class="heatmap-kpi-content">
                    <span class="heatmap-kpi-label">PROMEDIO DIARIO</span>
                    <div class="heatmap-kpi-val">${formatNum(avgDaily)} <small class="heatmap-kpi-unit">veh/día</small></div>
                    <span class="heatmap-kpi-sub">${formatNum(total_entradas)} en ${nDias} ${nDias === 1 ? 'día' : 'días'}</span>
                </div>
            </div>
        </div>
    `;
}

function _renderHeatmapSemana(container) {
    const data = heatmapCache;
    const { horas_labels, matrix, totals_per_hour, dias } = data;

    const dowCounts = [0, 0, 0, 0, 0, 0, 0];
    const dowMatrix = Array.from({ length: horas_labels.length }, () => [0, 0, 0, 0, 0, 0, 0]);
    const dowTotals = [0, 0, 0, 0, 0, 0, 0];

    dias.forEach((fecha, c) => {
        const parts = fecha.split('-');
        const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        const dow = (dt.getDay() + 6) % 7;
        dowCounts[dow]++;
        for (let r = 0; r < horas_labels.length; r++) {
            const v = matrix[r][c] || 0;
            dowMatrix[r][dow] += v;
            dowTotals[dow] += v;
        }
    });

    let maxDowCell = 0;
    for (let r = 0; r < horas_labels.length; r++) {
        for (let d = 0; d < 7; d++) {
            if (dowMatrix[r][d] > maxDowCell) maxDowCell = dowMatrix[r][d];
        }
    }

    const kpisHtml = _renderHeatmapKPIs(data);
    const corner = `<div class="heatmap-corner"><span>${data.sucursal || 'TODAS'}</span></div>`;

    const dowHeader = DOW_SHORT.map((shortName, d) => {
        const isWeekend = d >= 5;
        const count = dowCounts[d];
        const countTxt = count === 1 ? '1 día' : `${count} días`;
        return `
            <div class="heatmap-dia heatmap-dia--semana ${isWeekend ? 'heatmap-dia--weekend' : ''}" title="${DOW_NAMES[d]} (${countTxt} analizados)">
                <span class="heatmap-dow-name">${shortName}</span>
                <span class="heatmap-dow-sub">${countTxt}</span>
            </div>
        `;
    }).join('') + '<div class="heatmap-dia heatmap-dia--total">TOTAL</div>';

    const hourRows = horas_labels.map((hl, r) => {
        const celdas = [0, 1, 2, 3, 4, 5, 6].map(d => {
            const v = dowMatrix[r][d];
            const isWeekend = d >= 5;
            const ratio = maxDowCell > 0 ? v / maxDowCell : 0;
            const avg = dowCounts[d] > 0 ? (v / dowCounts[d]).toFixed(1) : 0;
            const tooltip = `${DOW_NAMES[d]} ${hl} — ${formatNum(v)} entradas totales (promedio: ${avg}/día)`;
            if (!v) {
                return `<div class="heatmap-cell heatmap-cell--semana heatmap-cell--zero ${isWeekend ? 'heatmap-cell--weekend' : ''}" title="${tooltip}">—</div>`;
            }
            return `<div class="heatmap-cell heatmap-cell--semana ${isWeekend ? 'heatmap-cell--weekend' : ''}" title="${tooltip}"
                         style="background:${_hmCellColor(ratio, v)};color:${_hmCellText(ratio, v)};">${formatNum(v)}</div>`;
        }).join('');
        return `
            <div class="heatmap-hour">${hl}</div>
            ${celdas}
            <div class="heatmap-hour heatmap-hour--total">${formatNum(totals_per_hour[r])}</div>
        `;
    }).join('');

    const footer = ['<div class="heatmap-day heatmap-day--total">TOTAL</div>']
        .concat(dowTotals.map((tot, d) => `<div class="heatmap-day heatmap-day--total ${d >= 5 ? 'heatmap-day--weekend' : ''}">${formatNum(tot)}</div>`))
        .concat([`<div class="heatmap-day heatmap-day--total">${formatNum(data.total_entradas)}</div>`]).join('');

    container.innerHTML = `
        ${kpisHtml}
        <div class="heatmap-wrap">
            <div class="heatmap-grid heatmap-grid--semana" style="--hm-cols: 7;">
                ${corner}${dowHeader}
                ${hourRows}
                ${footer}
            </div>
        </div>
    `;
}

function _renderHeatmapMes(container) {
    const data = heatmapCache;
    if (!data.meses || !data.meses.length) {
        container.innerHTML = '<div class="heatmap-vacio"><i class="fas fa-calendar-xmark"></i> No hay datos mensuales para mostrar.</div>';
        return;
    }

    if (currentMonthIndex < 0 || currentMonthIndex >= data.meses.length) {
        currentMonthIndex = data.meses.length - 1;
    }

    const monthChunk = data.meses[currentMonthIndex];
    const { start, count, label } = monthChunk;
    const end = start + count;

    // Recorte de datos para el mes seleccionado
    const monthDias = data.dias.slice(start, end);
    const monthMatrix = data.matrix.map(row => row.slice(start, end));
    const monthTotalsPerDay = data.totals_per_day.slice(start, end);
    const monthTotalsPerHour = monthMatrix.map(row => row.reduce((a, b) => a + b, 0));
    const monthTotalEntradas = monthTotalsPerDay.reduce((a, b) => a + b, 0);
    const monthMax = Math.max(...monthMatrix.flatMap(row => row), 0);

    const kpisHtml = _renderHeatmapKPIs({
        horas_labels: data.horas_labels,
        totals_per_hour: monthTotalsPerHour,
        total_entradas: monthTotalEntradas,
        dias: monthDias,
        matrix: monthMatrix,
        contextLabel: label
    });

    const isFirstMonth = currentMonthIndex <= 0;
    const isLastMonth = currentMonthIndex >= data.meses.length - 1;

    const navBar = `
        <div class="heatmap-nav-bar">
            <div class="heatmap-nav-controls">
                <button type="button" class="heatmap-nav-btn" data-delta="-1" ${isFirstMonth ? 'disabled' : ''} onclick="navegarHeatmapMes(-1)" title="${isFirstMonth ? 'Primer mes disponible' : 'Ver mes anterior'}">
                    <i class="fas fa-chevron-left" aria-hidden="true"></i> Anterior
                </button>
                <span class="heatmap-nav-title">
                    <i class="fas fa-calendar-alt" aria-hidden="true"></i> ${label}
                </span>
                <button type="button" class="heatmap-nav-btn" data-delta="1" ${isLastMonth ? 'disabled' : ''} onclick="navegarHeatmapMes(1)" title="${isLastMonth ? 'Mes actual (más reciente)' : 'Ver mes siguiente'}">
                    Siguiente <i class="fas fa-chevron-right" aria-hidden="true"></i>
                </button>
            </div>
            <div class="heatmap-nav-meta">
                <span><strong>${count}</strong> ${count === 1 ? 'día' : 'días'}</span>
                <span>&bull;</span>
                <span><strong>${formatNum(monthTotalEntradas)}</strong> entradas</span>
                ${data.meses.length > 1 ? `<span class="heatmap-nav-counter">(${currentMonthIndex + 1} de ${data.meses.length})</span>` : ''}
            </div>
        </div>
    `;

    const dayRow = monthDias.map(fecha => {
        const parts = fecha.split('-');
        const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        const isWeekend = dt.getDay() === 0 || dt.getDay() === 6;
        const dowIndex = (dt.getDay() + 6) % 7;
        const dayNum = fecha.slice(8, 10);
        const dowTxt = DOW_SHORT[dowIndex];
        return `
            <div class="heatmap-dia heatmap-dia--col ${isWeekend ? 'heatmap-dia--weekend' : ''}" title="${formatDate(fecha)} (${DOW_NAMES[dowIndex]})">
                <span class="heatmap-dia-num">${dayNum}</span>
                <span class="heatmap-dia-dow">${dowTxt}</span>
            </div>
        `;
    }).join('') + '<div class="heatmap-dia heatmap-dia--total">TOT</div>';

    const cornerCells = `<div class="heatmap-corner"><span>${data.sucursal || 'TODAS'}</span></div>`;

    const hourRows = data.horas_labels.map((hl, r) => {
        const celdas = monthDias.map((fecha, c) => {
            const v = monthMatrix[r][c];
            const parts = fecha.split('-');
            const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
            const isWeekend = dt.getDay() === 0 || dt.getDay() === 6;
            const ratio = monthMax > 0 ? v / monthMax : 0;
            const tooltip = `${formatDate(fecha)} ${hl} — ${v} entradas`;
            if (!v) {
                return `<div class="heatmap-cell heatmap-cell--zero ${isWeekend ? 'heatmap-cell--weekend' : ''}" title="${tooltip}"></div>`;
            }
            return `<div class="heatmap-cell ${isWeekend ? 'heatmap-cell--weekend' : ''}" title="${tooltip}"
                        style="background:${_hmCellColor(ratio, v)};color:${_hmCellText(ratio, v)};">${v}</div>`;
        }).join('');
        return `
            <div class="heatmap-hour">${hl}</div>
            ${celdas}
            <div class="heatmap-hour heatmap-hour--total">${formatNum(monthTotalsPerHour[r])}</div>
        `;
    }).join('');

    const footer = ['<div class="heatmap-day heatmap-day--total">TOTAL</div>']
        .concat(monthTotalsPerDay.map((v, c) => {
            const parts = monthDias[c].split('-');
            const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
            const isWeekend = dt.getDay() === 0 || dt.getDay() === 6;
            return `<div class="heatmap-day heatmap-day--total ${isWeekend ? 'heatmap-day--weekend' : ''}">${formatNum(v)}</div>`;
        }))
        .concat([`<div class="heatmap-day heatmap-day--total">${formatNum(monthTotalEntradas)}</div>`]).join('');

    container.innerHTML = `
        ${navBar}
        ${kpisHtml}
        <div class="heatmap-wrap">
            <div class="heatmap-grid heatmap-grid--mes" style="--hm-cols: ${count};">
                ${cornerCells}${dayRow}
                ${hourRows}
                ${footer}
            </div>
        </div>`;
}

// Divide las horas de apertura en 5 tramos y suma las entradas de cada día dentro de cada tramo
function _calcTramos(data) {
    const horas = data.horas_labels;
    const tam = Math.max(1, Math.ceil(horas.length / 5));
    const tramos = [];
    for (let i = 0; i < horas.length; i += tam) {
        const hasta = Math.min(i + tam, horas.length);
        const idx = [];
        for (let j = i; j < hasta; j++) idx.push(j);
        tramos.push({
            label: `${horas[i].slice(0, 5)} a ${horas[hasta - 1].slice(0, 5)}`,
            cls: `hm-leg--t${tramos.length}`,
            color: HM_TRAMO_COLORS[tramos.length],
            values: data.dias.map((_, c) => {
                let s = 0;
                for (const r of idx) s += data.matrix[r][c] || 0;
                return s;
            })
        });
    }
    return tramos;
}

function _renderHeatmapBarras(container) {
    const data = heatmapCache;
    const tramos = _calcTramos(data);

    const viewport = document.createElement('div');
    viewport.className = 'hm-barras-viewport';
    viewport.style.width = (data.dias.length * 150 + 90) + 'px';
    viewport.innerHTML = '<canvas id="hmBarrasChart"></canvas>';

    container.innerHTML = '';
    container.appendChild(viewport);
    container.insertAdjacentHTML('beforeend', `<div class="informe-note">
        <i class="fas fa-circle-info"></i> Columnas: días del ${data.desde.slice(0, 7)} al ${data.hasta.slice(0, 7)}
        (usá el scroll horizontal para recorrerlos). Barras 1-5: total de entradas por tramo
        (${data.horas_labels[0]} a ${data.horas_labels[data.horas_labels.length - 1]}). Barra TOTAL: suma del día en la misma escala
        (= la suma de las 5 barras del día). Total general: ${formatNum(data.total_entradas)} entradas.
    </div>`);

    const canvas = document.getElementById('hmBarrasChart');
    if (!canvas || typeof window.Chart === 'undefined') {
        container.innerHTML = '<div class="heatmap-vacio" style="color:var(--danger);"><i class="fas fa-chart-simple"></i> No se pudo dibujar el gráfico de barras.</div>';
        return;
    }
    if (window.Chart.getChart(canvas)) window.Chart.getChart(canvas).destroy();

    const datasets = tramos.map(t => ({
        label: t.label,
        data: t.values,
        backgroundColor: t.color,
        borderRadius: 3,
        barPercentage: 0.86,
        categoryPercentage: 0.92
    })).concat([{
        label: 'TOTAL',
        data: data.totals_per_day,
        backgroundColor: THEME.gold,
        borderRadius: 3,
        barPercentage: 0.86,
        categoryPercentage: 0.92
    }]);

    hmBarrasChart = new window.Chart(canvas, {
        type: 'bar',
        data: { labels: data.dias.map(d => d.slice(8, 10)), datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: THEME.bgSoft, titleColor: THEME.gold,
                    bodyColor: THEME.textPrimary, borderColor: THEME.goldBorder, borderWidth: 1,
                    callbacks: {
                        title: (items) => formatDate(data.dias[items[0].dataIndex]),
                        label: (c) => c.dataset.label === 'TOTAL'
                            ? ` TOTAL: ${formatNum(c.parsed.y)} entradas`
                            : ` ${c.dataset.label}: ${formatNum(c.parsed.y)} entradas`
                    }
                }
            },
            scales: {
                x: { grid: { color: THEME.grid, drawBorder: false }, ticks: { color: THEME.textMuted, font: { size: 9 }, maxRotation: 0, autoSkip: false } },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Entradas', color: THEME.textMuted, font: { size: 9 } },
                    grid: { color: THEME.grid, drawBorder: false },
                    ticks: { color: THEME.textMuted, font: { size: 9 } }
                }
            }
        }
    });
}

function _pintarLeyenda() {
    const ley = document.getElementById('hm-leyenda');
    if (!ley) return;
    if (heatmapView === 'barras' && heatmapCache) {
        ley.innerHTML = _calcTramos(heatmapCache)
            .map(t => `<span class="heatmap-legend"><span class="heatmap-legend-cell ${t.cls}"></span>${t.label}</span>`)
            .join('')
            + '<span class="heatmap-legend"><span class="heatmap-legend-cell hm-leg--tot"></span>TOTAL DÍA</span>';
        return;
    }
    ley.innerHTML = `
        <span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--0"></span>Sin mov.</span>
        <span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--low"></span>Bajo</span>
        <span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--mid"></span>Medio</span>
        <span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--high"></span>Alto</span>
        <span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--peak"></span>Pico</span>
    `;
}

function _err(el, msg) {
    el.innerHTML = `<div class="heatmap-vacio" style="color:var(--danger);"><i class="fas fa-exclamation-circle"></i> No se pudo cargar el informe: ${msg}</div>`;
}

// ==========================================================================
// 2) OCUPACIÓN Y RESERVAS
// ==========================================================================
let occChart = null;

async function cargarOcupacion() {
    const res = await api.get(`/reports/metrics/occupancy-summary${_params(filtros.ocupacion)}`);
    const kpis = document.getElementById('occ-kpis');
    if (!res.ok) { if (kpis) kpis.innerHTML = '<div class="heatmap-vacio" style="color:var(--danger);"><i class="fas fa-exclamation-circle"></i>No se pudo cargar: ' + res.error + '</div>'; return; }
    const data = res.data;
    const k = data.kpi;
    if (kpis) {
        kpis.innerHTML = _kpi('RESERVAS', formatNum(k.total), 'fa-calendar-check', '') +
            _kpi('RESERVAS PAGADAS', `${formatNum(k.pagadas)} · ${k.tasa_pago}%`, 'fa-money-bill') +
            _kpi('PENDIENTES', formatNum(k.pendientes), 'fa-hourglass-half') +
            _kpi('CANCELADAS', `${formatNum(k.canceladas)} · ${k.tasa_cancelacion}%`, 'fa-ban') +
            _kpi('NO-SHOW', formatNum(k.no_show), 'fa-user-slash', 'highlight') +
            _kpi('TICKET PROMEDIO', `$${formatNum(k.ticket_promedio)}`, 'fa-receipt') +
            _kpi('INGRESOS PAGADOS', `$${formatNum(k.monto_pagado)}`, 'fa-sack-dollar') +
            _kpi('DÍAS EVALUADOS', formatNum(data.dias_evaluados), 'fa-calendar');
    }

    const canvas = document.getElementById('occChart');
    if (!canvas || typeof window.Chart === 'undefined') return;
    if (window.Chart.getChart(canvas)) window.Chart.getChart(canvas).destroy();

    const colores = [THEME.gold, THEME.accent, THEME.success];
    const labels = ['Moto', 'Auto', 'Camioneta'];
    const datasets = Object.entries(data.por_tipo).map(([tipo, v], i) => ({
        label: `${tipo} (cap. ${v.capacidad})`,
        data: v.porcentaje,
        backgroundColor: colores[i],
        borderRadius: 3,
        barPercentage: 0.9
    })).sort((a, b) => labels.indexOf(a.label.split(' ')[0]) - labels.indexOf(b.label.split(' ')[0]));

    occChart = new window.Chart(canvas, {
        type: 'bar',
        data: { labels: data.horas.map(h => `${String(h).padStart(2, '0')}h`), datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: THEME.textPrimary, boxWidth: 12, usePointStyle: true } },
                title: { display: true, text: `Ocupación promedio (% de plazas) por hora — ${data.sucursal || 'todas las sucursales'}`, color: THEME.textMuted, font: { size: 11 } },
                tooltip: {
                    backgroundColor: THEME.bgSoft, titleColor: THEME.gold,
                    bodyColor: THEME.textPrimary, borderColor: THEME.goldBorder, borderWidth: 1,
                    callbacks: { label: (c) => ` ${c.dataset.label}: ${c.parsed.y.toFixed(1)}%` }
                }
            },
            scales: {
                x: { grid: { color: THEME.grid, drawBorder: false }, ticks: { color: THEME.textMuted, font: { size: 9 } } },
                y: { beginAtZero: true, max: 100, grid: { color: THEME.grid, drawBorder: false }, ticks: { color: THEME.textMuted, font: { size: 10 }, callback: (v) => v + '%' } }
            }
        }
    });
}

function _kpi(label, valor, icono, extra = '') {
    return `<div class="kpi-card ${extra}">
        <div class="kpi-icon"><i class="fas ${icono}"></i></div>
        <div class="kpi-data"><span class="label">${label}</span><span class="value">${valor}</span></div>
    </div>`;
}

// ==========================================================================
// 3) RECAUDACIÓN
// ==========================================================================
let finChart = null;

async function cargarRecaudacion() {
    const f = filtros.recaudacion;
    const p = new URLSearchParams();
    if (f.desde || f.hasta) {
        p.set('period', 'day');
        p.set('start', `${f.desde || '1900-01-01'}T00:00:00`);
        p.set('end', `${f.hasta || '2099-12-31'}T23:59:59`);
    }
    if (f.sucursal) p.set('sucursal', f.sucursal);
    const qs = p.toString();
    const res = await api.get(`/reports/financial-summary${qs ? '?' + qs : ''}`);
    const kpis = document.getElementById('fin-kpis');
    if (!res.ok) {
        if (kpis) kpis.innerHTML = '<div class="heatmap-vacio" style="color:var(--danger);"><i class="fas fa-exclamation-circle"></i>No se pudo cargar: ' + res.error + '</div>';
        _renderVentasPorSucursal(null);
        return;
    }
    const d = res.data;
    if (kpis) {
        kpis.innerHTML = _kpi('TOTAL RECAUDADO', `$${formatNum(d.total_recaudado)}`, 'fa-sack-dollar', 'highlight') +
            _kpi('PAGOS', formatNum(d.cantidad_pagos), 'fa-credit-card') +
            _kpi('TICKET PROMEDIO', `$${formatNum(d.ticket_promedio)}`, 'fa-receipt') +
            _kpi('EFECTIVO', `$${formatNum(d.recaudado_efectivo || 0)}`, 'fa-money-bill-1') +
            _kpi('DIGITAL', `$${formatNum(d.recaudado_digital || 0)}`, 'fa-mobile-screen-button') +
            _kpi('REEMBOLSADO', `$${formatNum(d.total_reembolsado)}`, 'fa-rotate-left') +
            _kpi('PROYECTADO', `$${formatNum(d.ingresos_proyectados)}`, 'fa-chart-line') +
            _kpi('CANCELACIÓN', `${d.tasa_cancelacion || 0}%`, 'fa-percent');
    }
    _renderVentasPorSucursal(d);

    const canvas = document.getElementById('finChart');
    if (!canvas || typeof window.Chart === 'undefined') return;
    if (window.Chart.getChart(canvas)) window.Chart.getChart(canvas).destroy();

    const metodos = d.desglose_metodos || [];
    finChart = new window.Chart(canvas, {
        type: 'bar',
        data: {
            labels: metodos.map(m => m.metodo),
            datasets: [{
                label: 'Monto',
                data: metodos.map(m => m.monto),
                backgroundColor: THEME.gold,
                borderRadius: 3
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: THEME.bgSoft, titleColor: THEME.gold,
                    bodyColor: THEME.textPrimary, borderColor: THEME.goldBorder, borderWidth: 1,
                    callbacks: {
                        label: (c) => ` $${formatNum(c.parsed.y)} (${formatNum(metodos[c.dataIndex].cantidad)} pagos)`
                    }
                }
            },
            scales: {
                x: { grid: { color: THEME.grid, drawBorder: false }, ticks: { color: THEME.textMuted, font: { size: 10 } } },
                y: { grid: { color: THEME.grid, drawBorder: false }, ticks: { color: THEME.textMuted, font: { size: 10 }, callback: (v) => '$' + formatNum(v) } }
            }
        }
    });
}

// Tabla de ventas por sucursal (solo llega `por_sucursal` para el admin general sin filtro de sede)
function _renderVentasPorSucursal(d) {
    const card = document.getElementById('fin-por-sucursal-card');
    const body = document.getElementById('fin-por-sucursal-body');
    if (!card || !body) return;
    const filas = d && Array.isArray(d.por_sucursal) ? d.por_sucursal : [];
    if (!filas.length) {
        body.innerHTML = '';
        card.hidden = true;
        return;
    }
    body.innerHTML = filas.map(f => `<tr>
            <td data-label="Sucursal">${f.sucursal}</td>
            <td data-label="Recaudado">$${formatNum(f.total_recaudado)}</td>
            <td data-label="Pagos">${formatNum(f.cantidad_pagos)}</td>
            <td data-label="Ticket prom.">$${formatNum(f.ticket_promedio)}</td>
            <td data-label="Efectivo">$${formatNum(f.recaudado_efectivo)}</td>
            <td data-label="Digital">$${formatNum(f.recaudado_digital)}</td>
        </tr>`).join('');
    card.hidden = false;
}

// ==========================================================================
// 4) TIEMPOS OCR & ALPR
// ==========================================================================
let ocrWindowed = null;

function _buildOcrDatasets(pts) {
    return [{
        label: 'Tiempo OCR (s)',
        data: pts,
        borderColor: THEME.accent,
        backgroundColor: 'rgba(56,189,248,0.08)',
        borderWidth: 1.5,
        pointRadius: 0,
        pointHoverRadius: 3,
        fill: true,
        tension: 0.25
    }];
}

async function cargarOcr() {
    const kpis = document.getElementById('ocr-kpis');
    const canvas = document.getElementById('ocrChart');

    const [resStats, resSerie] = await Promise.all([
        api.get('/reports/ocr-stats?limit=100'),
        api.get('/reports/ocr-activity')
    ]);

    if (resStats.ok && resStats.data && kpis) {
        const s = resStats.data.stats;
        kpis.innerHTML = _kpi('EVENTOS OCR', s.count ? formatNum(s.count) : '0', 'fa-microchip') +
            _kpi('PROMEDIO', s.count ? s.avg_ocr.toFixed(3) + 's' : '--', 'fa-gauge-high') +
            _kpi('MÍNIMO', s.count ? s.min_ocr.toFixed(3) + 's' : '--', 'fa-bolt') +
            _kpi('MÁXIMO', s.count ? s.max_ocr.toFixed(3) + 's' : '--', 'fa-triangle-exclamation') +
            _kpi('PERCENTIL 90', s.count ? s.p90_ocr.toFixed(3) + 's' : '--', 'fa-chart-gantt') +
            _kpi('DETECCIONES >1s', s.lentos !== undefined ? formatNum(s.lentos) : '--', 'fa-stopwatch');
    } else if (kpis) {
        kpis.innerHTML = '<div class="heatmap-vacio" style="color:var(--danger);"><i class="fas fa-exclamation-circle"></i>No se pudieron obtener estadísticas OCR.</div>';
    }

    if (resSerie.ok && resSerie.data && canvas && typeof window.Chart !== 'undefined') {
        const points = (resSerie.data.points || [])
            .map(p => ({ x: parseFecha(p.fecha_hora).getTime(), y: parseFloat(p.ocr_time) }))
            .filter(p => !isNaN(p.x) && !isNaN(p.y));
        if (!ocrWindowed) {
            ocrWindowed = new WindowedChart({
                prefix: 'ocrm',
                canvasId: 'ocrChart',
                defaultSpanH: 24,
                buildDatasets: _buildOcrDatasets,
                yExtra: {
                    title: { display: true, text: 'Segundos', color: THEME.textMuted, font: { size: 10 } },
                    ticks: { color: THEME.textMuted, font: { size: 10 }, callback: (v) => v + 's' }
                },
                tooltipTitle: (item) => formatDateTime(new Date(item.parsed.x)),
                tooltipLabel: (c) => ` ${(c.parsed.y || 0).toFixed(3)}s`
            });
        }
        ocrWindowed.setSeries(points);
    }
}