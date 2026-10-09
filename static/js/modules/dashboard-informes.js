import api from './api.js';
import { formatNum, formatDate } from './utils.js';
import { THEME } from './theme.js';

/**
 * Módulo de Informes del Dashboard (Métricas)
 * MAPA DE CALOR DE TRÁFICO, OCUPACIÓN Y RESERVAS, RECAUDACIÓN y TIEMPOS OCR & ALPR.
 * Recae sobre: /reports/metrics/traffic-heatmap, /reports/metrics/occupancy-summary,
 *              /reports/financial-summary, /reports/ocr-stats y /reports/ocr-activity.
 */

const filtros = {
    heatmap: { sucursal: '', desde: '', hasta: '' },
    ocupacion: { sucursal: '', desde: '', hasta: '' },
    recaudacion: { desde: '', hasta: '' }
};

let branchesLoaded = false;

// Vista del mapa de calor: 'calor' (grilla) o 'barras' (gráfico por tramos horarios)
let heatmapView = 'calor';
let heatmapCache = null;
let hmBarrasChart = null;

// Rampa blanco → rojo: menos actividad (blanco) → más actividad (rojo) [solo grilla heatmap]
const HM_WHITE_TO_RED = [[255, 255, 255], [220, 38, 38]];

// Colores fijos por tramo horario (indicación de horario en el gráfico de barras)
const HM_TRAMO_COLORS = [
    'rgba(223,186,107,0.25)',
    'rgba(223,186,107,0.45)',
    'rgba(223,186,107,0.65)',
    'rgba(223,186,107,0.85)',
    THEME.gold
];

function _hmLerp(ratio) {
    const t = Math.min(1, Math.max(0, ratio));
    const [aw, ag, ab] = HM_WHITE_TO_RED[0];
    const [bw, bg, bb] = HM_WHITE_TO_RED[1];
    return [
        Math.round(aw + (bw - aw) * t),
        Math.round(ag + (bg - ag) * t),
        Math.round(ab + (bb - ab) * t)
    ];
}

function _hmCellColor(ratio) {
    const [r, g, b] = _hmLerp(ratio);
    return `rgb(${r},${g},${b})`;
}

function _hmCellText(ratio) {
    const [r, g, b] = _hmLerp(ratio);
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 150 ? '#14161a' : 'rgba(255,255,255,0.92)';
}

async function cargarBranches() {
    if (branchesLoaded) return;
    const res = await api.get('/parking/branches');
    if (!res.ok || !Array.isArray(res.data)) return;
    const opts = ['<option value="">TODAS</option>']
        .concat(res.data.map(b => `<option value="${b.nombre}">${b.nombre}</option>`));
    ['hm-sucursal', 'occ-sucursal'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = opts.join('');
    });
    branchesLoaded = true;
}

export async function cargarInforme(key) {
    if (key === 'heatmap' || key === 'ocupacion') await cargarBranches();
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
    if (vista !== 'calor' && vista !== 'barras') return;
    heatmapView = vista;
    document.querySelectorAll('[data-hm-view]').forEach(btn =>
        btn.classList.toggle('hm-view-btn--active', btn.dataset.hmView === vista));
    _pintarLeyenda();
    if (heatmapCache) _renderHeatmap();
}

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
    _pintarLeyenda();
    _renderHeatmap();
}

function _renderHeatmap() {
    const container = document.getElementById('hm-contenido');
    if (!container || !heatmapCache) return;
    if (heatmapView === 'barras') return _renderHeatmapBarras(container);
    _renderHeatmapGrid(container);
}

