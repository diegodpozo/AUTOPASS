/**
 * MÓDULO SUCURSALES Y PISOS - FACHADA (FACADE PATTERN)
 * Re-exporta la gestión de sucursales CRUD/Mapa y la gestión de pisos/niveles.
 */

export {
    getAllBranchesData,
    setAllBranchesData,
    initBranchMap,
    searchAddress,
    populateBranchSelect,
    showCreateBranchModal,
    loadBranches,
    editBranch,
    toggleBranch,
    toggleBranchHorario,
    previewBranchLogo,
    clearBranchLogo,
    handleCreateBranch,
    deleteBranch
} from './dashboard-admin-branches-crud.js';

export {
    showBranchFloors,
    loadFloors,
    toggleLevelEdit,
    savePBCapacity,
    updateFloorCapacity,
    openAddFloorModal,
    openEditFloorModal,
    handleCreateFloor,
    deleteFloor
} from './dashboard-admin-branches-floors.js';
