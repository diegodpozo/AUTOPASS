import * as ui from './modules/dashboard-ui.js';
import * as stats from './modules/dashboard-stats.js';
import * as admin from './modules/dashboard-admin.js';
import * as promos from './modules/dashboard-promotions.js';
import * as ops from './modules/dashboard-operations.js';
import * as reservations from './modules/dashboard-reservations.js';
import * as finance from './modules/dashboard-finance.js';
import * as metricas from './modules/dashboard-metrics.js';
import * as informes from './modules/dashboard-informes.js';
import * as tickets from './modules/dashboard-tickets.js';
import * as adminTour from './modules/admin-tour.js';
import * as baseUi from './modules/ui.js';
import * as utils from './modules/utils.js';
import { initVirtualTime } from './modules/virtual-time.js';
import './modules/notifications.js';
import { initOperatorAlerts } from './modules/operator-alerts.js';

/**
 * PUENTE / ORQUESTADOR: DASHBOARD.JS (v9.9.9)
 * MANTIENE LA INTERFAZ OPERATIVA CENTRALIZANDO LA LOGICA MODULAR.
 */

// 1. UI & NAVEGACION
window.switchTab = ui.switchTab;
window.switchMonitorTab = (tabId, element) => {
    element.parentElement.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');
    
    document.querySelectorAll('.monitor-tab-content').forEach(content => content.classList.remove('active'));
    
    const targetTable = document.getElementById(`monitor-tab-${tabId}`);
    const targetSearch = document.getElementById(`search-container-${tabId}`);
    
    if (targetTable) targetTable.classList.add('active');
    if (targetSearch) targetSearch.classList.add('active');
};
window.toggleMobileNav = baseUi.toggleMobileNav;

// 2. MODALES Y UTILIDADES GLOBALES
window.openModal = baseUi.openModal;
window.closeModal = baseUi.closeModal;
window.filterTable = utils.filterTable;
window.formatDate = utils.formatDate;
window.formatNum = utils.formatNum;
window.formatTime = utils.formatTime;
window.formatTimeSeconds = utils.formatTimeSeconds;
window.formatDateTime = utils.formatDateTime;
window.formatDayTime = utils.formatDayTime;
window.formatLocalDateTime = utils.formatLocalDateTime;

// 3. TOURS GUIADOS Y AYUDA OPERATIVA DE ADMINISTRACION
window.startAdminLiveTour = adminTour.startAdminLiveTour;
window.startAdminReservationsTour = adminTour.startAdminReservationsTour;
window.startAdminUsersTour = adminTour.startAdminUsersTour;
window.startAdminFinanceTour = adminTour.startAdminFinanceTour;
window.startAdminTicketsTour = adminTour.startAdminTicketsTour;
window.startAdminBranchesSettingsTour = adminTour.startAdminBranchesSettingsTour;
window.startAdminFullDashboardTour = adminTour.startAdminFullDashboardTour;
window.openAdminHelpModal = adminTour.openAdminHelpModal;
window.toggleAdminFaq = adminTour.toggleAdminFaq;
window.filterAdminHelpCategory = adminTour.filterAdminHelpCategory;
window.filterAdminHelpSearch = adminTour.filterAdminHelpSearch;

// 3.1 OPERACIONES Y PAGINADOR DE LOGS / OCUPACION
window.changePageLogs = stats.changePageLogs;
window.filterLogs = stats.filterLogs;
window.changePageOcc = stats.changePageOcc;
window.filterOccupancy = stats.filterOccupancy;

// 4. OPERACIONES MANUALES
window.manualEntry = ops.manualEntry;
window.payOccupancy = (plate, amount) => ops.payOccupancy(plate, amount, () => {
    if (document.getElementById('tab-finance')?.style.display !== 'none') {
        finance.loadFinanceData();
    }
});
window.cancelStay = stats.cancelStay;
window.manualExit = ops.manualExit;
window.showLogDetail = ops.showLogDetail;
window.openPendingExitPopup = ops.openPendingExitPopup;
window.confirmPendingExit = ops.confirmPendingExit;
window.closePendingExitPopup = ops.closePendingExitPopup;

// 4. RESERVAS ADMINISTRATIVAS
window.loadAdminReservations = reservations.loadAdminReservations;
window.onAdminResSearch = reservations.onAdminResSearch;
window.payReservationAdmin = reservations.payReservationAdmin;
window.cancelReservationAdmin = reservations.cancelReservationAdmin;
window.showReservationDetail = reservations.showReservationDetail;
window.openNewReservationModal = reservations.openNewReservationModal;
window.editReservationAdmin = reservations.openEditReservationModal;
window.updateNewFormGroups = reservations.updateNewFormGroups;
window.updateNewPeriodEnd = reservations.updateNewPeriodEnd;
window.updateNewReservationPrice = reservations.updateNewReservationPrice;
window.selectNewHourRange = reservations.selectNewHourRange;
window.updateNewVehicleTypeIcon = reservations.updateNewVehicleTypeIcon;
window.initNewResPatenteLookup = reservations.initNewResPatenteLookup;
window.resetNewResPatenteLookup = reservations.resetNewResPatenteLookup;
window.clearNewResPatenteLookup = reservations.clearNewResPatenteLookup;
window.handleAdminNewReservation = reservations.handleAdminNewReservation;
window.confirmEditResumoProceed = reservations.confirmEditResumoProceed;
window.cancelEditResumo = reservations.cancelEditResumo;
window.updateReservationBadge = reservations.updateReservationBadge;
window.clearReservationBadge = reservations.clearReservationBadge;

