/**
 * ESTADISTICAS OCR MODULO
 * DASHBOARD DE ESTADISTICAS DEL SISTEMA ALPR: KPIS, GRÁFICO MÓVIL Y TABLA DE DETALLE.
 */
import api from './api.js';
import { formatTimeSeconds, formatDateTime } from './utils.js';
import { WindowedChart } from './chart-window.js';
import { THEME } from './theme.js';

let todosLosLogs = [];
let intervaloAutoRefresh = null;
let serieOcr = [];

// --- GRÁFICO MÓVIL (controles comunes en chart-window.js) ---
function buildOCRDatasets(pts) {
    const values = pts.map(p => p.y);
    let avg = null;
    let min = null;
    let max = null;
    if (values.length > 0) {
        avg = values.reduce((s, v) => s + v, 0) / values.length;
        const sorted = [...values].sort((a, b) => a - b);
        min = sorted[0];
        max = sorted[sorted.length - 1];
    }
    const flat = (val) => pts.map(p => ({ x: p.x, y: val }));
    return [
        {
            label: 'Tiempo OCR',
            data: pts,
            borderColor: THEME.gold,
            backgroundColor: 'rgba(223, 186, 107, 0.12)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: THEME.gold,
            pointBorderColor: THEME.pointDark,
            pointBorderWidth: 1.5,
            hitRadius: 30
        },
        {
            label: 'Promedio',
            data: flat(avg !== null ? avg : 0),
            borderColor: THEME.accent,
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            pointHoverRadius: 0,
            hitRadius: 14,
            fill: false
        },
        {
            label: 'Máximo',
            data: flat(max !== null ? max : 0),
            borderColor: THEME.danger,
            borderWidth: 1.5,
            borderDash: [2, 3],
            pointRadius: 0,
            pointHoverRadius: 0,
            hitRadius: 14,
            fill: false
        },
        {
            label: 'Mínimo',
            data: flat(min !== null ? min : 0),
            borderColor: THEME.success,
            borderWidth: 1.5,
            borderDash: [2, 3],
            pointRadius: 0,
            pointHoverRadius: 0,
            hitRadius: 14,
            fill: false
        }
    ];
}

const yExtraOcr = {
    title: { display: true, text: 'Segundos', color: THEME.textMuted, font: { size: 10 } },
    ticks: { color: THEME.textMuted, font: { size: 10 }, callback: (v) => v + 's' }
};

const chartOcr = new WindowedChart({
    prefix: 'ocr',
    canvasId: 'ocrChart',
    defaultSpanH: 24,
    buildDatasets: buildOCRDatasets,
    yExtra: yExtraOcr,
    tooltipTitle: (item) => item.datasetIndex === 0 ? `Lectura: ${formatDateTime(new Date(item.parsed.x))}` : item.dataset.label,
    tooltipLabel: (c) => ` ${(c.parsed.y || 0).toFixed(3)} s`
});

// Alimenta el gráfico con la serie filtrada por los inputs de la tabla.
function pushSerieOcr() {
    chartOcr.setSeries(serieFiltrada().map(p => ({ x: p.tMs, y: p.y })));
}

function formatearFecha(isoStr) {
    if (!isoStr) return '--';
    try {
        const d = new Date(isoStr);
        if (isNaN(d.getTime())) {
            return isoStr.replace('T', ' ').substring(0, 19);
        }
        return formatDateTime(d);
    } catch {
        return isoStr;
    }
}

function obtenerBadgeRendimiento(ocrTime) {
    if (ocrTime === null || ocrTime === undefined) {
        return '<span class="text-muted font-mono">--</span>';
    }
    const val = parseFloat(ocrTime);
    let clase = 'perf-fast';
    let icono = 'fa-bolt';
    if (val > 1.5) {
        clase = 'perf-slow';
        icono = 'fa-triangle-exclamation';
    } else if (val > 0.6) {
        clase = 'perf-medium';
        icono = 'fa-gauge';
    }
    return `<span class="perf-badge ${clase}"><i class="fas ${icono}"></i> ${val.toFixed(3)}s</span>`;
}

