(function(){

  "use strict";

  /*
   * Discipline already has its own complete sidebar.
   * All other Life OS pages use this common sidebar.
   */

  const path =
    window.location.pathname.replace(/\/+$/, "") || "/";

  if(path === "/discipline"){
    return;
  }

  if(document.querySelector(".skyla-global-sidebar")){
    return;
  }

  /* Hide old page-specific sidebars.
     We keep their HTML/functionality untouched. */
  document.querySelectorAll(".sidebar").forEach(el=>{
    el.classList.add("skyla-old-sidebar-hidden");
  });

  const items = [
    ["🏠","Home","/"],
    ["🔥","Motivation","/motivation"],
    ["🧱","Discipline","/discipline"],
    ["⚡","Obsession","/obsession"],
    ["📅","Calendar","/calendar"],
    ["🕒","Daily Routine","/routine"],
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

  const sidebar=document.createElement("aside");

  sidebar.className="skyla-global-sidebar";

  sidebar.innerHTML=`

    <div class="skyla-brand">

      <div class="skyla-brand-mark">⚡</div>

      <div class="skyla-brand-text">
        <div class="skyla-brand-name">
          Skyla Life OS
        </div>

        <div class="skyla-brand-sub">
          Plan • Train • Grow • Win
        </div>
      </div>

    </div>

    <div class="skyla-nav-label">
      LIFE OS
    </div>

    <nav class="skyla-global-nav">

      ${items.map(item=>`

        <a
          href="${item[2]}"
          class="skyla-nav-item"
          data-skyla-page="${item[2]}"
        >

          <span class="skyla-nav-icon">
            ${item[0]}
          </span>

          <span class="skyla-nav-text">
            ${item[1]}
          </span>

        </a>

      `).join("")}

    </nav>

    <div class="skyla-global-profile">

      <div class="skyla-avatar">
        A
      </div>

      <div class="skyla-profile-info">

        <strong>
          Azad
        </strong>

        <span>
          Keep Going!
        </span>

      </div>

      <span class="skyla-online"></span>

    </div>
  `;

  document.body.insertBefore(
    sidebar,
    document.body.firstChild
  );

  document.body.classList.add(
    "skyla-global-page"
  );

  /*
   * Highlight current page.
   */

  sidebar
    .querySelectorAll("[data-skyla-page]")
    .forEach(link=>{

      const target =
        link.dataset.skylaPage.replace(/\/+$/,"") || "/";

      if(target === path){
        link.classList.add("active");
      }

    });

})();
