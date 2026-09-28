(function(){

  "use strict";

  const existingSidebar =
    document.querySelector(
      ".discipline-sidebar, .sidebar, .app-sidebar, .skyla-sidebar, .nav-sidebar"
    );

  /*
   * Discipline / Motivation / Obsession already have their
   * own dedicated navigation. Do not duplicate it.
   */
  if(existingSidebar){
    return;
  }

  const navItems = [
    ["🏠","Home","/"],
    ["🔥","Motivation","/motivation"],
    ["🧱","Discipline","/discipline"],
    ["⚡","Obsession","/obsession"],
    ["📅","Calendar","/calendar"],
    ["🕒","Routine","/routine"],
    ["🔥","Habits","/habits"],
    ["🎯","Goals","/goals"],
    ["⚽","Football","/football"],
    ["🏆","Sports Hub","/sports"],
    ["💪","Fitness","/fitness"],
    ["🔒","Finance","/finance"],
    ["🔔","Reminders","/reminders"],
    ["📊","Analytics","/analytics"],
    ["🎨","Customization","/customization"],
    ["⚙️","Settings","/settings"]
  ];

  const sidebar = document.createElement("aside");

  sidebar.className = "skyla-global-sidebar";

  sidebar.innerHTML = `
    <div class="skyla-brand">
      <div class="skyla-brand-icon">⚡</div>

      <div>
        <div class="skyla-brand-name">Skyla Life OS</div>
        <div class="skyla-brand-sub">
          Plan • Train • Grow • Win
        </div>
      </div>
    </div>

    <div class="skyla-nav-label">
      LIFE OS
    </div>

    <nav class="skyla-global-nav">
      ${navItems.map(item => `
        <a href="${item[2]}" data-skyla-path="${item[2]}">
          <span class="nav-icon">${item[0]}</span>
          <span>${item[1]}</span>
        </a>
      `).join("")}
    </nav>

    <div class="skyla-global-profile">
      <div class="skyla-avatar">A</div>

      <div>
        <span class="skyla-profile-name">Azad</span>
        <span class="skyla-profile-status">Keep Going!</span>
      </div>

      <span class="skyla-online"></span>
    </div>
  `;

  document.body.insertBefore(
    sidebar,
    document.body.firstChild
  );

  document.body.classList.add(
    "skyla-global-page",
    "skyla-has-global-sidebar"
  );

  const currentPath =
    window.location.pathname.replace(/\/+$/,"") || "/";

  sidebar
    .querySelectorAll("[data-skyla-path]")
    .forEach(link => {

      const target =
        link.dataset.skylaPath.replace(/\/+$/,"") || "/";

      if(target === currentPath){
        link.classList.add("active");
      }

    });

})();
