import { showToast } from './utils.js';

// ESCAPAR CARACTERES ESPECIALES DE HTML
function EscaparHtml(Texto) {
    return String(Texto).replace(/[&<>"']/g, Caracter => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[Caracter]);
}

// OBTENER TITULO DEL REPORTE SEGUN BOTON O CONTENEDOR
function ObtenerTituloReporte(Boton, Destino, DestinoId) {
    if (DestinoId === 'metricas-detail-heatmap') {
        const titleEl = Destino.querySelector('.heatmap-nav-title');
        let mesTexto = '';
        if (titleEl) {
            mesTexto = titleEl.textContent
                .replace(/[\u2022•\u00b7].*$/i, '')
                .replace(/semana.*$/i, '')
                .replace(/\s+/g, ' ')
                .trim();
        }
        if (!mesTexto) mesTexto = 'Mes';

        const activeWeekBtn = Destino.querySelector('.heatmap-week-btn--active');
        const weekVal = activeWeekBtn?.dataset?.week;

        if (weekVal && weekVal !== 'todas') {
            return `Mapa de trafico ${mesTexto} Semana ${weekVal}`;
        }
        return `Mapa de trafico ${mesTexto}`;
    }

    return Boton?.dataset?.reportTitle
        || Destino.querySelector('.metrica-detail-breadcrumb')?.textContent.trim()
        || Destino.querySelector('h1, h2, h3')?.textContent.trim()
        || 'INFORME AUTOPASS';
}

// EXTRAER FILTROS ACTIVOS VISIBLES EN EL DASHBOARD
function ExtraerFiltrosActivos(DestinoId, Destino) {
    const Filtros = [];

    // 1. SUCURSAL SELECCIONADA
    const SelectorSucursal = Destino.querySelector('#hm-sucursal, #occ-sucursal, #fin-sucursal, select[id*="sucursal"]')
        || document.querySelector('#hm-sucursal, #occ-sucursal, #fin-sucursal');
    let TextoSucursal = '';
    if (SelectorSucursal && SelectorSucursal.selectedIndex >= 0) {
        TextoSucursal = SelectorSucursal.options[SelectorSucursal.selectedIndex]?.textContent?.trim() || '';
    }
    if (!TextoSucursal || TextoSucursal === 'TODAS' || TextoSucursal.includes('Cargando')) {
        const SucursalLocal = localStorage.getItem('sucursal');
        TextoSucursal = (SucursalLocal && SucursalLocal !== 'null') ? SucursalLocal : 'TODAS LAS SUCURSALES';
    }
    Filtros.push({ Etiqueta: 'SUCURSAL', Valor: TextoSucursal });

    // 2. PERIODO Y FECHA EXACTA (REPORTE FINANCIERO)
    const SelectorPeriodo = Destino.querySelector('#fin-period') || document.getElementById('fin-period');
    if (SelectorPeriodo && DestinoId === 'tab-finance') {
        const TextoPeriodo = SelectorPeriodo.options[SelectorPeriodo.selectedIndex]?.textContent?.trim() || 'TODA LA HISTORIA';
        const InputFechaEspecifica = Destino.querySelector('#fin-date') || document.getElementById('fin-date');
        if (SelectorPeriodo.value === 'specific' && InputFechaEspecifica?.value) {
            Filtros.push({ Etiqueta: 'PERIODO', Valor: `FECHA EXACTA (${InputFechaEspecifica.value})` });
        } else {
            Filtros.push({ Etiqueta: 'PERIODO', Valor: TextoPeriodo });
        }
    }

    // 3. RANGOS DESDE / HASTA (METRICAS E INFORMES)
    const InputDesde = Destino.querySelector('input[id$="-desde"]') || document.querySelector(`#${DestinoId} input[id$="-desde"]`);
    const InputHasta = Destino.querySelector('input[id$="-hasta"]') || document.querySelector(`#${DestinoId} input[id$="-hasta"]`);
    if (InputDesde?.value || InputHasta?.value) {
        const Tramo = `${InputDesde?.value || 'INICIO'} -> ${InputHasta?.value || 'ACTUAL'}`;
        Filtros.push({ Etiqueta: 'RANGO DE FECHAS', Valor: Tramo });
    }

    // 4. TIPO DE VEHICULO
    const SelectorVehiculo = Destino.querySelector('#fin-vehicle-type') || document.getElementById('fin-vehicle-type');
    if (SelectorVehiculo && DestinoId === 'tab-finance') {
        const TextoVehiculo = SelectorVehiculo.options[SelectorVehiculo.selectedIndex]?.textContent?.trim() || 'TODOS LOS VEHICULOS';
        Filtros.push({ Etiqueta: 'TIPO DE VEHICULO', Valor: TextoVehiculo });
    }

    // 5. METODO DE PAGO
    const SelectorPago = Destino.querySelector('#fin-payment-method') || document.getElementById('fin-payment-method');
    if (SelectorPago && DestinoId === 'tab-finance') {
        const TextoPago = SelectorPago.options[SelectorPago.selectedIndex]?.textContent?.trim() || 'TODOS LOS METODOS';
        Filtros.push({ Etiqueta: 'METODO DE PAGO', Valor: TextoPago });
    }

    // 6. VENTANA TEMPORAL Y MODO EN VIVO (ACTIVIDAD DE ACCESOS / OCR)
    const SelectorVentana = Destino.querySelector('#metricas-ventana, select[id$="-ventana"]');
    if (SelectorVentana) {
        const TextoVentana = SelectorVentana.options[SelectorVentana.selectedIndex]?.textContent?.trim() || '';
        if (TextoVentana) Filtros.push({ Etiqueta: 'VENTANA TEMPORAL', Valor: TextoVentana });
    }
    const CheckEnVivo = Destino.querySelector('#metricas-live');
    if (CheckEnVivo) {
        Filtros.push({ Etiqueta: 'MODALIDAD', Valor: CheckEnVivo.checked ? 'SEGUIMIENTO EN VIVO' : 'HISTORICO FIJO' });
    }

    // 7. VISTA ACTIVA EN MAPA DE CALOR (CALOR VS BARRAS)
    if (DestinoId === 'metricas-detail-heatmap') {
        const BotonBarrasActivo = Destino.querySelector('.hm-view-btn--active[data-hm-view="barras"]')
            || document.querySelector('#metricas-detail-heatmap .hm-view-btn--active[data-hm-view="barras"]');
        const ModoVista = BotonBarrasActivo ? 'GRAFICO DE BARRAS POR TRAMO HORARIO' : 'MAPA DE CALOR (MATRIZ DIARIA)';
        Filtros.push({ Etiqueta: 'VISTA SELECCIONADA', Valor: ModoVista });
    }

    return Filtros;
}

// OBTENER METADATOS GENERALES DEL INFORME
function ObtenerMetadatosInforme(DestinoId, Destino) {
    const Filtros = ExtraerFiltrosActivos(DestinoId, Destino);
    const SucursalFiltro = Filtros.find(Item => Item.Etiqueta === 'SUCURSAL')?.Valor
        || localStorage.getItem('sucursal')
        || 'TODAS LAS SUCURSALES';

    const NombreUsuario = [localStorage.getItem('nombre'), localStorage.getItem('apellido')]
        .filter(Boolean).join(' ').trim().toUpperCase() || 'USUARIO AUTENTICADO';

    const FechaEmision = new Intl.DateTimeFormat('es-AR', {
        dateStyle: 'short', timeStyle: 'medium'
    }).format(new Date()).toUpperCase();

    return {
        Sucursal: SucursalFiltro,
        Usuario: NombreUsuario,
        FechaEmision: FechaEmision,
        Filtros: Filtros
    };
}

// CONVERTIR CANVAS A IMAGEN PNG CON FONDO OSCURO EN ALTA RESOLUCION
function ObtenerImagenCanvasConFondo(CanvasOriginal) {
    if (!CanvasOriginal) return '';
    const AnchoOriginal = CanvasOriginal.width || 800;
    const AltoOriginal = CanvasOriginal.height || 400;

    // ESCALAR PARA GARANTIZAR MAXIMA NITIDEZ EN A4 Y PANTALLAS RETINA
    const FactorEscala = Math.max(1, Math.min(2.5, 1800 / AnchoOriginal));
    const CanvasSalida = document.createElement('canvas');
    CanvasSalida.width = Math.round(AnchoOriginal * FactorEscala);
    CanvasSalida.height = Math.round(AltoOriginal * FactorEscala);

    const ContextoSalida = CanvasSalida.getContext('2d');
    if (!ContextoSalida) {
        return CanvasOriginal.toDataURL('image/png', 1.0);
    }

    // APLICAR FONDO OSCURO DEL TEMA AUTOPASS (#11141B)
    ContextoSalida.fillStyle = '#11141b';
    ContextoSalida.fillRect(0, 0, CanvasSalida.width, CanvasSalida.height);

    // DIBUJAR CONTENIDO DEL GRAFICO
    ContextoSalida.imageSmoothingEnabled = true;
    ContextoSalida.imageSmoothingQuality = 'high';
    ContextoSalida.drawImage(CanvasOriginal, 0, 0, CanvasSalida.width, CanvasSalida.height);

    return CanvasSalida.toDataURL('image/png', 1.0);
}

// REEMPLAZAR CANVASES POR IMAGENES RESPONSIVAS A ANCHO COMPLETO
function IncrustarCanvasesRenderizados(Origen, Clon) {
    const Originales = Origen.querySelectorAll('canvas');
    const Copias = Clon.querySelectorAll('canvas');

    Originales.forEach((Canvas, Indice) => {
        const Copia = Copias[Indice];
        if (!Copia) return;

        const DataUrl = ObtenerImagenCanvasConFondo(Canvas);
        const Imagen = document.createElement('img');
        Imagen.className = 'report-chart-image';
        Imagen.alt = Canvas.getAttribute('aria-label') || 'GRAFICO DEL INFORME';
        Imagen.src = DataUrl;

        // OCUPAR 100% DEL ANCHO DEL CONTENEDOR Y ESCALADO PROPORCIONAL
        Imagen.style.cssText = [
            'display: block !important',
            'width: 100% !important',
            'max-width: 100% !important',
            'height: auto !important',
            'margin: 0 auto !important',
            'border-radius: 8px !important',
            'object-fit: contain !important'
        ].join(';');

        Copia.replaceWith(Imagen);
    });
}

// CLONAR EL ELEMENTO DEL REPORTE Y LIMPIAR CONTROLES INTERACTIVOS
function ClonarReporte(DestinoId, Destino) {
    const Clon = Destino.cloneNode(true);
    Clon.style.setProperty('display', 'block', 'important');

    // REMOVER BOTONES DE EXPORTACION Y NAVEGACION DENTRO DEL CONTENIDO
    Clon.querySelectorAll('.report-export-group, .report-html-export, .report-pdf-export, .metricas-detail-top, .metricas-back-btn, .heatmap-nav-btn, .heatmap-nav-weeks')
        .forEach(Elemento => Elemento.remove());

    // LIMPIEZA ESPECIFICA PARA METRICAS DETAIL
    const EsMetricaDetail = /^metricas-detail(?:-|$)/.test(DestinoId || '');
    if (EsMetricaDetail) {
        Clon.querySelectorAll('.metricas-controls, .metricas-controls-row, .metricas-range-wrap, .metricas-helper, .chart-window-controls, .chart-window-toolbar')
            .forEach(Elemento => Elemento.remove());
    }

    // MANEJO ESPECIFICO PARA REPORTE FINANCIERO
    if (DestinoId === 'tab-finance') {
        Clon.querySelectorAll('.finance-report-export-row, .pagination-premium, #prev-fin-btn, #next-fin-btn')
            .forEach(Elemento => Elemento.remove());

        // ASEGURAR QUE EL RESUMEN COLAPSIBLE ESTE EXPANDIDO Y VISIBLE
        const ContenidoColapsable = Clon.querySelector('#finance-stats-collapsible-content');
        if (ContenidoColapsable) {
            ContenidoColapsable.style.setProperty('display', 'block', 'important');
            ContenidoColapsable.style.setProperty('max-height', 'none', 'important');
            ContenidoColapsable.style.setProperty('opacity', '1', 'important');
            ContenidoColapsable.style.setProperty('visibility', 'visible', 'important');
        }
        const DisparadorColapsable = Clon.querySelector('.user-stats-trigger');
        if (DisparadorColapsable) {
            DisparadorColapsable.remove();
        }

        // LIMPIAR CONTROLES DENTRO DEL HEADER DEL GRAFICO (SUS VALORES VAN EN LOS FILTROS)
        const ControlesGraficoFin = Clon.querySelector('.finance-analytics-row .header-actions');
        if (ControlesGraficoFin) {
            ControlesGraficoFin.remove();
        }
    }

    // MANEJO ESPECIFICO PARA MAPA DE CALOR
    if (DestinoId === 'metricas-detail-heatmap') {
        Clon.querySelectorAll('.hm-view-toggle').forEach(Elemento => Elemento.remove());
        // SI SE ENCONTRABA EN MODO BARRAS, ASEGURAR QUE EL VIEWPORT OCUPE ANCHO COMPLETO
        Clon.querySelectorAll('.hm-barras-viewport').forEach(Viewport => {
            Viewport.style.setProperty('width', '100%', 'important');
            Viewport.style.setProperty('max-width', '100%', 'important');
            Viewport.style.setProperty('overflow', 'visible', 'important');
        });
    }

    // MANEJO ESPECIFICO PARA RECAUDACION (VENTAS POR SUCURSAL)
    if (DestinoId === 'metricas-detail-recaudacion') {
        const TarjetaSucursalOriginal = Destino.querySelector('#fin-por-sucursal-card');
        const TarjetaSucursalClon = Clon.querySelector('#fin-por-sucursal-card');
        if (TarjetaSucursalOriginal && TarjetaSucursalClon) {
            if (TarjetaSucursalOriginal.hidden || TarjetaSucursalOriginal.style.display === 'none') {
                TarjetaSucursalClon.remove();
            } else {
                TarjetaSucursalClon.removeAttribute('hidden');
                TarjetaSucursalClon.style.setProperty('display', 'block', 'important');
            }
        }
    }

    // INCRUSTAR IMAGENES DE TODOS LOS CANVASES
    IncrustarCanvasesRenderizados(Destino, Clon);

    // PRESERVAR VALORES DE INPUTS Y SELECTS EN EL CLON
    Clon.querySelectorAll('input').forEach(Input => {
        Input.setAttribute('value', Input.value);
        if (Input.type === 'checkbox' || Input.type === 'radio') {
            if (Input.checked) Input.setAttribute('checked', 'checked');
            else Input.removeAttribute('checked');
        }
    });

    Clon.querySelectorAll('select').forEach((SelectOriginal, Indice) => {
        const SelectClon = Clon.querySelectorAll('select')[Indice];
        if (SelectClon) {
            [...SelectClon.options].forEach((Opcion, IndiceOpcion) => {
                if (IndiceOpcion === SelectOriginal.selectedIndex) Opcion.setAttribute('selected', 'selected');
                else Opcion.removeAttribute('selected');
            });
        }
    });

    // ELIMINAR ELEMENTOS OCULTOS
    Clon.querySelectorAll('[hidden]').forEach(Elemento => {
        if (Elemento.hidden) Elemento.remove();
    });

    return Clon;
}

// AJUSTAR URLS DENTRO DE HOJAS DE ESTILO
function IncrustarUrlsCss(CssTexto, CssUrl) {
    return CssTexto.replace(/url\(\s*(['"]?)(?!data:|https?:|#)([^)'"\s]+)\1\s*\)/gi, (Coincidencia, Comilla, Ruta) => {
        try {
            return `url("${new URL(Ruta, CssUrl).href}")`;
        } catch {
            return Coincidencia;
        }
    });
}

// RECOLECTAR Y COMPILAR TODAS LAS HOJAS DE ESTILO
async function ObtenerMarcadoHojasEstilo() {
    const Bloques = [...document.querySelectorAll('link[rel="stylesheet"]')].map(async Enlace => {
        const Href = new URL(Enlace.getAttribute('href'), document.baseURI).href;
        try {
            const Respuesta = await fetch(Href, { credentials: 'same-origin' });
            if (!Respuesta.ok) throw new Error(`HTTP ${Respuesta.status}`);
            const Css = IncrustarUrlsCss(await Respuesta.text(), Href);
            return `<style data-fuente="${EscaparHtml(Href)}">${Css.replace(/<\/style/gi, '<\\/style')}</style>`;
        } catch (Error) {
            console.warn('CSS NO INCRUSTADO; SE MANTIENE ENLACE REMOTO:', Href, Error);
            return `<link rel="stylesheet" href="${EscaparHtml(Href)}">`;
        }
    });
    const EstilosEnLinea = [...document.querySelectorAll('style')].map(Estilo => Estilo.outerHTML);
    return `${(await Promise.all(Bloques)).join('\n')}\n${EstilosEnLinea.join('\n')}`;
}

// INCRUSTAR IMAGENES EXTERNAS A DATA URL BASE64
async function IncrustarFuentesImagenes(ElementoRaiz) {
    const Imagenes = [...ElementoRaiz.querySelectorAll('img')];
    await Promise.all(Imagenes.map(async Imagen => {
        if (!Imagen.src || Imagen.src.startsWith('data:')) return;
        try {
            const Respuesta = await fetch(Imagen.src, { credentials: 'same-origin' });
            if (!Respuesta.ok) throw new Error(`HTTP ${Respuesta.status}`);
            const BlobImagen = await Respuesta.blob();
            Imagen.src = await new Promise((Resolver, Rechazar) => {
                const Lector = new FileReader();
                Lector.onload = () => Resolver(Lector.result);
                Lector.onerror = Rechazar;
                Lector.readAsDataURL(BlobImagen);
            });
        } catch (Error) {
            console.warn('IMAGEN NO INCRUSTADA EN REPORTE:', Imagen.src, Error);
        }
    }));
}

// CONSTRUIR ESTRUCTURA PRINCIPAL DEL REPORTE
function ConstruirCarcasaInforme(DestinoId, Clon, Titulo, Metadatos, LogoDataUrl) {
    const Principal = document.createElement('main');
    Principal.className = 'content dashboard-content report-export-document';
    if (DestinoId === 'metricas-detail-heatmap') Principal.classList.add('report-export-heatmap');

    Principal.innerHTML = `
      <!-- BARRA DE HERRAMIENTAS (SOLO VISIBLE EN PANTALLA) -->
      <div class="report-export-toolbar" role="toolbar" aria-label="ACCIONES DEL INFORME">
        <div class="toolbar-info">
          <i class="fas fa-file-invoice" aria-hidden="true"></i> AUTOPASS &bull; EXPORTACION DE INFORME
        </div>
        <div class="toolbar-actions">
          <button type="button" class="toolbar-btn toolbar-btn--pdf" onclick="window.print()" title="IMPRIMIR O GUARDAR COMO PDF EN HOJA A4 VERTICAL">
            <i class="fas fa-print" aria-hidden="true"></i> IMPRIMIR / GUARDAR PDF (A4)
          </button>
        </div>
      </div>

      <!-- ENCABEZADO OFICIAL -->
      <header class="report-export-header">
        <div class="report-export-brand">
          <img src="${LogoDataUrl}" alt="AUTOPASS">
          <div class="brand-text">
            <strong>AUTOPASS</strong>
            <span class="brand-sub">SISTEMA INTEGRAL DE CONTROL Y GESTION</span>
          </div>
        </div>
        <div class="report-export-meta">
          <h1>${EscaparHtml(Titulo)}</h1>
          <div class="meta-row">
            <span><i class="fas fa-building" aria-hidden="true"></i> SUCURSAL: ${EscaparHtml(Metadatos.Sucursal)}</span>
            <span><i class="fas fa-user" aria-hidden="true"></i> EMITIDO POR: ${EscaparHtml(Metadatos.Usuario)}</span>
            <span><i class="fas fa-clock" aria-hidden="true"></i> FECHA: ${EscaparHtml(Metadatos.FechaEmision)}</span>
          </div>
        </div>
      </header>`;

    Clon.style.setProperty('display', 'block', 'important');
    if (DestinoId === 'tab-metricas') {
        const Seccion = document.createElement('section');
        Seccion.id = 'tab-metricas';
        Seccion.className = 'tab-view';
        const Lista = Clon.querySelector('#metricas-list');
        if (Lista) Seccion.append(Lista.cloneNode(true));
        const Envoltura = Clon.querySelector('#metricas-detail-wrap') || document.createElement('div');
        Envoltura.id = 'metricas-detail-wrap';
        const Detalle = Clon.querySelector('#metricas-detail');
        if (Detalle) {
            Detalle.style.setProperty('display', 'block', 'important');
            Envoltura.append(Detalle.cloneNode(true));
        }
        Seccion.append(Envoltura);
        Principal.append(Seccion);
    } else {
        if (Clon.classList.contains('metrica-detail-view')) {
            Clon.style.setProperty('display', 'block', 'important');
        }
        Principal.append(Clon);
    }

    return Principal;
}

// GENERAR DOCUMENTO HTML AUTOSUFICIENTE
async function ConstruirHtmlAutosuficiente(DestinoId, Destino, Boton, AutoImprimir = false) {
    const Titulo = ObtenerTituloReporte(Boton, Destino, DestinoId);
    const Metadatos = ObtenerMetadatosInforme(DestinoId, Destino);
    const Clon = ClonarReporte(DestinoId, Destino);

    // OBTENER LOGO EN BASE64
    let LogoDataUrl = '';
    try {
        const RespuestaLogo = await fetch(new URL('/static/images/logo.png', document.baseURI), { credentials: 'same-origin' });
        const BlobLogo = await RespuestaLogo.blob();
        LogoDataUrl = await new Promise((Resolver, Rechazar) => {
            const Lector = new FileReader();
            Lector.onload = () => Resolver(Lector.result);
            Lector.onerror = Rechazar;
            Lector.readAsDataURL(BlobLogo);
        });
    } catch (ErrorLogo) {
        console.warn('NO SE PUDO CARGAR EL LOGO EN BASE64:', ErrorLogo);
        LogoDataUrl = '/static/images/logo.png';
    }

    const Carcasa = ConstruirCarcasaInforme(DestinoId, Clon, Titulo, Metadatos, LogoDataUrl);
    await IncrustarFuentesImagenes(Carcasa);

    const ClasesCuerpo = document.body.className.split(/\s+/).filter(Nombre => Nombre.startsWith('role-')).join(' ');
    const EstilosGlobales = await ObtenerMarcadoHojasEstilo();

    return `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${EscaparHtml(Titulo)}</title>
${EstilosGlobales}
<style>
/* REGLAS BASE DE PRESENTACION */
*, *:before, *:after { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  min-height: 100%;
  background: #0b0d12;
  color: #f5f6f8;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
body {
  padding: 24px 28px;
}

/* BARRA DE ACCIONES SUPERIOR (SOLO EN PANTALLA) */
.report-export-toolbar {
  position: sticky;
  top: 12px;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  margin-bottom: 24px;
  background: #151922;
  border: 1px solid rgba(223, 186, 107, 0.4);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}
.report-export-toolbar .toolbar-info {
  font-size: 13px;
  font-weight: 700;
  color: #dfba6b;
  letter-spacing: 0.5px;
}
.report-export-toolbar .toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.report-export-toolbar .toolbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  background: #f43f5e;
  color: #ffffff;
  transition: opacity 0.2s ease;
}
.report-export-toolbar .toolbar-btn:hover {
  opacity: 0.9;
}

/* CONTENEDOR PRINCIPAL */
.report-export-document {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 auto !important;
  padding: 0 !important;
  overflow: visible !important;
}

/* ENCABEZADO */
.report-export-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 20px 24px;
  margin-bottom: 16px;
  background: #11141b;
  border: 1px solid rgba(223, 186, 107, 0.3);
  border-radius: 14px;
}
.report-export-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 0 0 auto;
}
.report-export-brand img {
  width: 58px;
  height: 58px;
  object-fit: contain;
}
.report-export-brand strong {
  display: block;
  font-size: 22px;
  color: #dfba6b;
  letter-spacing: 1px;
}
.report-export-brand .brand-sub {
  display: block;
  font-size: 10px;
  color: #9ca3af;
  letter-spacing: 0.5px;
}
.report-export-meta {
  flex: 1 1 auto;
  min-width: 0;
}
.report-export-meta h1 {
  margin: 0 0 8px 0;
  font-size: 22px;
  color: #f5f6f8;
  font-weight: 800;
  letter-spacing: 0.5px;
}
.report-export-meta .meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 20px;
}
.report-export-meta span {
  font-size: 12px;
  color: #c4c9d2;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* BARRA DE FILTROS ACTIVOS */
.report-export-filters-bar {
  background: #131720;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-left: 4px solid #dfba6b;
  border-radius: 10px;
  padding: 12px 18px;
  margin-bottom: 20px;
}
.filters-bar-title {
  font-size: 11px;
  font-weight: 800;
  color: #dfba6b;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.filters-bar-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}
.report-filter-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 20px;
  background: #1a1f2c;
  border: 1px solid rgba(223, 186, 107, 0.25);
  font-size: 12px;
  color: #f5f6f8;
}
.report-filter-badge strong {
  color: #dfba6b;
  font-size: 11px;
  letter-spacing: 0.3px;
}

/* GRAFICOS Y CONTENEDORES A ANCHO TOTAL */
.report-export-document .card,
.report-export-document .channel-card {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  margin-bottom: 20px !important;
}
.report-export-document .chart-wrapper,
.report-export-document .metricas-chart-body,
.report-export-document .channel-body {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  height: auto !important;
  min-height: 0 !important;
  max-height: none !important;
  padding: 14px 0 !important;
  overflow: visible !important;
}
.report-export-document img.report-chart-image,
.report-export-document .chart-wrapper img,
.report-export-document .metricas-chart-body img {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  height: auto !important;
  margin: 0 auto !important;
  border-radius: 8px !important;
  object-fit: contain !important;
}

/* MAPA DE CALOR A ANCHO TOTAL */
.report-export-heatmap .channel-body {
  display: block !important;
  width: 100% !important;
  min-width: 0 !important;
}
.report-export-heatmap .heatmap-wrap {
  display: block !important;
  width: 100% !important;
  max-width: none !important;
  min-width: 0 !important;
  overflow: visible !important;
  padding: 8px 0 !important;
}
.report-export-heatmap .heatmap-grid {
  display: grid !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  grid-template-columns: 46px repeat(var(--hm-cols, 31), minmax(0, 1fr)) 50px !important;
  grid-auto-flow: row !important;
  gap: 2px !important;
}
.report-export-heatmap .heatmap-cell {
  min-width: 0 !important;
  height: 22px !important;
  font-size: clamp(6px, 0.6vw, 9px) !important;
  border-radius: 2px !important;
}

/* REGLAS ESPECIFICAS PARA IMPRESION Y EXPORTACION A PDF EN HOJA A4 VERTICAL */
@page {
  size: A4 portrait;
  margin: 8mm 8mm 10mm 8mm;
}
@media print {
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    background: #0b0d12 !important;
    color: #f5f6f8 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    font-size: 11px !important;
    width: 100% !important;
    max-width: 100% !important;
  }
  .report-export-toolbar {
    display: none !important;
  }
  .report-export-document {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  .report-export-header {
    margin-bottom: 10px !important;
    padding: 12px 16px !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  .report-export-filters-bar {
    margin-bottom: 12px !important;
    padding: 8px 12px !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  .card, .channel-card, .kpi-grid {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
    margin-bottom: 12px !important;
  }
  .report-export-document img.report-chart-image,
  .report-export-document .chart-wrapper img,
  .report-export-document .metricas-chart-body img {
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    display: block !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  .report-export-heatmap .heatmap-cell {
    height: 17px !important;
    font-size: 6px !important;
  }
  .report-export-heatmap .heatmap-month,
  .report-export-heatmap .heatmap-dia,
  .report-export-heatmap .heatmap-hour,
  .report-export-heatmap .heatmap-day,
  .report-export-heatmap .heatmap-hour--total,
  .report-export-heatmap .heatmap-dia--total {
    font-size: 6px !important;
    padding: 0 1px !important;
  }
}
@media (max-width: 700px) {
  body { padding: 12px; }
  .report-export-header { flex-direction: column; align-items: flex-start; }
}
</style>
</head>
<body class="${EscaparHtml(ClasesCuerpo)}">
${Carcasa.outerHTML}
${AutoImprimir ? `<script>
window.addEventListener('load', () => {
    setTimeout(() => {
        window.focus();
        window.print();
    }, 450);
});
<\/script>` : ''}
</body>
</html>`;
}

// FUNCION PRINCIPAL DE EXPORTACION (PDF A4)
export async function exportVisibleReport(DestinoId, Boton, Formato = 'pdf') {
    const Destino = document.getElementById(DestinoId);
    if (!Destino || !Boton) return;

    const TextoOriginal = Boton.innerHTML;
    Boton.disabled = true;
    Boton.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> GENERANDO';

    try {
        const HtmlGenerado = await ConstruirHtmlAutosuficiente(DestinoId, Destino, Boton, false);

        // Disparar diálogo nativo de imprimir/guardar PDF directamente sin abrir pestañas nuevas
        let Iframe = document.getElementById('report-pdf-print-iframe');
        if (Iframe) Iframe.remove();

        Iframe = document.createElement('iframe');
        Iframe.id = 'report-pdf-print-iframe';
        Iframe.style.position = 'fixed';
        Iframe.style.left = '-10000px';
        Iframe.style.top = '-10000px';
        Iframe.style.width = '1024px';
        Iframe.style.height = '768px';
        Iframe.style.border = '0';
        Iframe.style.opacity = '0';
        Iframe.style.pointerEvents = 'none';

        document.body.appendChild(Iframe);

        const doc = Iframe.contentWindow.document;
        doc.open();
        doc.write(HtmlGenerado);
        doc.close();

        // Alinear el título del documento para que el navegador sugiera el nombre de archivo exacto
        const tituloSugerido = doc.title || 'INFORME AUTOPASS';
        const docTitleAnterior = document.title;
        document.title = tituloSugerido;

        setTimeout(() => {
            try {
                Iframe.contentWindow.focus();
                Iframe.contentWindow.print();
            } catch (errPrint) {
                console.error('Error al invocar diálogo de guardado PDF:', errPrint);
                showToast('NO SE PUDO ABRIR LA VENTANA DE IMPRESIÓN/GUARDADO.', 'error');
            } finally {
                setTimeout(() => {
                    document.title = docTitleAnterior;
                    if (Iframe && Iframe.parentNode) Iframe.remove();
                }, 4000);
            }
        }, 350);
    } catch (ErrorExportacion) {
        console.error('ERROR AL EXPORTAR INFORME:', ErrorExportacion);
        showToast('NO SE PUDO GENERAR EL PDF.', 'error');
    } finally {
        Boton.disabled = false;
        Boton.innerHTML = TextoOriginal;
    }
}

// ALIAS PARA COMPATIBILIDAD CON CODIGO EXISTENTE
export async function exportVisibleReportHtml(DestinoId, Boton) {
    return exportVisibleReport(DestinoId, Boton, 'pdf');
}

export async function exportVisibleReportPdf(DestinoId, Boton) {
    return exportVisibleReport(DestinoId, Boton, 'pdf');
}
