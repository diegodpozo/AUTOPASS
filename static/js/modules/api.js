/**
 * API MODULO
 * CENTRALIZACION DE PETICIONES HTTP CON MANEJO DE TOKENS Y ERRORES.
 */

const API_BASE = '/v1';

const api = {
    get: (url, opts = {}) => {
        let finalUrl = url;
        if (opts.params) {
            const qs = Object.entries(opts.params)
                .filter(([_, v]) => v !== undefined && v !== null)
                .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
                .join('&');
            if (qs) finalUrl += `?${qs}`;
        }
        return api.request(finalUrl, 'GET');
    },
    post: (url, body) => api.request(url, 'POST', body),
    put: (url, body) => api.request(url, 'PUT', body),
    patch: (url, body) => api.request(url, 'PATCH', body),
    delete: (url) => api.request(url, 'DELETE'),

    async request(url, method, body = null) {
        const token = localStorage.getItem('token');
        const headers = {
            'Authorization': token ? `Bearer ${token}` : ''
        };

        if (body && !(body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        const options = {
            method,
            headers,
            body: body ? (body instanceof FormData ? body : JSON.stringify(body)) : null
        };

        try {
            const response = await fetch(`${API_BASE}${url}`, options);
            
            if (response.status === 401 && token) {
                console.warn('Sesión expirada.');
                const savedKeys = {};
                const keepPrefixes = ['autopass_tour_seen_', 'seen_reservation_onboarding'];
                const keepExact = ['autopass_device_id'];

                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (!key) continue;
                    if (keepExact.includes(key) || keepPrefixes.some(p => key.startsWith(p))) {
                        savedKeys[key] = localStorage.getItem(key);
                    }
                }

                localStorage.clear();
                Object.keys(savedKeys).forEach(k => localStorage.setItem(k, savedKeys[k]));

                window.location.href = '/';
                return null;
            }

            // 204 NO CONTENT - EXITO SIN CUERPO
            if (response.status === 204) {
                return { ok: true, data: {} };
            }

            if (!response.ok) {
                let detail = '';
                try {
                    const d = await response.json();
                    detail = d.detail || '';
                    if (Array.isArray(detail)) {
                        detail = detail.map(e => `${e.loc?.slice(-1)[0]}: ${e.msg}`).join('; ');
                    }
                } catch(e) {}
                return { 
                    ok: false, 
                    status: response.status, 
                    error: detail || 'Error en la petición' 
                };
            }

            let data = {};
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            }

            return { ok: true, data };
        } catch (error) {
            console.error(`Error en API Client (${method} ${url}):`, error);
            return { ok: false, error: 'Error de conexión con el servidor' };
        }
    }
};

export default api;