// 5. FINANZAS Y REPORTES
window.loadFinanceData = finance.loadFinanceData;
window.toggleFinanceDateFilter = finance.toggleFinanceDateFilter;
window.nextFinancePage = finance.nextFinancePage;
window.prevFinancePage = finance.prevFinancePage;
window.switchMethodTab = finance.switchMethodTab;

// 5.1 MÉTRICAS DEL SISTEMA
window.abrirMetrica = metricas.abrirMetrica;
window.volverMetricas = metricas.volverMetricas;
window.irAlInicio = metricas.irAlInicio;
window.irAlFinal = metricas.irAlFinal;
window.aplicarFiltroMetricas = metricas.aplicarFiltroMetricas;
window.limpiarFiltroMetricas = metricas.limpiarFiltroMetricas;

// 5.2 INFORMES DEL SISTEMA (mapa de calor, ocupación, recaudación, OCR)
window.cargarInforme = informes.cargarInforme;
window.aplicarInforme = informes.aplicarInforme;
window.limpiarInforme = informes.limpiarInforme;
window.alternarHeatmapVista = informes.alternarHeatmapVista;

// 6. ACCIONES ADMINISTRATIVAS Y USUARIOS
window.openBarrier = admin.openBarrier;
window.loadUsers = admin.loadUsers;
window.filterUserList = admin.filterUserList;
window.toggleUserStatsCollapsible = (btn) => {
    const content = document.getElementById('user-stats-collapsible-content');
    if (!content) return;
    content.classList.toggle('open');
    if (btn) btn.classList.toggle('open');
};
window.prevUserPage = admin.prevUserPage;
window.nextUserPage = admin.nextUserPage;
window.toggleBranchSelection = admin.toggleBranchSelection;
window.toggleUserBlock = admin.toggleUserBlock;
window.showCreateUserModal = admin.showCreateUserModal;
window.deleteUserAdmin = admin.deleteUserAdmin;
window.handleAdminCreateUser = admin.handleAdminCreateUser;
window.toggleInviteMode = admin.toggleInviteMode;
window.openPasswordModal = admin.openPasswordModal;
window.handleAdminChangePassword = admin.handleAdminChangePassword;
window.openEditUserModal = admin.openEditUserModal;
window.toggleEditBranchSelection = admin.toggleEditBranchSelection;
window.handleAdminEditUser = admin.handleAdminEditUser;

// 7. AJUSTES Y NAVEGACION SECCIONAL
window.switchSettingsTab = admin.switchSettingsTab;
window.switchRatesTab = admin.switchRatesTab;
window.refreshSystemDiagnostics = admin.refreshSystemDiagnostics;
window.loadSettings = admin.loadSettings;
window.saveAllRates = admin.saveAllRates;
window.toggleRateEdit = admin.toggleRateEdit;
window.saveRateGroup = admin.saveRateGroup;
window.saveCapacities = admin.saveCapacities;
window.saveSystemParam = admin.saveSystemParam;
window.resetSys = admin.resetSys;
window.exportFinanceData = admin.exportFinanceData;
window.toggleFinanceStatsCollapsible = finance.toggleFinanceStatsCollapsible;

// 8. SUCURSALES
window.loadBranches = admin.loadBranches;
window.handleCreateBranch = admin.handleCreateBranch;
window.createBranch = admin.handleCreateBranch;
window.showCreateBranchModal = admin.showCreateBranchModal;
window.deleteBranch = admin.deleteBranch;
window.toggleBranchHorario = admin.toggleBranchHorario;
window.editBranch = admin.editBranch;
window.showBranchFloors = admin.showBranchFloors;
window.toggleBranch = admin.toggleBranch;
window.previewBranchLogo = admin.previewBranchLogo;
window.clearBranchLogo = admin.clearBranchLogo;
window.searchAddress = admin.searchAddress;

// 9. PISOS DE SUCURSAL
window.openAddFloorModal = admin.openAddFloorModal;
window.openEditFloorModal = admin.openEditFloorModal;
window.handleCreateFloor = admin.handleCreateFloor;
window.deleteFloor = admin.deleteFloor;
window.updatePBCapacity = admin.updatePBCapacity;
window.savePBCapacity = admin.savePBCapacity;
window.toggleLevelEdit = admin.toggleLevelEdit;