function _renderHeatmapGrid(container) {
    const data = heatmapCache;
    const { horas_labels, matrix, totals_per_day, totals_per_hour, max, dias, meses } = data;
    const n_dias = dias.length;

    // Cabecera: mes (con su hueco inferior para el día) + días
    const monthRow = meses.map(m =>
        `<div class="heatmap-month" style="grid-column: ${m.start + 2} / span ${m.count}">${m.label}</div>`
    ).join('') + '<div class="heatmap-dia heatmap-dia--total">TOT</div>';

    const dayRow = dias.map((fecha, c) =>
        `<div class="heatmap-dia" title="${formatDate(fecha)}">${fecha.slice(8, 10)}</div>`
    ).join('') + '<div class="heatmap-dia heatmap-dia--total">TOT</div>';

    const cornerCells = ['<div class="heatmap-corner"><span>' + (data.sucursal || 'TODAS') + '</span></div>']
        .join('');

    // Filas por hora: label + celdas + total por hora
    const hourRows = horas_labels.map((hl, r) => {
        const celdas = dias.map((fecha, c) => {
            const v = matrix[r][c];
            const ratio = max > 0 ? v / max : 0;
            const tooltip = `${formatDate(fecha)} ${hl} — ${v} entradas`;
            return `<div class="heatmap-cell" title="${tooltip}"
                        style="background:${_hmCellColor(ratio)};color:${_hmCellText(ratio)};">${v || ''}</div>`;
        }).join('');
        return `<div class="heatmap-hour">${hl}</div>${celdas}
                <div class="heatmap-hour heatmap-hour--total">${formatNum(totals_per_hour[r])}</div>`;
    }).join('');

    // Fila final: TOTAL + total por día + total general
    const footer = ['<div class="heatmap-day heatmap-day--total">TOTAL</div>']
        .concat(totals_per_day.map(v => `<div class="heatmap-day heatmap-day--total">${formatNum(v)}</div>`))
        .concat([`<div class="heatmap-day heatmap-day--total">${formatNum(data.total_entradas)}</div>`]).join('');

    container.innerHTML = `
        <div class="heatmap-grid heatmap-grid--mes" style="--hm-cols: ${n_dias};">
            ${cornerCells}${monthRow}
            ${cornerCells}${dayRow}
            ${hourRows}
            ${footer}
        </div>
        <div class="informe-note">
            <i class="fas fa-circle-info"></i> Columnas: días del ${data.desde.slice(0, 7)} al ${data.hasta.slice(0, 7)}
            (cada columna es un día calendario).
            Filas: horas de apertura de ${data.sucursal || 'todas las sucursales'} (${horas_labels[0]} a ${horas_labels[horas_labels.length - 1]}).
            Total: ${formatNum(data.total_entradas)} entradas.
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
    ley.innerHTML = `<span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--0"></span>Bajo</span>
        <span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--m"></span>Medio</span>
        <span class="heatmap-legend"><span class="heatmap-legend-cell heatmap-legend-cell--h"></span>Alto</span>`;
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
    let qs = '';
    if (f.desde || f.hasta) {
        qs = `period=day&start=${f.desde || '1900-01-01'}T00:00:00&end=${f.hasta || '2099-12-31'}T23:59:59`;
    }
    const res = await api.get(`/reports/financial-summary${qs ? '?' + qs : ''}`);
    const kpis = document.getElementById('fin-kpis');
    if (!res.ok) { if (kpis) kpis.innerHTML = '<div class="heatmap-vacio" style="color:var(--danger);"><i class="fas fa-exclamation-circle"></i>No se pudo cargar: ' + res.error + '</div>'; return; }
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

// ==========================================================================
// 4) TIEMPOS OCR & ALPR
// ==========================================================================
let ocrChart = null;
let serieOcrSerial = [];

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
        serieOcrSerial = (resSerie.data.points || []).slice(0, 500);
        if (window.Chart.getChart(canvas)) window.Chart.getChart(canvas).destroy();
        ocrChart = new window.Chart(canvas, {
            type: 'line',
            data: {
                labels: serieOcrSerial.map(p => p.fecha_hora || ''),
                datasets: [{
                    label: 'Tiempo OCR (s)',
                    data: serieOcrSerial.map(p => parseFloat(p.ocr_time)),
                    borderColor: THEME.accent,
                    backgroundColor: 'rgba(56,189,248,0.08)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    pointHoverRadius: 3,
                    fill: true,
                    tension: 0.25
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: THEME.bgSoft, titleColor: THEME.gold,
                        bodyColor: THEME.textPrimary, borderColor: THEME.goldBorder, borderWidth: 1,
                        callbacks: { label: (c) => ` ${c.parsed.y?.toFixed(3)}s` }
                    }
                },
                scales: {
                    x: { grid: { color: THEME.grid, drawBorder: false }, ticks: { color: THEME.textMuted, font: { size: 9 }, maxTicksLimit: 12 } },
                    y: { title: { display: true, text: 'Segundos', color: THEME.textMuted, font: { size: 10 } }, grid: { color: THEME.grid, drawBorder: false }, ticks: { color: THEME.textMuted, font: { size: 10 }, callback: (v) => v + 's' } }
                }
            }
        });
    }
}