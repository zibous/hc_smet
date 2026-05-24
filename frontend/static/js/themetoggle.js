export function initThemeToggle() {

  const theme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", theme);
  const btn = document.getElementById("themeToggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const current =
      document.documentElement.getAttribute("data-theme");
    const next =
      current === "dark"
        ? "light"
        : "dark";
    document.documentElement.setAttribute(
      "data-theme",
      next
    );
    localStorage.setItem("theme", next);
  });
}

init();