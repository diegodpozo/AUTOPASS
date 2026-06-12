import * as v from './modules/vehicles.js';

/**
 * BRIDGE: vehicles.js
 */

window.loadVehicles = v.loadVehicles;
window.addVehicle = v.addVehicle;
window.deleteVehicle = v.deleteVehicle;
window.toggleVehicleForm = v.toggleVehicleForm;
window.updateVehicleTypeIcon = v.updateVehicleTypeIcon;

window.toggleNuevoVinculo = function() {
    const container = document.getElementById('vinculo-container');
    const trigger = document.querySelector('.register-trigger-card');
    const arrow = document.getElementById('vinculo-arrow');
    
    if (!container) return;

    const isOpen = container.classList.toggle('open');
    if (trigger) trigger.classList.toggle('open');
    if (arrow) {
        const isMobile = window.innerWidth <= 900;
        if (isMobile) {
            arrow.style.transform = isOpen ? 'rotate(270deg)' : 'rotate(90deg)';
        } else {
            arrow.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }
};