export async function actualizarEstadisticasOcr() {
    const btnIcon = document.getElementById('refresh-icon');
    if (btnIcon) btnIcon.classList.add('fa-spin');

    const limit = document.getElementById('ocr-limit-select')?.value || 100;
    try {
        const [resStats, resSerie] = await Promise.all([
            api.get(`/reports/ocr-stats?limit=${limit}`),
            api.get('/reports/ocr-activity')
        ]);

        // SERIE COMPLETA PARA EL GRÁFICO MÓVIL (desde el primer dato hasta el último)
        if (resSerie && resSerie.ok && resSerie.data) {
            serieOcr = (resSerie.data.points || []).map(l => ({
                fecha_hora: l.fecha_hora,
                y: parseFloat(l.ocr_time),
                patente: l.patente,
                sucursal: l.sucursal,
                tipo_evento: l.tipo_evento,
                t: new Date(String(l.fecha_hora).replace(' ', 'T'))
            })).filter(p => !isNaN(p.t.getTime()) && !isNaN(p.y))
              .map(p => ({ ...p, tMs: p.t.getTime() }));
        }

        if (resStats && resStats.ok && resStats.data) {
            const { logs, stats } = resStats.data;
            todosLosLogs = logs || [];

            // ACTUALIZAR KPIS
            document.getElementById('kpi-avg').textContent = stats.count > 0 ? `${stats.avg_ocr.toFixed(3)}s` : '--';
            document.getElementById('kpi-min').textContent = stats.count > 0 ? `${stats.min_ocr.toFixed(3)}s` : '--';
            document.getElementById('kpi-max').textContent = stats.count > 0 ? `${stats.max_ocr.toFixed(3)}s` : '--';
            document.getElementById('kpi-p90').textContent = stats.count > 0 ? `${stats.p90_ocr.toFixed(3)}s` : '--';
            document.getElementById('kpi-count').textContent = stats.count ? stats.count.toLocaleString('es-AR') : '0';

            filtrarTablaOcr();
        } else {
            document.getElementById('ocr-table-body').innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: #f43f5e; padding: 30px;">
                        <i class="fas fa-exclamation-circle mr-8"></i> No se pudieron obtener las estadísticas OCR. Verificá tu sesión de administrador.
                    </td>
                </tr>
            `;
        }
    } catch (err) {
        console.error('Error cargando OCR stats:', err);
    } finally {
        if (btnIcon) {
            setTimeout(() => btnIcon.classList.remove('fa-spin'), 400);
        }
    }
}

// SERIE FILTRADA POR LOS MISMOS INPUTS DE LA TABLA (patente/sede + evento)
function serieFiltrada() {
    const texto = (document.getElementById('ocr-search-input')?.value || '').trim().toUpperCase();
    const eventoFiltro = document.getElementById('ocr-filter-evento')?.value || '';
    return serieOcr.filter(p => {
        const coincideTexto = !texto ||
            (p.patente && p.patente.toUpperCase().includes(texto)) ||
            (p.sucursal && p.sucursal.toUpperCase().includes(texto));
        const coincideEvento = !eventoFiltro || p.tipo_evento === eventoFiltro;
        return coincideTexto && coincideEvento;
    });
}

export function filtrarTablaOcr() {
    const texto = (document.getElementById('ocr-search-input')?.value || '').trim().toUpperCase();
    const eventoFiltro = document.getElementById('ocr-filter-evento')?.value || '';

    const filtrados = todosLosLogs.filter(log => {
        const coincideTexto = !texto || 
            (log.patente && log.patente.toUpperCase().includes(texto)) ||
            (log.sucursal && log.sucursal.toUpperCase().includes(texto));
        
        const coincideEvento = !eventoFiltro || log.tipo_evento === eventoFiltro;

        return coincideTexto && coincideEvento;
    });

    pushSerieOcr();

    const countEl = document.getElementById('ocr-table-count');
    if (countEl) {
        countEl.textContent = `Mostrando ${filtrados.length} de ${todosLosLogs.length} registros`;
    }

    const tbody = document.getElementById('ocr-table-body');
    if (!tbody) return;

    if (filtrados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: #6b7280; padding: 40px;">
                    <i class="fas fa-inbox fa-2x mb-10" style="display: block; opacity: 0.5;"></i>
                    No se encontraron registros de reconocimiento OCR para los filtros seleccionados.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtrados.map(l => {
        const esEntrada = l.tipo_evento === 'ENTRADA';
        const badgeEvento = `<span class="event-badge ${esEntrada ? 'event-entrada' : 'event-salida'}">${l.tipo_evento || '--'}</span>`;

        return `
            <tr>
                <td style="font-family: var(--font-mono); color: #6b7280;">#${l.id}</td>
                <td style="font-family: var(--font-mono); font-size: 0.8rem; color: #d1d5db;">${formatearFecha(l.fecha_hora)}</td>
                <td style="font-weight: 800; font-family: var(--font-mono); color: #fff; font-size: 0.95rem;">${l.patente || '--'}</td>
                <td>${badgeEvento}</td>
                <td style="color: #9ca3af;">${l.sucursal || 'Global'}</td>
                <td style="text-align: right;">${obtenerBadgeRendimiento(l.ocr_time)}</td>
            </tr>
        `;
    }).join('');
}

// RELOJ EN VIVO
function actualizarReloj() {
    const clockEl = document.getElementById('ocr-live-clock');
    if (clockEl) {
        const now = new Date();
        clockEl.textContent = formatTimeSeconds(now);
    }
}

// MANEJO DE AUTO-REFRESH
function configurarAutoRefresh() {
    const check = document.getElementById('ocr-autorefresh');
    if (intervaloAutoRefresh) clearInterval(intervaloAutoRefresh);

    if (check && check.checked) {
        intervaloAutoRefresh = setInterval(actualizarEstadisticasOcr, 5000);
    }
}

export function initEstadisticasOcr() {
    document.getElementById('ocr-autorefresh')?.addEventListener('change', configurarAutoRefresh);

    setInterval(actualizarReloj, 1000);
    actualizarReloj();
    actualizarEstadisticasOcr();
    configurarAutoRefresh();
}