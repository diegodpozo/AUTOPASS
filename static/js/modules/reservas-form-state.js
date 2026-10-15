/**
 * MÓDULO RESERVAS - ESTADO COMPARTIDO
 * Única fuente de verdad del estado mutable del formulario de reservas.
 * Consumido por reservas-form.js (fachada) y por los submódulos temáticos
 * (tarifas y disponibilidad) para evitar ciclos de importación.
 */

const RESERVA_MIN_MS = (window.RESERVA_HORA_MIN_SEGUNDOS || 1800) * 1000;
const RESERVA_MIN_MIN = (window.RESERVA_HORA_MIN_SEGUNDOS || 1800) / 60;

let currentRates = { '30min': 750, hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };
let editingReservaId = null;
let userVehicles = [];
let branchesData = [];
// DESCUENTO DE RESERVA VIGENTE PARA LA SUCURSAL SELECCIONADA (se refleja en el total estimado)
let currentReservationDiscount = { pct: 0, sucursal: '', fetchedFor: '' };
// TOTALES DEL ÚLTIMO CÁLCULO ESTIMADO (original, descuento y final)
let currentReservationTotals = { original: 0, discount: 0, final: 0 };
// COTIZACIÓN VIGENTE DEL FORM (tarifas + duración + total base) que se envía al backend
// para que revalide el precio y lo persista como foto histórica de la reserva.
let currentReservationQuote = { base: 0, horas: 0, tarifaHora: 0, tarifaFraccion: 0, tarifaAplicada: 0 };
// TOKEN ANTI-RACE PARA CONSULTAS CONCURRENTES DE DESCUENTO POR SUCURSAL
let discountFetchToken = 0;
// INSTANCIAS DE FLATPICKR DEL FORMULARIO (fechas deshabilitadas en la grilla)
let fpInstances = {};

export function getCurrentRates() { return currentRates; }
export function setCurrentRates(v) { currentRates = v; }

export function getEditingReservaId() { return editingReservaId; }
export function setEditingReservaId(val) { editingReservaId = val; }

export function getUserVehicles() { return userVehicles; }
export function setUserVehicles(v) { userVehicles = v; }

export function getBranchesData() { return branchesData; }
export function setBranchesData(v) { branchesData = v; }

export function getReservationDiscount() { return currentReservationDiscount; }
export function setReservationDiscount(v) { currentReservationDiscount = v; }

export function getReservationTotals() { return currentReservationTotals; }
export function setReservationTotals(v) { currentReservationTotals = v; }

export function getReservationQuote() { return currentReservationQuote; }
export function setReservationQuote(v) { currentReservationQuote = v; }

export function getDiscountToken() { return discountFetchToken; }
export function bumpDiscountToken() { return ++discountFetchToken; }

export function getFpInstances() { return fpInstances; }

export { RESERVA_MIN_MS, RESERVA_MIN_MIN };
