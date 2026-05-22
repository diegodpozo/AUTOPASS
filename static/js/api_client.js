import api from './modules/api.js';

/**
 * BRIDGE: api_client.js
 * Mantiene compatibilidad global con el sistema antiguo mientras migramos a módulos.
 */
window.apiClient = api;
window.API_BASE = '/v1'; // Por si algún script aún lo usa directamente
