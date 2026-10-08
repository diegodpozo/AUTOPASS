import api from './api.js';
import { formatDateTime, formatDayTime, parseFecha } from './utils.js';
import { THEME } from './theme.js';
import { cargarInforme } from './dashboard-informes.js';

/**
 * Módulo de Métricas del Sistema (Gráfico de Accesos en Vivo)
 */

let serieData = { buckets: [], first_bucket: null, first_datetime: null, last_bucket: null, totals: {} };
let estado = {
    viewStart: 0,
    viewLen: 48,
    showAll: false,
    live: true,
    filtro: { desde: null, hasta: null, bloqueado: false }
};
let chartMetricas = null;
let intervaloRefresh = null;

// --- UTILIDADES DE FECHA ---
function bucketToDate(label) {
    if (!label) return null;
    const d = parseFecha(label);
    return isNaN(d.getTime()) ? null : d;
}

// --- CARGA DE DATOS ---
async function cargarSerie() {
    let url = '/reports/metrics/access-activity';
    const params = new URLSearchParams();
    if (estado.filtro.desde) params.set('desde', estado.filtro.desde);
    if (estado.filtro.hasta) params.set('hasta', estado.filtro.hasta);
    const qs = params.toString();
    if (qs) url += '?' + qs;
    const res = await api.get(url);
    if (!res || !res.ok || !res.data) {
        console.error('Error cargando métrica de accesos:', res && res.error);
        return false;
    }
    serieData = res.data;
    const wasFollowing = estado.live && !estado.showAll;
    actualizarKPIs();
    if (wasFollowing) {
        estado.viewStart = Math.max(0, serieData.buckets.length - estado.viewLen);
    }
    estado.viewStart = Math.min(estado.viewStart, maxStart());
    sincronizarSlider();
    renderGrafico();
    return true;
}

function maxStart() {
    if (estado.showAll || serieData.buckets.length === 0) return 0;
    return Math.max(0, serieData.buckets.length - estado.viewLen);
}

function actualizarKPIs() {
    const set = (id, txt) => {
        const el = document.getElementById(id);
        if (el) el.textContent = txt;
    };
    const dPrimero = bucketToDate(serieData.first_datetime);
    set('kpi-primer-dato', dPrimero ? formatDateTime(dPrimero) : '--');
    const dUltimo = bucketToDate(serieData.last_bucket);
    set('kpi-ultima-hora', dUltimo ? formatDateTime(dUltimo) : '--');
    set('det-primer-dato', dPrimero ? formatDateTime(dPrimero) : 'sin datos');
    set('kpi-entradas', (serieData.totals.entrada || 0).toLocaleString('es-AR'));
    set('kpi-salidas', (serieData.totals.salida || 0).toLocaleString('es-AR'));
    set('kpi-total', (serieData.totals.total || 0).toLocaleString('es-AR'));
}

function ventanaVisible() {
    const buckets = serieData.buckets;
    if (!buckets.length) return { labels: [], entradas: [], salidas: [] };
    if (estado.showAll) {
        return {
            labels: buckets.map(b => b.label),
            entradas: buckets.map(b => b.entrada),
            salidas: buckets.map(b => b.salida)
        };
    }
    const end = Math.min(estado.viewStart + estado.viewLen, buckets.length);
    const slice = buckets.slice(estado.viewStart, end);
    return {
        labels: slice.map(b => b.label),
        entradas: slice.map(b => b.entrada),
        salidas: slice.map(b => b.salida)
    };
}

