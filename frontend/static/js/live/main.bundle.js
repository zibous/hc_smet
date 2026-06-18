(()=>{var C="api/dashboard2/live/sensors",m=document.getElementById("sensors-grid"),A=document.getElementById("sensors-refresh"),v={licht:"\u{1F4A1}",light:"\u{1F4A1}",steckdosen:"\u{1F50C}",netzteil:"\u{1F50B}",kuehlschrank:"\u{1F9CA}",fridge:"\u{1F9CA}",tiefkuehltruhe:"\u2744\uFE0F",geschirrspueler:"\u{1F37D}\uFE0F",spuelmaschine:"\u{1F37D}\uFE0F",kueche:"\u{1F373}",kuechenmoebel:"\u{1FA91}",herd:"\u{1F525}",ofen:"\u{1F525}",backofen:"\u{1F525}",heizung:"\u2668\uFE0F",heizungsgeraet:"\u2668\uFE0F",heizungspumpe:"\u2668\uFE0F",boiler:"\u{1F6BF}",pumpe:"\u{1F4A7}",abwasserpumpe:"\u{1F4A7}",dampfdusche:"\u{1F6BF}",waschmaschine:"\u{1F9FA}",trockner:"\u2668\uFE0F",server:"\u{1F5A5}\uFE0F",rechner:"\u{1F5A5}\uFE0F",tv:"\u{1F4FA}",soundanlage:"\u{1F50A}",telefonanlage:"\u260E\uFE0F",wlan:"\u{1F4F6}",piko_wechselrichter:"\u{1F506}",wohnzimmer:"\u{1F6CB}\uFE0F",schlafzimmer:"\u{1F6CF}\uFE0F",kinderzimmer_1:"\u{1F9F8}",kinderzimmer_2:"\u{1F9F8}",fitnessraum:"\u{1F3CB}\uFE0F",garage:"\u{1F697}",gang:"\u{1F6AA}",vorratsraum:"\u{1F4E6}",wc:"\u{1F6BD}",bad:"\u{1F6C1}",rolladen:"\u{1FA9F}",zaehlerschrank:"\u26A1",reserve:"\u2B55"},L={A:"#009640",B:"#4cb123",C:"#c3d100",D:"#ffcc00",E:"#ff9900",F:"#ff3300",G:"#d3001e"};function S(e){let s=(e.name||"").toLowerCase().replace(/ä/g,"ae").replace(/ö/g,"oe").replace(/ü/g,"ue").replace(/ß/g,"ss"),o=e.devices||[];for(let l of o){let r=l.toLowerCase();if(v[r])return v[r]}for(let[l,r]of Object.entries(v))if(s.includes(l))return r;return"\u26A1"}async function h(){try{let e=await fetch(C);if(!e.ok)throw new Error(`HTTP ${e.status}`);let s=await e.json();F(s.sensors,s.mode),A.textContent=`${s.count} Sensoren \u2022 ${s.mode||"POST"} \u2022 ${O(s.timestamp)}`}catch(e){m.innerHTML=`<p style="color:var(--text-muted)">Fehler beim Laden: ${e.message}</p>`}}function F(e,s){if(!e||e.length===0){m.innerHTML='<p style="color:var(--text-muted)">Keine Sensordaten vorhanden.</p>';return}let o={};e.forEach(t=>{let a=t.area_id||"unknown";o[a]||(o[a]={name:t.area||"Unbekannt",sensors:[]}),o[a].sensors.push(t)});let l=["EG","WG","OG","DG","OS","NU"],r=Object.keys(o).sort((t,a)=>{let n=l.indexOf(t),i=l.indexOf(a);return n===-1&&i===-1?t.localeCompare(a):n===-1?1:i===-1?-1:n-i});m.innerHTML=r.map(t=>{let a=o[t],n=a.sensors.map(i=>I(i,s)).join("");return`
      <div class="area-group">
        <h3 class="area-group-title">${a.name} <span style="opacity:0.6;font-size:0.85em">(${a.sensors.length})</span></h3>
        <div class="sensor-grid">
          ${n}
        </div>
      </div>
    `}).join("")}function I(e,s){let o=S(e),l=s==="GET",t=(e.online!==void 0?e.online:!0)?'<span class="badge-online">ONLINE</span>':'<span class="badge-off">OFFLINE</span>',a=e.energieklasse||"A",n=L[a]||"#777",i=(e.devices||[]).map(y=>y.charAt(0).toUpperCase()+y.slice(1)).join(", "),d=e.watt!==void 0?e.watt:0,p=d>0?"watt-active":"watt-idle";if(l)return`
      <div class="sensor-card">
        <div class="sensor-card-header">
          <div>
            <div class="sensor-card-id">${o} ${e.id} ${t}</div>
            <div class="sensor-card-name">${e.name}</div>
            <div class="sensor-card-room">${e.room}</div>
          </div>
          <div class="sensor-watt ${p}">${d} W</div>
        </div>

        <div class="sensor-card-details">
          <div class="detail-row">
            <span class="detail-label">Ger\xE4te</span>
            <span class="detail-value">${i||"\u2014"}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Energieklasse</span>
            <span class="energieklasse-badge" style="background-color:${n}">${a}</span>
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
    `;let c=Math.round(Date.now()/1e3-e.timestamp),T=c<60?`${c}s`:`${Math.round(c/60)}m`;return`
    <div class="sensor-card">
      <div class="sensor-card-header">
        <div>
          <div class="sensor-card-id">${e.id}</div>
          <div class="sensor-card-name">${e.name}</div>
          <div class="sensor-card-room">${e.room}</div>
        </div>
        <div class="sensor-card-id" title="Alter">${T}</div>
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
  `}function O(e){return new Date(e*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}var j="api/dashboard2/hourly",w=document.getElementById("hourlyChart"),g=document.getElementById("hourly-table-wrap"),z=document.getElementById("hourly-refresh"),f=null,H=!1;async function b(){try{let e=await fetch(j);if(!e.ok)throw new Error(`HTTP ${e.status}`);let s=await e.json();D(s.data),G(s.data),z.textContent=`${s.hours_count} Stunden \u2022 ${_(s.timestamp)}`,H=!0}catch(e){g.innerHTML=`<p style="color:var(--text-muted)">Fehler: ${e.message}</p>`}}function D(e){if(!e||e.length===0)return;let s=[...e].reverse(),o=s.map(i=>new Date(i.hour*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})),l=s.map(i=>i.total),r=document.documentElement.getAttribute("data-theme")==="dark",t=r?"rgba(56, 189, 248, 0.7)":"rgba(37, 99, 235, 0.7)",a=r?"rgba(255,255,255,0.06)":"rgba(0,0,0,0.06)",n=r?"#94a3b8":"#475569";f&&f.destroy(),f=new Chart(w,{type:"bar",data:{labels:o,datasets:[{label:"Verbrauch (kWh)",data:l,backgroundColor:t,borderRadius:4,borderSkipped:!1}]},options:{responsive:!0,maintainAspectRatio:!1,plugins:{legend:{display:!1}},scales:{x:{grid:{color:a},ticks:{color:n,font:{size:11}}},y:{grid:{color:a},ticks:{color:n,font:{size:11}},beginAtZero:!0}}}}),w.parentElement.style.height="280px"}function G(e){if(!e||e.length===0){g.innerHTML='<p style="color:var(--text-muted)">Keine Stundenwerte vorhanden.</p>';return}let s=e,o={};s.forEach(a=>{Object.entries(a.sensors).forEach(([n,i])=>{o[n]=(o[n]||0)+i})});let l=Object.entries(o).sort((a,n)=>n[1]-a[1]).slice(0,10).map(([a])=>a),r=s.map(a=>{let i=new Date(a.hour*1e3).toLocaleString("de-DE",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}),d=l.map(p=>{let c=a.sensors[p];return`<td>${c!==void 0?c.toFixed(3):"-"}</td>`}).join("");return`<tr><td>${i}</td><td><strong>${a.total.toFixed(3)}</strong></td>${d}</tr>`}).join(""),t=l.map(a=>`<th>${a}</th>`).join("");g.innerHTML=`
    <table class="hourly-table">
      <thead>
        <tr><th>Zeit</th><th>Gesamt</th>${t}</tr>
      </thead>
      <tbody>${r}</tbody>
    </table>
  `}function _(e){return new Date(e*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}var B="api/dashboard2/analytics",$=document.getElementById("analytics-grid"),M=document.getElementById("analytics-refresh"),P=!1;async function k(){try{let e=await fetch(B);if(!e.ok)throw new Error(`HTTP ${e.status}`);let s=await e.json();W(s.sensors),M.textContent=`${s.count} Profile \u2022 ${N(s.timestamp)}`,P=!0}catch(e){$.innerHTML=`<p style="color:var(--text-muted)">Fehler: ${e.message}</p>`}}function W(e){if(!e||e.length===0){$.innerHTML='<p style="color:var(--text-muted)">Keine Analytics-Daten vorhanden. Wurde der Analytics-Daemon bereits ausgef\xFChrt?</p>';return}let s={};e.forEach(r=>{let t=r.area_id||"unknown";s[t]||(s[t]={name:r.area||"Unbekannt",sensors:[]}),s[t].sensors.push(r)});let o=["EG","WG","OG","DG","OS","NU"],l=Object.keys(s).sort((r,t)=>{let a=o.indexOf(r),n=o.indexOf(t);return a===-1&&n===-1?r.localeCompare(t):a===-1?1:n===-1?-1:a-n});$.innerHTML=l.map(r=>{let t=s[r],a=t.sensors.map(n=>{let i=U(n.cluster),d=(n.load_factor*100).toFixed(1);return`
        <div class="sensor-card">
          <div class="sensor-card-header">
            <div>
              <div class="sensor-card-id">${n.id}</div>
              <div class="sensor-card-name">${n.name}</div>
              <div class="sensor-card-room">${n.room}</div>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Samples</span>
              <span class="sensor-val-number">${n.samples}</span>
            </div>
          </div>
          <span class="cluster-badge ${i}">Energieverbrauch ${n.cluster}</span>
          <div class="sensor-card-values" style="margin-top:1.2rem;">
            <div class="sensor-val">
              <span class="sensor-val-label">Total kWh</span>
              <span class="sensor-val-number">${n.total.toFixed(1)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Grundlast</span>
              <span class="sensor-val-number">${n.base.toFixed(1)}</span>
            </div>
            <div class="sensor-val">
              <span class="sensor-val-label">Spitze</span>
              <span class="sensor-val-number">${n.peak.toFixed(1)}</span>
            </div>
          </div>
          <div class="sensor-card-values">
            <div class="sensor-val">
              <span class="sensor-val-label">\xD8 kWh/h</span>
              <span class="sensor-val-number">${n.average.toFixed(3)}</span>
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
        <h3 class="area-group-title">${t.name} <span style="opacity:0.6;font-size:0.85em">(${t.sensors.length})</span></h3>
        <div class="sensor-grid">
          ${a}
        </div>
      </div>
    `}).join("")}function U(e){if(!e)return"cluster-standard";let s=e.toLowerCase();return s.includes("hoch")?"cluster-peak":s.includes("niedrig")?"cluster-base":"cluster-standard"}function N(e){return new Date(e*1e3).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}var x=document.querySelectorAll(".tab-btn"),R=document.querySelectorAll(".tab-content"),u=localStorage.getItem("liveTab")||"sensors";x.forEach(e=>{e.addEventListener("click",()=>{let s=e.dataset.tab;E(s)})});function E(e){u=e,localStorage.setItem("liveTab",e),x.forEach(s=>s.classList.toggle("active",s.dataset.tab===e)),R.forEach(s=>s.classList.toggle("active",s.id===`tab-${e}`)),e==="sensors"&&h(),e==="hourly"&&b(),e==="analytics"&&k()}async function K(){E(u)}setInterval(()=>{u==="sensors"&&h(),u==="hourly"&&b()},3e4);K();})();
//# sourceMappingURL=main.bundle.js.map
