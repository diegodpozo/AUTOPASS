import { DatosCarrusel } from './landing-data.js';

let IndiceCarruselActual = 0;
let IntervaloCarrusel = null;
let IndiceFraseActual = 0;
let IntervaloFrase = null;

export function InicializarCarrusel() {
    const Contenedor = document.getElementById('contenedorCarrusel');
    if (!Contenedor || Contenedor.children.length > 0) return;

    DatosCarrusel.forEach((dato, i) => {
        const Item = document.createElement('div');
        Item.className = `item-carrusel ${i === 0 ? 'activo' : ''}`;
        Item.style.backgroundImage = `url('${dato.imagen}')`;
        //REMOVED INNERHTML CON LEGEND
        Contenedor.appendChild(Item);
    });

    // FLECHAS DE NAVEGACION
    const flechaIzq = document.getElementById('carrusel-prev');
    const flechaDer = document.getElementById('carrusel-next');
    if (flechaIzq) flechaIzq.addEventListener('click', () => RotarCarrusel(-1, true));
    if (flechaDer) flechaDer.addEventListener('click', () => RotarCarrusel(1, true));

    IniciarTemporizadores();
}

function RotarCarrusel(Direccion, reiniciarTimer) {
    const Items = document.querySelectorAll('.item-carrusel');
    if (Items.length === 0) return;

    Items[IndiceCarruselActual].classList.remove('activo');
    IndiceCarruselActual = (IndiceCarruselActual + Direccion + Items.length) % Items.length;
    Items[IndiceCarruselActual].classList.add('activo');
    
    // SINCRONIZAR FRASE CON CARRUSEL
    IndiceFraseActual = IndiceCarruselActual;
    const contenedor = document.getElementById('frase-animada');
    if (contenedor) {
        contenedor.innerText = DatosCarrusel[IndiceFraseActual].leyenda;
    }

    // REINICIAR TIMER SI SE NAVEGO MANUALMENTE
    if (reiniciarTimer) {
        if (IntervaloCarrusel) clearInterval(IntervaloCarrusel);
        IntervaloCarrusel = setInterval(() => RotarCarrusel(1), 5000);
    }
}

function IniciarTemporizadores() {
    if (IntervaloCarrusel) clearInterval(IntervaloCarrusel);
    
    IntervaloCarrusel = setInterval(() => RotarCarrusel(1), 5000);
    
    // INICIALIZAR PRIMERA FRASE
    const contenedor = document.getElementById('frase-animada');
    if (contenedor) contenedor.innerText = DatosCarrusel[0].leyenda;
}