// --- GRÁFICO ---
function renderGrafico() {
    const canvas = document.getElementById('metricasChart');
    if (!canvas || typeof window.Chart === 'undefined') return;
    const ctx = canvas.getContext('2d');

    if (chartMetricas) {
        chartMetricas.destroy();
        chartMetricas = null;
    }

    if (!serieData.buckets.length) {
        fillEmpty(canvas.parentNode, 'Sin datos de accesos registrados aún.');
        return;
    }

    const { labels, entradas, salidas } = ventanaVisible();

    chartMetricas = new window.Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Entradas',
                    data: entradas,
                    borderColor: THEME.success,
                    backgroundColor: 'rgba(16, 185, 129, 0.10)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointBackgroundColor: THEME.success,
                    pointBorderColor: THEME.pointDark,
                    pointBorderWidth: 1.5,
                    hitRadius: 30
                },
                {
                    label: 'Salidas',
                    data: salidas,
                    borderColor: THEME.danger,
                    backgroundColor: 'rgba(244, 63, 94, 0.10)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointBackgroundColor: THEME.danger,
                    pointBorderColor: THEME.pointDark,
                    pointBorderWidth: 1.5,
                    hitRadius: 30
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'nearest', intersect: false, axis: 'xy', includeInvisible: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: THEME.bgSoft,
                    titleColor: THEME.gold,
                    bodyColor: THEME.textPrimary,
                    borderColor: THEME.goldBorder,
                    borderWidth: 1,
                    displayColors: true,
                    boxWidth: 8,
                    boxHeight: 8,
                    usePointStyle: true,
                    titleFont: { size: 12, weight: 'bold' },
                    bodyFont: { size: 12 },
                    callbacks: {
                        title: (items) => {
                            const it = items[0];
                            if (!it) return '';
                            const d = bucketToDate(it.label);
                            return d ? formatDateTime(d) : it.label;
                        },
                        label: (c) => ` ${c.dataset.label}: ${c.parsed.y}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Movimientos', color: THEME.textMuted, font: { size: 10 } },
                    grid: { color: THEME.grid, drawBorder: false },
                    ticks: { color: THEME.textMuted, font: { size: 10 }, precision: 0 }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: THEME.textMuted,
                        font: { size: 9 },
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 12,
                        callback: function(val, idx) {
                            const d = bucketToDate(this.getLabelForValue(val));
                            return d ? formatDayTime(d) : this.getLabelForValue(val);
                        }
                    }
                }
            }
        }
    });
}

function fillEmpty(container, msg) {
    const div = document.createElement('div');
    div.style.cssText = 'height:100%;display:flex;align-items:center;justify-content:center;color:#6b7280;flex-direction:column;gap:10px;';
    div.innerHTML = `<i class="fas fa-inbox fa-2x" style="opacity:0.4;"></i><span style="font-size:0.85rem;">${msg}</span>`;
    container.appendChild(div);
}

// --- NAVEGACIÓN POR EL GRÁFICO ---
function sincronizarSlider() {
    const slider = document.getElementById('metricas-range');
    if (!slider) return;
    slider.min = 0;
    slider.max = maxStart();
    slider.value = Math.min(estado.viewStart, maxStart());
    slider.disabled = estado.showAll || serieData.buckets.length === 0;
}

function setVentana(vlen) {
    if (vlen === 0) {
        estado.showAll = true;
    } else {
        estado.showAll = false;
        estado.viewLen = vlen;
    }
    estado.viewStart = Math.min(estado.viewStart, maxStart());
    sincronizarSlider();
    renderGrafico();
}

function detenerRefresh() {
    if (intervaloRefresh) {
        clearInterval(intervaloRefresh);
        intervaloRefresh = null;
    }
}

function configurarRefresh() {
    detenerRefresh();
    intervaloRefresh = setInterval(async () => {
        if (localStorage.getItem('activeAdminTab') !== 'metricas') return;
        if (estado.filtro.bloqueado) return;
        await cargarSerie();
    }, 15000);
}

// --- FILTRO POR RANGO DE FECHAS ---
function sincronizarEstadoFiltro() {
    let bloqueado = false;
    if (estado.filtro.hasta) {
        const fin = new Date(estado.filtro.hasta + 'T23:59:59');
        bloqueado = fin.getTime() < Date.now() - 3600 * 1000;
    }
    estado.filtro.bloqueado = bloqueado;
    if (bloqueado) {
        estado.live = false;
        estado.showAll = true;
    }
    const check = document.getElementById('metricas-live');
    if (check) check.disabled = bloqueado;
}

export function aplicarFiltroMetricas() {
    const desdeEl = document.getElementById('metricas-desde');
    const hastaEl = document.getElementById('metricas-hasta');
    if (!desdeEl || !hastaEl) return;
    if (desdeEl.value && hastaEl.value && desdeEl.value > hastaEl.value) {
        const tmp = desdeEl.value;
        desdeEl.value = hastaEl.value;
        hastaEl.value = tmp;
    }
    estado.filtro.desde = desdeEl.value || null;
    estado.filtro.hasta = hastaEl.value || null;
    sincronizarEstadoFiltro();
    cargarSerie();
}

export function limpiarFiltroMetricas() {
    const desdeEl = document.getElementById('metricas-desde');
    const hastaEl = document.getElementById('metricas-hasta');
    if (desdeEl) desdeEl.value = '';
    if (hastaEl) hastaEl.value = '';
    estado.filtro = { desde: null, hasta: null, bloqueado: false };
    estado.live = true;
    estado.showAll = false;
    estado.viewStart = maxStart();
    const check = document.getElementById('metricas-live');
    if (check) { check.checked = true; check.disabled = false; }
    sincronizarSlider();
    cargarSerie();
}

function setViewTitle(text) {
    const el = document.getElementById('view-title');
    if (el) el.innerText = text;
}

const TITULOS_METRICAS = {
    accesos: 'Métricas: Actividad de Accesos',
    heatmap: 'Métricas: Mapa de Calor de Tráfico',
    ocupacion: 'Métricas: Ocupación y Reservas',
    recaudacion: 'Métricas: Recaudación',
    ocr: 'Métricas: Tiempos OCR y ALPR'
};

export function abrirMetrica(key) {
    const list = document.getElementById('metricas-list');
    if (list) list.style.display = 'none';
    const cont = (_key) =>
        document.getElementById(_key === 'accesos' ? 'metricas-detail' : `metricas-detail-${_key}`);
    [null, 'accesos', 'heatmap', 'ocupacion', 'recaudacion', 'ocr'].forEach((k) => {
        if (!k) return;
        const el = cont(k);
        if (el) el.style.display = k === key ? 'block' : 'none';
    });
    setViewTitle(TITULOS_METRICAS[key] || 'Métricas');
    if (key === 'accesos') {
        cargarSerie();
        configurarRefresh();
    } else {
        detenerRefresh();
        cargarInforme(key);
    }
}

export function volverMetricas() {
    const list = document.getElementById('metricas-list');
    if (list) list.style.display = 'block';
    ['metricas-detail', 'metricas-detail-heatmap', 'metricas-detail-ocupacion',
        'metricas-detail-recaudacion', 'metricas-detail-ocr'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    setViewTitle('Métricas');
    detenerRefresh();
}

export function verDetalleVisible() {
    if (document.getElementById('metricas-detail')?.style.display === 'block') return 'accesos';
    if (document.getElementById('metricas-detail-heatmap')?.style.display === 'block') return 'heatmap';
    if (document.getElementById('metricas-detail-ocupacion')?.style.display === 'block') return 'ocupacion';
    if (document.getElementById('metricas-detail-recaudacion')?.style.display === 'block') return 'recaudacion';
    if (document.getElementById('metricas-detail-ocr')?.style.display === 'block') return 'ocr';
    return null;
}

export function loadMetricas() {
    const key = verDetalleVisible();
    if (key === 'accesos') {
        setViewTitle(TITULOS_METRICAS.accesos);
        cargarSerie();
    } else if (key) {
        setViewTitle(TITULOS_METRICAS[key] || 'Métricas');
        cargarInforme(key);
    }
}

export function irAlInicio() {
    estado.live = false;
    const check = document.getElementById('metricas-live');
    if (check) check.checked = false;
    estado.viewStart = 0;
    sincronizarSlider();
    renderGrafico();
}

export function irAlFinal() {
    estado.live = true;
    const check = document.getElementById('metricas-live');
    if (check) check.checked = true;
    estado.viewStart = maxStart();
    sincronizarSlider();
    renderGrafico();
}

export function initMetricas() {
    document.getElementById('metricas-live')?.addEventListener('change', (e) => {
        estado.live = e.target.checked;
        if (estado.live) {
            estado.viewStart = maxStart();
            sincronizarSlider();
            renderGrafico();
        }
    });

    document.getElementById('metricas-range')?.addEventListener('input', (e) => {
        estado.viewStart = parseInt(e.target.value, 10);
        estado.live = false;
        const check = document.getElementById('metricas-live');
        if (check) check.checked = false;
        renderGrafico();
    });

    document.getElementById('metricas-ventana')?.addEventListener('change', (e) => {
        setVentana(parseInt(e.target.value, 10));
    });
}