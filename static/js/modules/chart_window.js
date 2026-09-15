import { formatTime, formatDateTime, formatDayTime } from './utils.js';

const HOUR_MS = 3600000;

export class WindowedChart {
    /**
     * Controles comunes de los gráficos de métricas (seguir en vivo, ventana,
     * INICIO/FINAL y deslizador) + construcción del gráfico con eje X de
     * tiempo real (escala lineal).
     *
     * La página solo debe: instanciar, alimentar la serie con setSeries()
     * (ya filtrada si corresponde) y el resto (timers/refresco) es suyo.
     *
     * @param {Object} opts
     * @param {string} opts.prefix        Prefijo de ids de los controles (p.ej. "metricas" o "ocr-chart")
     * @param {string} opts.canvasId      Id del canvas de Chart.js
     * @param {number} [opts.defaultSpanH=24] Ventana inicial en horas (0 = toda la historia)
     * @param {Function} opts.buildDatasets Puntos visibles -> datasets de Chart.js
     * @param {Function} [opts.tooltipTitle] (item, Date) -> título del tooltip
     * @param {Function} [opts.tooltipLabel] (context) -> etiqueta del tooltip
     * @param {Object} [opts.yExtra]        Props extra para la escala Y (title, ticks...)
     */
    constructor(opts) {
        this.prefix = opts.prefix;
        this.canvas = document.getElementById(opts.canvasId);
        this.buildDatasets = opts.buildDatasets;
        this.tooltipTitle = opts.tooltipTitle || null;
        this.tooltipLabel = opts.tooltipLabel || null;
        this.yExtra = opts.yExtra || {};

        this.series = [];
        this.live = true;
        this.showAll = opts.defaultSpanH === 0;
        this.spanMs = (opts.defaultSpanH || 24) * HOUR_MS;
        this.endMs = null;

        this.chart = null;
        this._el = null;
        this._wire();
    }

    _on(id) { return document.getElementById(`${this.prefix}-${id}`); }

    _wire() {
        const live = this._on('chart-live');
        const ventana = this._on('chart-ventana');
        const inicio = this._on('chart-ir-inicio');
        const final = this._on('chart-ir-final');
        const range = this._on('chart-range');

        this._el = { live, ventana, inicio, final, range };

        live?.addEventListener('change', (e) => {
            this.live = e.target.checked;
            if (this.live) this.endMs = null;
            this.render();
        });

        ventana?.addEventListener('change', (e) => {
            this.updateSpan(parseInt(e.target.value, 10));
        });

        inicio?.addEventListener('click', () => this.irInicio());
        final?.addEventListener('click', () => this.irFinal());

        range?.addEventListener('input', (e) => {
            this.live = false;
            if (this._el.live) this._el.live.checked = false;
            this.endMs = parseFloat(e.target.value);
            this.render();
        });
    }

    /** Reemplaza la serie (debe estar ordenada +/- y con puntos {x, y}). */
    setSeries(points) {
        this.series = (points || []).slice().sort((a, b) => a.x - b.x);
        if (this.live) this.endMs = null;
        this.render();
    }

    liveSiguiente(bool) {
        this.live = !!bool;
        if (this._el.live) this._el.live.checked = this.live;
        if (this.live) this.endMs = null;
        this.render();
    }

    updateSpan(horas) {
        if (horas === 0) {
            this.showAll = true;
        } else {
            this.showAll = false;
            this.spanMs = horas * HOUR_MS;
        }
        if (this.live) this.endMs = null;
        this.render();
    }

    irInicio() {
        this.liveSiguiente(false);
        const rng = this._range();
        if (rng) this.endMs = rng.minEnd;
        this.render();
    }

    irFinal() {
        this.liveSiguiente(true);
        this.endMs = null;
        this.render();
    }

    destroy() {
        if (this.chart) { this.chart.destroy(); this.chart = null; }
        this.series = [];
    }

    _range() {
        if (!this.series.length || this.showAll) return null;
        const firstT = this.series[0].x;
        const lastT = this.series[this.series.length - 1].x;
        const span = this.spanMs;
        const pad = Math.min(span * 0.05, 2 * HOUR_MS);
        const minEnd = firstT + span;
        const maxEnd = Math.max(minEnd, lastT + pad);
        let end = this.live ? maxEnd : (this.endMs ?? maxEnd);
        end = Math.max(minEnd, Math.min(end, maxEnd));
        return { end, minEnd, maxEnd, span };
    }

    _visible() {
        if (!this.series.length) return [];
        const rng = this._range();
        if (!rng) return this.series.slice();
        return this.series.filter((p) => p.x >= rng.end - rng.span && p.x <= rng.end);
    }

    _syncSlider() {
        const slider = this._el?.range;
        if (!slider) return;
        const rng = this._range();
        if (!rng) {
            slider.min = 0;
            slider.max = 0;
            slider.value = 0;
            slider.disabled = true;
            return;
        }
        slider.min = rng.minEnd;
        slider.max = rng.maxEnd;
        slider.value = Math.max(rng.minEnd, Math.min(rng.end, rng.maxEnd));
        slider.disabled = false;
    }

    render() {
        const canvas = this.canvas;
        if (!canvas || typeof window.Chart === 'undefined') return;
        const ctx = canvas.getContext('2d');
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        this._syncSlider();
        const pts = this._visible();

        if (!pts.length) {
            this.chart = new window.Chart(ctx, {
                type: 'line',
                data: { datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { type: 'linear', min: 0, max: 1, grid: { display: false }, ticks: { display: false } },
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { display: false } }
                    }
                }
            });
            return;
        }

        const xs = pts.map((p) => p.x);
        const xMin = Math.min(...xs);
        const xMax = Math.max(...xs);
        const rangeMs = xMax - xMin;
        const padMs = Math.max(1, rangeMs * 0.03);
        const tickFmt = (v) => {
            const d = new Date(v);
            return rangeMs > 2 * 86400000 ? formatDayTime(d) : formatTime(d);
        };

        const datasets = this.buildDatasets(pts);
        this.chart = new window.Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'nearest', intersect: false, axis: 'xy', includeInvisible: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0a0a0a',
                        titleColor: '#C5A059',
                        bodyColor: '#fff',
                        borderColor: 'rgba(197, 160, 89, 0.3)',
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
                                return this.tooltipTitle
                                    ? this.tooltipTitle(it, new Date(it.parsed.x))
                                    : formatDateTime(new Date(it.parsed.x));
                            },
                            label: this.tooltipLabel || ((c) => ` ${c.dataset.label}: ${c.parsed.y}`)
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: false, text: '', color: '#666', font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                        ticks: { color: '#666', font: { size: 10 } },
                        ...this.yExtra
                    },
                    x: {
                        type: 'linear',
                        min: xMin - padMs,
                        max: xMax + padMs,
                        grid: { display: false },
                        ticks: {
                            color: '#666',
                            font: { size: 9 },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 10,
                            callback: tickFmt
                        }
                    }
                }
            }
        });
    }
}