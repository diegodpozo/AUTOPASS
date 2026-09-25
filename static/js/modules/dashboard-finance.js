import api from './api.js';
import * as utils from './utils.js';
import { getVirtualNow } from './virtual-time.js';

/**
 * Módulo de Analítica Financiera y Gráficos del Dashboard
 */

let revenueChart = null;
let currentFinancePage = 1;
const financeLimit = 15;

export function toggleFinanceStatsCollapsible(button) {
    if (!button) return;
    button.classList.toggle('open');
    const content = document.getElementById('finance-stats-collapsible-content');
    if (content) {
        content.classList.toggle('open');
    }
}

export function fitKpiValue(el) {
    if (!el) return;
    const baseSize = parseFloat(getComputedStyle(el).fontSize) || 18;
    el.style.fontSize = '';
    let size = baseSize;
    while (size > 10 && el.scrollWidth > el.clientWidth) {
        size -= 1;
        el.style.fontSize = size + 'px';
    }
}

function setKpi(id, text) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerText = text;
    fitKpiValue(el);
}

export function toggleFinanceDateFilter() {
    const period = document.getElementById('fin-period')?.value;
    const dateGroup = document.getElementById('fin-date-group');
    const dateInput = document.getElementById('fin-date');
    
    if (!dateGroup || !dateInput) return;

    if (period === 'specific') {
        dateGroup.style.display = 'flex';
        if (!dateInput.value) {
            dateInput.value = getVirtualNow().toISOString().split('T')[0];
        }
    } else {
        dateGroup.style.display = 'none';
    }
    loadFinanceData();
}

export function switchMethodTab(method) {
    const container = document.getElementById('metodos-breakdown');
    if (!container) return;
    container.querySelectorAll('.method-tab').forEach(t => t.classList.toggle('active', t.dataset.method === method));
    container.querySelectorAll('.method-panel').forEach(p => p.classList.toggle('active', p.dataset.panel === method));
}