// 10. PROMOCIONES
window.loadPromotionsAdmin = promos.loadPromotionsAdmin;
window.showCreatePromotionModal = promos.showCreatePromotionModal;
window.editPromotion = promos.editPromotion;
window.handleCreatePromotion = promos.handleCreatePromotion;
window.togglePromotion = promos.togglePromotion;
window.deletePromotion = promos.deletePromotion;
window.selectPromoIcon = promos.selectPromoIcon;
window.togglePromoTipoCanje = promos.togglePromoTipoCanje;
window.searchPromoAddress = promos.searchPromoAddress;

// 11. CAMARAS IP
window.loadCameraSettings = ui.loadCameraSettings;
window.showCreateCameraModal = ui.showCreateCameraModal;
window.showEditCameraModal = ui.showEditCameraModal;
window.handleSaveCameraConfig = ui.handleSaveCameraConfig;
window.deleteCamera = ui.deleteCamera;
window.toggleDynamicCameraService = ui.toggleDynamicCameraService;

// 12. TICKETS DE SOPORTE
window.loadAdminTickets = tickets.loadAdminTickets;
window.openTicketAnswerModal = tickets.openTicketAnswerModal;
window.submitTicketAnswer = tickets.submitTicketAnswer;
window.filterTicketList = tickets.filterTicketList;
window.openSupportTicketModal = (ticketId) => {
    ui.switchTab('tickets', document.querySelector('.nav-item[onclick*="tickets"]'));
    if (ticketId) setTimeout(() => tickets.openTicketAnswerModal(ticketId), 400);
};

// 13. DISPATCHER DE CARGA POR PESTAÑA
window.loadTabData = async (tabId) => {
    switch (tabId) {
        case 'live':
            stats.loadLiveStats();
            stats.loadRecentLogs();
            stats.loadOccupancy();
            break;
        case 'admin-reservations':
            reservations.loadAdminReservations();
            if (typeof reservations.clearReservationBadge === 'function') {
                reservations.clearReservationBadge();
            }
            break;
        case 'users':
            admin.loadUsers();
            break;
        case 'finance':
            finance.loadFinanceData();
            break;
        case 'metricas':
            metricas.loadMetricas();
            break;
        case 'promotions':
            promos.loadPromotionsAdmin();
            break;
        case 'branches':
            admin.loadBranches();
            break;
        case 'settings':
            admin.loadSettings();
            break;
        case 'tickets':
            tickets.loadAdminTickets();
            break;
    }
};

// 13. INICIALIZACIÓN DE LA APLICACIÓN
document.addEventListener('DOMContentLoaded', async () => {
    const rol = localStorage.getItem('rol');
    const sucursalRaw = localStorage.getItem('sucursal');
    
    let sucursalLimpia = '';
    if (sucursalRaw && sucursalRaw !== 'null' && sucursalRaw !== 'undefined') {
        sucursalLimpia = sucursalRaw.replace('AUTOPASS ', '').trim();
    }
    
    const roleNameEl = document.getElementById('role-name');
    const settingsTitleEl = document.getElementById('settings-title');

    if (roleNameEl) {
        let label = 'Personal Autorizado';
        if (rol === 'admin') label = 'Administrador Global';
        else if (rol === 'local_admin') label = `Administrador ${sucursalLimpia || 'Sucursal'}`;
        else if (rol === 'staff') label = `Empleado ${sucursalLimpia || 'Sucursal'}`;
        roleNameEl.innerText = label;
    }

    if (settingsTitleEl) {
        settingsTitleEl.innerText = 'CONFIGURACIÓN';
    }

    try {
        ui.initClock();
        initVirtualTime();
        initOperatorAlerts();
        ui.checkSystemHealth();
        stats.initOccupancyWS();
        metricas.initMetricas();
    } catch (e) { 
        console.warn("Error en servicios UI:", e); 
    }

    let lastTab = localStorage.getItem('activeAdminTab');

    if (rol === 'admin') {
        const allowedSuperAdmin = ['users', 'promotions', 'tickets', 'branches'];
        if (!lastTab || !allowedSuperAdmin.includes(lastTab)) {
            lastTab = 'users';
        }
    } else if (rol === 'staff') {
        const restrictedStaff = ['users', 'finance', 'promotions', 'tickets', 'settings', 'branches', 'metricas'];
        if (!lastTab || restrictedStaff.includes(lastTab)) {
            lastTab = 'live';
        }
    } else if (rol === 'local_admin') {
        if (!lastTab || lastTab === 'branches') {
            lastTab = 'live';
        }
    } else {
        if (!lastTab) lastTab = 'live';
    }

    const activeItem = document.querySelector(`.nav-item[onclick*="'${lastTab}'"]`);
    ui.switchTab(lastTab, activeItem);

    // BURBUJA 'SOPORTE & TICKETS': mostrar conteo real de tickets pendientes al cargar
    if (typeof tickets.updateTicketBadge === 'function') {
        tickets.updateTicketBadge();
    }

    // BURBUJA 'RESERVAS': verificar si hay reservas nuevas al cargar
    if (typeof reservations.updateReservationBadge === 'function') {
        reservations.updateReservationBadge();
    }

    document.getElementById('form-add-branch')?.addEventListener('submit', window.handleCreateBranch);
});
