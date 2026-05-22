/**
 * API MODULE
 * Centralización de peticiones HTTP con manejo de tokens y errores.
 */

const API_BASE = '/v1';

const api = {
    get: (url) => api.request(url, 'GET'),
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
                localStorage.clear();
                window.location.href = '/';
                return null;
            }

            let data = {};
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                const text = await response.text();
                console.error(`Respuesta no-JSON detectada (${response.status}):`, text);
                return { 
                    ok: false, 
                    status: response.status, 
                    error: `Error del servidor (${response.status})`
                };
            }
            
            if (!response.ok) {
                return { 
                    ok: false, 
                    status: response.status, 
                    error: data.detail || 'Error en la petición' 
                };
            }

            return { ok: true, data };
        } catch (error) {
            console.error(`Error en API Client (${method} ${url}):`, error);
            return { ok: false, error: 'Error de conexión con el servidor' };
        }
    }
};

export default api;