export async function loadFinanceData(resetPage = true) {
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

        if (document.getElementById('fin-total')) setKpi('fin-total', `$${utils.formatNum(data.total_recaudado)}`);
        if (document.getElementById('fin-refunded')) setKpi('fin-refunded', `$${utils.formatNum(data.total_reembolsado)}`);
        if (document.getElementById('fin-count')) setKpi('fin-count', utils.formatNum(data.cantidad_pagos));
        if (document.getElementById('fin-avg')) setKpi('fin-avg', `$${utils.formatNum(data.ticket_promedio)}`);

        const elCash = document.getElementById('fin-cash');
        if (elCash) setKpi('fin-cash', `$${utils.formatNum(data.recaudado_efectivo || 0)}`);

        const elDigital = document.getElementById('fin-digital');
        if (elDigital) setKpi('fin-digital', `$${utils.formatNum(data.recaudado_digital || 0)}`);

        const elProy = document.getElementById('fin-proyectado');
        if (elProy) setKpi('fin-proyectado', `$${utils.formatNum(data.ingresos_proyectados)}`);

        const elCancel = document.getElementById('fin-cancel-rate');
        if (elCancel) elCancel.innerText = `${data.tasa_cancelacion || 0}%`;

        const elNoShow = document.getElementById('fin-noshow');
        if (elNoShow) setKpi('fin-noshow', `$${utils.formatNum(data.ingresos_incumplimiento || 0)}`);

        // DESGLOSE POR CANAL
        const d = data.desglose;
        if (d) {
            const elStayMonto = document.getElementById('fin-stay-monto');
            const elStayCount = document.getElementById('fin-stay-count');
            const elStayAvg = document.getElementById('fin-stay-avg');

            if (elStayMonto) elStayMonto.innerText = `$${utils.formatNum(d.estadias?.monto || 0)}`;
            if (elStayCount) elStayCount.innerText = utils.formatNum(d.estadias?.cantidad || 0);
            if (elStayAvg) elStayAvg.innerText = `$${utils.formatNum(d.estadias?.promedio || 0)}`;

            const elResMonto = document.getElementById('fin-res-monto');
            const elResCount = document.getElementById('fin-res-count');
            const elResAvg = document.getElementById('fin-res-avg');

            if (elResMonto) elResMonto.innerText = `$${utils.formatNum(d.reservas?.monto || 0)}`;
            if (elResCount) elResCount.innerText = utils.formatNum(d.reservas?.cantidad || 0);
            if (elResAvg) elResAvg.innerText = `$${utils.formatNum(d.reservas?.promedio || 0)}`;
        }

        // DESGLOSE POR MÉTODO DE PAGO
        if (Array.isArray(data.desglose_metodos)) {
            data.desglose_metodos.forEach(m => {
                const elMount = document.getElementById(`fin-metodo-${m.metodo}`);
                if (elMount) elMount.innerText = `$${utils.formatNum(m.monto || 0)}`;
                const elCnt = document.getElementById(`fin-metodo-${m.metodo}-cnt`);
                if (elCnt) elCnt.innerText = utils.formatNum(m.cantidad || 0);
            });
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
                
                let metodoPago = utils.metodoPagoReport(p.metodo, p.tipo);

                return `
                <tr class="${rowClass}">
                    <td data-label="Fecha"><span class="text-light">${utils.formatDate(p.fecha_pago)}</span></td>
                    <td data-label="Patente"><span class="plate-style">${p.patente_detectada}</span>${isRefund ? ' <i class="fas fa-undo text-xs"></i>' : ''}</td>
                    <td data-label="Monto" class="text-bold ${amountClass}">$${utils.formatNum(p.costo_estadia)}</td>
                    <td data-label="Método"><span class="text-small">${metodoPago}</span></td>
                    <td data-label="Tipo"><span class="${badgeClass}">${p.tipo.toUpperCase()}</span></td>
                </tr>
            `}).join('') || '<tr><td colspan="5" class="text-center py-20">No hay transacciones en este período.</td></tr>';
        }

        // 3. ACTUALIZAR UI PAGINACION
        const prevBtn = document.getElementById('prev-fin-btn');
        const nextBtn = document.getElementById('next-fin-btn');
        const pageInfo = document.getElementById('fin-page-info');

        if (prevBtn) prevBtn.disabled = currentFinancePage === 1;
        if (nextBtn) nextBtn.disabled = resHist.data.length < financeLimit;
        if (pageInfo) pageInfo.innerText = `Página ${currentFinancePage}`;

        // 4. RENDERIZAR GRAFICO
        const resChart = await api.get(`/reports/payment-history?${urlParams}&limit=0`);
        if (resChart.ok) {
            renderRevenueChart(resChart.data, period);
        }
    }
}

export function nextFinancePage() {
    currentFinancePage++;
    loadFinanceData(false);
}

export function prevFinancePage() {
    if (currentFinancePage > 1) {
        currentFinancePage--;
        loadFinanceData(false);
    }
}

export function renderRevenueChart(data, period) {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (revenueChart) {
        revenueChart.destroy();
        revenueChart = null;
    }

    if (!data || data.length === 0) {
        console.warn("No hay datos para el gráfico financiero");
    }

    const grouped = {};
    
    const parseDate = (str) => {
        if (!str) return new Date(NaN);
        return new Date(str.replace(' ', 'T'));
    };

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

    if (typeof window.Chart !== 'undefined') {
        revenueChart = new window.Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.length > 0 ? labels : ['Sin datos'],
                datasets: [{
                    label: 'Ingresos',
                    data: values.length > 0 ? values : [0],
                    borderColor: '#dfba6b',
                    backgroundColor: 'rgba(223, 186, 107, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#dfba6b',
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
                        titleColor: '#dfba6b',
                        bodyColor: '#fff',
                        borderColor: 'rgba(223, 186, 107, 0.3)',
                        borderWidth: 1,
                        displayColors: false,
                        callbacks: {
                            label: (context) => {
                                const val = context.parsed.y || 0;
                                return ` Recaudado: $${utils.formatNum(val)}`;
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
                            callback: (value) => '$' + utils.formatNum(value)
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
}
