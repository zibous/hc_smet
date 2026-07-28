(()=>{var C="api/dashboard2/analytics",v=document.getElementById("analytics-grid"),L=document.getElementById("analytics-refresh"),A=!1;async function w(){try{let e=await fetch(C);if(!e.ok)throw new Error(`HTTP ${e.status}`);let s=await e.json();I(s.sensors),L.textContent=`${s.count} Profile \u2022 ${O(s.timestamp)}`,A=!0}catch(e){v.innerHTML=`<p style="color:var(--text-muted)">Fehler: ${e.message}</p>`}}function I(e){if(!e||e.length===0){v.innerHTML='<p style="color:var(--text-muted)">Keine Analytics-Daten vorhanden. Wurde der Analytics-Daemon bereits ausgef\xFChrt?</p>';return}let s={};e.forEach(r=>{let n=r.area_id||"unknown";s[n]||(s[n]={name:r.area||"Unbekannt",sensors:[]}),s[n].sensors.push(r)});let o=["EG","WG","OG","DG","OS","NU"],i=Object.keys(s).sort((r,n)=>{let a=o.indexOf(r),t=o.indexOf(n);return a===-1&&t===-1?r.localeCompare(n):a===-1?1:t===-1?-1:a-t});v.innerHTML=i.map(r=>{let n=s[r],a=n.sensors.map(t=>{let l=F(t.cluster),d=(t.load_factor*100).toFixed(1);return`
        <div class="sensor-card">
          <div class="sensor-card-header">
            <div>
              <div class="sensor-card-id">${t.id}</div>
              <div class="sensor-card-name">${t.name}</div>
              <div class="sensor-card-room">${t.room}</div>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Samples</span>
              <span class="sensor-val-number">${t.samples}</span>
            </div>
          </div>
          <span class="cluster-badge ${l}">Energieverbrauch ${t.cluster}</span>
          <div class="sensor-card-values" style="margin-top:1.2rem;">
            <div class="sensor-val">
              <span class="sensor-val-label">Total kWh</span>
              <span class="sensor-val-number">${t.total.toFixed(1)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Grundlast</span>
              <span class="sensor-val-number">${t.base.toFixed(1)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Spitze</span>
              <span class="sensor-val-number">${t.peak.toFixed(1)}</span>
            </div>
          </div>
          <div class="sensor-card-values">
            <div class="sensor-val">
              <span class="sensor-val-label">\xD8 kWh/h</span>
              <span class="sensor-val-number">${t.average.toFixed(3)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Load Factor</span>
              <span class="sensor-val-number">${d}%</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">&nbsp;</span>
              <span class="sensor-val-number">&nbsp;</span>
            </div>
          </div>
        </div>
      `}).join("");return`
      <div class="area-group">
        <h3 class="area-group-title">${n.name} <span style="opacity:0.6;font-size:0.85em">(${n.sensors.length})</span></h3>
        <div class="sensor-grid">
          ${a}
        </div>
      </div>
    `}).join("")}function F(e){if(!e)return"cluster-standard";let s=e.toLowerCase();return s.includes("hoch")?"cluster-peak":s.includes("niedrig")?"cluster-base":"cluster-standard"}function O(e){return new Date(e*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}var j="api/dashboard2/hourly",k=document.getElementById("hourlyChart"),h=document.getElementById("hourly-table-wrap"),D=document.getElementById("hourly-refresh"),m=null,z=!1;async function f(){try{let e=await fetch(j);if(!e.ok)throw new Error(`HTTP ${e.status}`);let s=await e.json();H(s.data),B(s.data),D.textContent=`${s.hours_count} Stunden \u2022 ${G(s.timestamp)}`,z=!0}catch(e){h.innerHTML=`<p style="color:var(--text-muted)">Fehler: ${e.message}</p>`}}function H(e){if(!e||e.length===0)return;let s=[...e].reverse(),o=s.map(l=>new Date(l.hour*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})),i=s.map(l=>l.total),r=document.documentElement.getAttribute("data-theme")==="dark",n=r?"rgba(56, 189, 248, 0.7)":"rgba(37, 99, 235, 0.7)",a=r?"rgba(255,255,255,0.06)":"rgba(0,0,0,0.06)",t=r?"#94a3b8":"#475569";m&&m.destroy(),m=new Chart(k,{type:"bar",data:{labels:o,datasets:[{label:"Verbrauch (kWh)",data:i,backgroundColor:n,borderRadius:4,borderSkipped:!1}]},options:{responsive:!0,maintainAspectRatio:!1,plugins:{legend:{display:!1}},scales:{x:{grid:{color:a},ticks:{color:t,font:{size:11}}},y:{grid:{color:a},ticks:{color:t,font:{size:11}},beginAtZero:!0}}}}),k.parentElement.style.height="280px"}function B(e){if(!e||e.length===0){h.innerHTML='<p style="color:var(--text-muted)">Keine Stundenwerte vorhanden.</p>';return}let s=e,o={};s.forEach(a=>{Object.entries(a.sensors).forEach(([t,l])=>{o[t]=(o[t]||0)+l})});let i=Object.entries(o).sort((a,t)=>t[1]-a[1]).slice(0,10).map(([a])=>a),r=s.map(a=>{let l=new Date(a.hour*1e3).toLocaleString("de-DE",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}),d=i.map(p=>{let c=a.sensors[p];return`<td>${c!==void 0?c.toFixed(3):"-"}</td>`}).join("");return`<tr><td>${l}</td><td><strong>${a.total.toFixed(3)}</strong></td>${d}</tr>`}).join(""),n=i.map(a=>`<th>${a}</th>`).join("");h.innerHTML=`
    <table class="hourly-table">
      <thead>
        <tr><th>Zeit</th><th>Gesamt</th>${n}</tr>
      </thead>
      <tbody>${r}</tbody>
    </table>
  `}function G(e){return new Date(e*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}var _="api/dashboard2/live/sensors",b=document.getElementById("sensors-grid"),M=document.getElementById("sensors-refresh"),g={licht:"\u{1F4A1}",light:"\u{1F4A1}",steckdosen:"\u{1F50C}",netzteil:"\u{1F50B}",kuehlschrank:"\u{1F9CA}",fridge:"\u{1F9CA}",tiefkuehltruhe:"\u2744\uFE0F",geschirrspueler:"\u{1F37D}\uFE0F",spuelmaschine:"\u{1F37D}\uFE0F",kueche:"\u{1F373}",kuechenmoebel:"\u{1FA91}",herd:"\u{1F525}",ofen:"\u{1F525}",backofen:"\u{1F525}",heizung:"\u2668\uFE0F",heizungsgeraet:"\u2668\uFE0F",heizungspumpe:"\u2668\uFE0F",boiler:"\u{1F6BF}",pumpe:"\u{1F4A7}",abwasserpumpe:"\u{1F4A7}",dampfdusche:"\u{1F6BF}",waschmaschine:"\u{1F9FA}",trockner:"\u2668\uFE0F",server:"\u{1F5A5}\uFE0F",rechner:"\u{1F5A5}\uFE0F",tv:"\u{1F4FA}",soundanlage:"\u{1F50A}",telefonanlage:"\u260E\uFE0F",wlan:"\u{1F4F6}",piko_wechselrichter:"\u{1F506}",wohnzimmer:"\u{1F6CB}\uFE0F",schlafzimmer:"\u{1F6CF}\uFE0F",kinderzimmer_1:"\u{1F9F8}",kinderzimmer_2:"\u{1F9F8}",fitnessraum:"\u{1F3CB}\uFE0F",garage:"\u{1F697}",gang:"\u{1F6AA}",vorratsraum:"\u{1F4E6}",wc:"\u{1F6BD}",bad:"\u{1F6C1}",rolladen:"\u{1FA9F}",zaehlerschrank:"\u26A1",reserve:"\u2B55"},P={A:"#009640",B:"#4cb123",C:"#c3d100",D:"#ffcc00",E:"#ff9900",F:"#ff3300",G:"#d3001e"};function U(e){let s=(e.name||"").toLowerCase().replace(/ä/g,"ae").replace(/ö/g,"oe").replace(/ü/g,"ue").replace(/ß/g,"ss"),o=e.devices||[];for(let i of o){let r=i.toLowerCase();if(g[r])return g[r]}for(let[i,r]of Object.entries(g))if(s.includes(i))return r;return"\u26A1"}async function $(){try{let e=await fetch(_);if(!e.ok)throw new Error(`HTTP ${e.status}`);let s=await e.json();W(s.sensors,s.mode),M.textContent=`${s.count} Sensoren \u2022 ${s.mode||"POST"} \u2022 ${R(s.timestamp)}`}catch(e){b.innerHTML=`<p style="color:var(--text-muted)">Fehler beim Laden: ${e.message}</p>`}}function W(e,s){if(!e||e.length===0){b.innerHTML='<p style="color:var(--text-muted)">Keine Sensordaten vorhanden.</p>';return}let o={};e.forEach(n=>{let a=n.area_id||"unknown";o[a]||(o[a]={name:n.area||"Unbekannt",sensors:[]}),o[a].sensors.push(n)});let i=["EG","WG","OG","DG","OS","NU"],r=Object.keys(o).sort((n,a)=>{let t=i.indexOf(n),l=i.indexOf(a);return t===-1&&l===-1?n.localeCompare(a):t===-1?1:l===-1?-1:t-l});b.innerHTML=r.map(n=>{let a=o[n],t=a.sensors.map(l=>N(l,s)).join("");return`
      <div class="area-group">
        <h3 class="area-group-title">${a.name} <span style="opacity:0.6;font-size:0.85em">(${a.sensors.length})</span></h3>
        <div class="sensor-grid">
          ${t}
        </div>
      </div>
    `}).join("")}function N(e,s){let o=U(e),i=s==="GET",n=(e.online!==void 0?e.online:!0)?'<span class="badge-online">ONLINE</span>':'<span class="badge-off">OFFLINE</span>',a=e.energieklasse||"A",t=P[a]||"#777",l=(e.devices||[]).map(y=>y.charAt(0).toUpperCase()+y.slice(1)).join(", "),d=e.watt!==void 0?e.watt:0,p=d>0?"watt-active":"watt-idle";if(i)return`
      <div class="sensor-card">
        <div class="sensor-card-header">
          <div>
            <div class="sensor-card-id">${o} ${e.id} ${n}</div>
            <div class="sensor-card-name">${e.name}</div>
            <div class="sensor-card-room">${e.room}</div>
          </div>
          <div class="sensor-watt ${p}">${d} W</div>
        </div>

        <div class="sensor-card-details">
          <div class="detail-row">
            <span class="detail-label">Ger\xE4te</span>
            <span class="detail-value">${l||"\u2014"}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Energieklasse</span>
            <span class="energieklasse-badge" style="background-color:${t}">${a}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Verbrauch</span>
            <span class="detail-value">${(e.delta||0).toFixed(3)} kWh</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Kosten</span>
            <span class="detail-value">${(e.kosten||0).toFixed(3)} \u20AC</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">CO\u2082</span>
            <span class="detail-value">${(e.co2||0).toFixed(1)} g</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Prognose Tag</span>
            <span class="detail-value">${(e.prognose_tag||0).toFixed(2)} \u20AC</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Prognose Jahr</span>
            <span class="detail-value">${(e.prognose_jahr||0).toFixed(2)} \u20AC</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Model</span>
            <span class="detail-value">${e.model||"\u2014"}</span>
          </div>
        </div>
      </div>
    `;let c=Math.round(Date.now()/1e3-e.timestamp),S=c<60?`${c}s`:`${Math.round(c/60)}m`;return`
    <div class="sensor-card">
      <div class="sensor-card-header">
        <div>
          <div class="sensor-card-id">${e.id}</div>
          <div class="sensor-card-name">${e.name}</div>
          <div class="sensor-card-room">${e.room}</div>
        </div>
        <div class="sensor-card-id" title="Alter">${S}</div>
      </div>
      <div class="sensor-card-values">
        <div class="sensor-val">
          <span class="sensor-val-label">Aktuell</span>
          <span class="sensor-val-number">${e.current.toFixed(2)}</span>
        </div>
        <div class="sensor-val">
          <span class="sensor-val-label">Letzter</span>
          <span class="sensor-val-number">${e.last.toFixed(2)}</span>
        </div>
        <div class="sensor-val">
          <span class="sensor-val-label">Delta</span>
          <span class="sensor-val-number ${e.delta>0?"delta-positive":"delta-zero"}">${e.delta.toFixed(4)}</span>
        </div>
      </div>
    </div>
  `}function R(e){return new Date(e*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}function x(){let e=document.getElementById("header-update");if(!e)return;let s=new Date,o=s.toLocaleDateString("sv-SE"),i=s.toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"});e.textContent=`${o} um ${i} Uhr`}var E=document.querySelectorAll(".tab-btn"),K=document.querySelectorAll(".tab-content"),u=localStorage.getItem("liveTab")||"sensors";E.forEach(e=>{e.addEventListener("click",()=>{let s=e.dataset.tab;T(s)})});function T(e){u=e,localStorage.setItem("liveTab",e),E.forEach(s=>s.classList.toggle("active",s.dataset.tab===e)),K.forEach(s=>s.classList.toggle("active",s.id===`tab-${e}`)),e==="sensors"&&$(),e==="hourly"&&f(),e==="analytics"&&w()}async function q(){T(u)}setInterval(()=>{u==="sensors"&&$(),u==="hourly"&&f(),x()},3e4);q();x();})();
//# sourceMappingURL=main.bundle.js.map
