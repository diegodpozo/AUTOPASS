/**
 * AUTOPASS - ESTADO COMPARTIDO DEL MAPA DE LA LANDING
 * Submodulo de landing-map.js: estado mutable compartido entre
 * initMap (fachada), findNearestBranch (geo), filterMapByLocality (locality).
 */

export const lmState = {
    mapInstance: null,
    mapInstances: {},
    mapLocalityItems: {},
    allBranchesMap: null,
};