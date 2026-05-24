/* ----------------------------------------------------
   GLOBAL STATE
---------------------------------------------------- */

export let chart = null;

export function setChart(c) {
    chart = c;
}

/* ----------------------------------------------------
   NAVIGATION STATE (Wiederherstellung aus dem LocalStorage)
---------------------------------------------------- */

export let currentNode = localStorage.getItem("dash_node") || "HOME";

const savedBreadcrumb = localStorage.getItem("dash_breadcrumb");
export let breadcrumb = savedBreadcrumb ? JSON.parse(savedBreadcrumb) : ["Haus"];

const savedNodes = localStorage.getItem("dash_nodes");
export let breadcrumbNodes = savedNodes ? JSON.parse(savedNodes) : ["HOME"];

/* ----------------------------------------------------
   🔧 NEW: TIME & COMPARE STATE (Zeitreihen-Gedächtnis)
---------------------------------------------------- */

const savedRange = localStorage.getItem("dash_range");
export let currentRange = savedRange ? JSON.parse(savedRange) : null;

// Der Schalter steht standardmäßig auf true (aktiv), falls nichts gespeichert ist
export let compareActive = localStorage.getItem("dash_compare") !== "false";

/* ----------------------------------------------------
   SET CURRENT NODE
---------------------------------------------------- */

export function setCurrentNode(id) {
    currentNode = id;
    localStorage.setItem("dash_node", id); // Sichern!
}

/* ----------------------------------------------------
   ADD BREADCRUMB STEP
---------------------------------------------------- */

export function updateBreadcrumb(name, id) {
    breadcrumb.push(name);
    breadcrumbNodes.push(id);

    // Änderungen sofort im Speicher sichern
    localStorage.setItem("dash_breadcrumb", JSON.stringify(breadcrumb));
    localStorage.setItem("dash_nodes", JSON.stringify(breadcrumbNodes));
}

/* ----------------------------------------------------
   BACK / SLICE BREADCRUMB
---------------------------------------------------- */

export function sliceBreadcrumb(i) {
    breadcrumb = breadcrumb.slice(0, i + 1);
    breadcrumbNodes = breadcrumbNodes.slice(0, i + 1);
    currentNode = breadcrumbNodes[i];

    // Zustand nach dem Zurückgehen synchronisieren
    setCurrentNode(currentNode);
    localStorage.setItem("dash_breadcrumb", JSON.stringify(breadcrumb));
    localStorage.setItem("dash_nodes", JSON.stringify(breadcrumbNodes));
}

/* ----------------------------------------------------
   🔧 NEW: MUTATIONS FOR TIME & COMPARE
---------------------------------------------------- */

export function setCurrentRange(range, label) {
    currentRange = range;
    localStorage.setItem("dash_range", JSON.stringify(range));
    if (label) {
        localStorage.setItem("dash_btn_label", label);
    }
}

export function setCompareActive(active) {
    compareActive = active;
    localStorage.setItem("dash_compare", active);
}

/* ----------------------------------------------------
   🔥 CURRENT TITLE (FOR CHART / KPI / UI)
---------------------------------------------------- */

export function getCurrentTitle() {
    if (!breadcrumb || breadcrumb.length === 0) {
        return "Haus";
    }

    return breadcrumb[breadcrumb.length - 1];
}

/* ----------------------------------------------------
   OPTIONAL: FULL PATH STRING (nice for debug / UI)
---------------------------------------------------- */

export function getBreadcrumbPath() {
    return breadcrumb.join(" / ");
}
