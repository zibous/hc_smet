(()=>{var L=null;function Y(e){L=e}var $=localStorage.getItem("dash_node")||"HOME",W=localStorage.getItem("dash_breadcrumb"),w=W?JSON.parse(W):["Haus"],V=localStorage.getItem("dash_nodes"),B=V?JSON.parse(V):["HOME"],G=localStorage.getItem("dash_range"),ie=G?JSON.parse(G):null,se=localStorage.getItem("dash_compare")!=="false";function H(e){$=e,localStorage.setItem("dash_node",e)}function q(e,i){w.push(e),B.push(i),localStorage.setItem("dash_breadcrumb",JSON.stringify(w)),localStorage.setItem("dash_nodes",JSON.stringify(B))}function K(e){w=w.slice(0,e+1),B=B.slice(0,e+1),$=B[e],H($),localStorage.setItem("dash_breadcrumb",JSON.stringify(w)),localStorage.setItem("dash_nodes",JSON.stringify(B))}function O(e,i){ie=e,localStorage.setItem("dash_range",JSON.stringify(e)),i&&localStorage.setItem("dash_btn_label",i)}function R(e){se=e,localStorage.setItem("dash_compare",e)}function Z(){return!w||w.length===0?"Haus":w[w.length-1]}var U=!1;function de(){if(U)return;let e=document.createElement("style");e.innerHTML=`
        .breadcrumb {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.8rem;
        }

        .crumb {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.9rem 1.4rem;
            border-radius: 9px;
            cursor: pointer;
            user-select: none;
            font-size: 1.6rem;
            font-weight: 500;

            color: var(--text-main, rgba(255,255,255,0.92));
            background: var(--card-bg, rgba(255,255,255,0.08));
            border: 1px solid var(--border, rgba(255,255,255,0.10));
            box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,0.1));
            transition: .25s ease;
        }

        .crumb:hover {
            transform: translateY(-2px);
            background: var(--border, rgba(255,255,255,0.14));
        }

        .crumb.active {
            background: linear-gradient(135deg, #3b82f6, #60a5fa);
            border-color: #3b82f6;
            color: white;
        }

        // Korrektur f\xFCr aktiven Text im Light Mode, falls var(--text-main) dunkel ist
        [data-theme="light"] .crumb.active {
            color: #ffffff;
        }

        .crumb-icon {
            font-size: 1.4rem;
        }

        .crumb-divider {
            opacity: 0.5;
            font-size: 1.2rem;
            color: var(--text-muted, rgba(255,255,255,0.35));
        }

        @media (max-width: 768px) {
            .breadcrumb {
                gap: 0.5rem;
            }

            .crumb {
                padding: 0.8rem 1.1rem;
                font-size: 1.25rem;
            }
        }
    `,document.head.appendChild(e),U=!0}function X(e,i){H(e),q(i,e),M(),z()}function le(e){K(e),M(),z()}function M(){de();let e=document.getElementById("breadcrumb");e&&(e.className="breadcrumb",e.innerHTML="",w.forEach((i,n)=>{let a=document.createElement("div");a.className=n===w.length-1?"crumb active":"crumb";let d=n===0?'<span class="crumb-icon">\u{1F3E0}</span>':"";if(a.innerHTML=`
            ${d}
            <span>
                ${i}
            </span>
        `,a.addEventListener("click",()=>{le(n)}),e.appendChild(a),n<w.length-1){let o=document.createElement("div");o.className="crumb-divider",o.innerHTML="\u2192",e.appendChild(o)}}))}var Q=!1;function ce(){if(Q)return;let e=document.createElement("style");e.innerHTML=`
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(22rem, 1fr));
            gap: 1.4rem;
        }

        .card {
            position: relative;
            overflow: hidden;
            padding: 1.4rem;
            border-radius: 1.8rem;
            cursor: pointer;

            color: var(--text-main, #ffffff);
            background: var(--card-bg, rgba(255,255,255,0.10));
            border: 1px solid var(--border, rgba(255,255,255,0.10));
            box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,0.1));

            transition:
                transform .25s ease,
                box-shadow .25s ease,
                background .25s ease;
        }

        .card:hover {
            transform: translateY(-4px);
            border-left-color: var(--primary, #3182ce);
            border-right-color: var(--primary, #3182ce);
            border-bottom-color: var(--primary, #3182ce);
            box-shadow: 0 12px 28px rgba(0,0,0,0.18);
        }

        // Deaktiviert Effekte auf der Sensor-Endebene
        .card.no-click {
            cursor: default;
        }
        .card.no-click:hover {
            transform: none;
            border-color: var(--border, rgba(255,255,255,0.10));
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.8rem;
        }

        /* Richtet Titel-Text und Punkt b\xFCndig nebeneinander aus */
        .card-title {
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            color: var(--text-main, #ffffff);

            /* \u2728 FIX: Erzwingt den Zeiger-Mauszeiger und verhindert Textmarkierung */
            cursor: inherit;
            user-select: none;
            -webkit-user-select: none;
        }

        /* Erzeugt den Punkt virtuell VOR dem Text, ohne JavaScript zu st\xF6ren */
        .card-title::before {
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.6rem;
            display: inline-block;
            transition: background-color 0.3s, box-shadow 0.3s;
        }

        /* Zustand: Aktiv -> Gr\xFCn leuchtend */
        .card[data-active="true"] .card-title::before {
            background-color: #10b981;
            box-shadow: 0 0 8px #10b981;
            position: relative;
        }

        /* Zustand: Inaktiv -> Mattes Grau */
        .card[data-active="false"] .card-title::before {
            background-color: #94a3b8;
            box-shadow: none;
            opacity: 0.5;
        }

        .card-value {
            font-size: 2.1rem;
            font-weight: 800;
            line-height: 1;
            margin-top: 0.35rem;
            color: var(--text-main, #ffffff);
        }

        .card-unit {
            color: var(--text-muted, rgba(255, 255, 255, 0.7));
            font-size: 1rem;
            margin-left: 0.2rem;
        }

        .card-delta {
            font-size: 1.1rem;
            font-weight: 700;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(128,128,128,0.08);
        }

        .sparkline-wrapper {
            position: relative;
            height: 60px;
            margin: 1rem -0.3rem 1rem -0.3rem;
        }

        .sparkline {
            width: 100%;
            height: 100%;
            display: block;
        }

        .card-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.7rem;
        }

        .stat {
            padding: 0.7rem;
            border-radius: 1rem;
            background: rgba(128,128,128,0.05);
            border: 1px solid var(--border, rgba(255,255,255,0.06));
            text-align: center;
        }

        .stat-label {
            font-size: 1rem;
            color: var(--text-muted, rgba(255,255,255,0.65));
            margin-bottom: 0.25rem;
        }

        .stat-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-main, #ffffff);
        }
    `,document.head.appendChild(e),Q=!0}function me(e,i,n){if(!i||i.length<2)return;let a=e.getContext("2d"),d=e.offsetWidth,o=e.offsetHeight,s=window.devicePixelRatio||1;e.width=d*s,e.height=o*s,a.scale(s,s),a.clearRect(0,0,d,o);let l=Math.floor(d/3),r=i;if(i.length>l){r=[];let m=i.length/l;for(let u=0;u<l;u++){let v=Math.floor(u*m),f=Math.floor((u+1)*m),p=0,t=0;for(let c=v;c<f;c++)p+=i[c],t++;r.push(p/t)}}let k=Math.min(...r),h=Math.max(...r)-k||1,g=r.map(m=>(m-k)/h),T=d/(g.length-1),x=document.documentElement.getAttribute("data-theme")==="dark",I=n||(x?"hsla(28, 100%, 58%, 1)":"#2b6cb0"),y=n||(x?"hsla(28, 100%, 60%, 1)":"#4299e1"),E=n?n.replace(/,\s*[\d.]+\)$/,", 0.28)"):x?"rgba(255, 119, 0, 0.28)":"rgba(66, 153, 225, 0.25)",b=a.createLinearGradient(0,0,0,o);b.addColorStop(0,E),b.addColorStop(1,"rgba(0, 0, 0, 0)"),a.beginPath(),g.forEach((m,u)=>{let v=u*T,f=o-m*(o-10)-5;u===0?a.moveTo(v,f):a.lineTo(v,f)}),a.lineTo(d,o),a.lineTo(0,o),a.closePath(),a.fillStyle=b,a.fill(),a.beginPath(),g.forEach((m,u)=>{let v=u*T,f=o-m*(o-10)-5;u===0?a.moveTo(v,f):a.lineTo(v,f)}),a.lineWidth=1.6,a.strokeStyle=I,a.shadowColor=y,a.shadowBlur=x?10:2,a.lineJoin="round",a.lineCap="round",a.stroke(),a.shadowBlur=0}function ee(e){ce();let i=document.getElementById("cards");if(!i)return;i.innerHTML="";let n=e.stats||{},a=e.series||{},d=e.items||[],o=document.documentElement.getAttribute("data-theme")==="dark",s=Object.keys(a),l=Math.max(1,s.length);d.forEach((r,k)=>{let S=r.level==4,h=n[r.id]||{current:0,delta:0,min:0,max:0,avg:0},g=Array.isArray(a[r.id])?a[r.id]:[],T=s.indexOf(r.id),I=(T>=0?T:k)*(360/l)%360,y=o?`hsla(${I}, 100%, 65%, 1)`:`hsla(${I}, 90%, 55%, 1)`,E=o?`hsla(${I}, 80%, 55%, 0.25)`:`hsla(${I}, 70%, 50%, 0.15)`,b=document.createElement("div");S?b.className="card no-click":b.className="card",o&&(b.style.background="rgba(30, 41, 59, 0.22)"),b.style.borderTop=`3px solid ${y}`,b.setAttribute("data-active",h.current>0?"true":"false");let m=h.delta>=0;b.innerHTML=`
            <div class="card-header">
                <div>
                    <div class="card-title">${r.name}</div>
                    <div class="card-value">
                        ${(r.value??0).toFixed(1)}
                        <span class="card-unit">kWh</span>
                    </div>
                </div>
                <div class="card-delta" style="color: ${m?"#00FFC2":"#FF7A7A"};">
                    ${m?"+":""}${(r.delta??0).toFixed(1)}%
                </div>
            </div>

            <div class="sparkline-wrapper">
                <canvas class="sparkline"></canvas>
            </div>

            <div class="card-stats">
                <div class="stat">
                    <div class="stat-label">Min</div>
                    <div class="stat-value">${(h.min??0).toFixed(1)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Max</div>
                    <div class="stat-value">${(h.max??0).toFixed(1)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Schnitt</div>
                    <div class="stat-value">${(h.avg??0).toFixed(1)}</div>
                </div>
            </div>
        `,S||b.addEventListener("click",()=>{X(r.id,r.name)}),i.appendChild(b);let u=b.querySelector(".sparkline");u&&g.length>0&&me(u,g,y)})}var C="area";function pe(e,i){let n=i==="dark",a=n?"#ffffff":"#1e293b",d=n?"#f1f5f9":"#475569",o=n?"rgba(255, 255, 255, 0.05)":"rgba(0,0,0,0.04)",s=n?"rgba(15, 23, 42, 0.98)":"rgba(255,255,255,0.96)",l=n?"rgba(56, 189, 248, 0.4)":"rgba(0,0,0,0.08)",r=n?"#ffffff":"#1e293b",k=n?"#f8fafc":"#475569",S=C==="bar";return{responsive:!0,maintainAspectRatio:!1,animation:!1,interaction:{intersect:!1,mode:"index"},layout:{padding:{left:30,right:20,top:0,bottom:10}},plugins:{legend:{display:!1},title:{display:!0,text:e,align:"start",color:a,FullSize:!1,font:{size:18,weight:"600"},padding:{top:10,bottom:10}},tooltip:{backgroundColor:s,borderColor:l,borderWidth:1.5,titleColor:r,bodyColor:k,padding:12,displayColors:C!=="area",boxBorderRadius:6}},scales:{x:{stacked:S,ticks:{color:d,autoSkip:!0,maxTicksLimit:6,font:{size:11,weight:"500"}},grid:{display:!1}},y:{stacked:S,beginAtZero:!0,ticks:{color:d,font:{size:11,weight:"500"}},grid:{color:o,drawBorder:!1}}}}}function _(e,i="light"){let n=document.getElementById("energyChart");if(!e?.current)return;let a=n.getContext("2d"),d="Verbrauch f\xFCr "+Z(),o=localStorage.getItem("theme")||i,s=o==="dark",l=document.getElementById("dashboardCard");l&&(l.style.position="relative",l.style.padding="1.5rem",l.style.borderRadius="1.4rem",l.style.background="var(--card-bg)",l.style.border="1px solid var(--border)",l.style.boxShadow=s?"var(--shadow-md)":"var(--shadow-sm)");let r=document.getElementById("chartModeBtn"),k={bar:"\u{1F4CA}",line:"\u{1F4C8}",area:"\u{1F308}"};!r&&l?(r=document.createElement("button"),r.id="chartModeBtn",r.textContent=k[C],r.style.position="absolute",r.style.top="1.2rem",r.style.left="12px",r.style.width="42px",r.style.height="42px",r.style.display="flex",r.style.alignItems="center",r.style.justifyContent="center",r.style.fontSize="1.3rem",r.style.padding="0",r.style.borderRadius="999px",r.style.border="1px solid var(--border)",r.style.background="rgba(128,128,128,0.06)",r.style.color="var(--text-main)",r.style.cursor="pointer",r.style.transition="all .2s ease",r.onclick=()=>{C=C==="bar"?"line":C==="line"?"area":"bar",r.textContent=k[C],_(e,o)},l.appendChild(r)):r&&(r.textContent=k[C],r.style.color="var(--text-main)",r.style.borderColor="var(--border)"),n.style.width="100%",n.style.height="380px";let S=e.current.time||[],h=e.current.series||{},g=Object.keys(h),T=e.current.labels||{},x=e.compare?.series||e.previous?.series||null;function I(m){let u=m.chart,{ctx:v,chartArea:f}=u;if(!f)return"rgba(16, 185, 129, 0.15)";let p=v.createLinearGradient(0,f.top,0,f.bottom);return s?(p.addColorStop(0,"rgba(244, 63, 94, 0.35)"),p.addColorStop(.5,"rgba(245, 158, 11, 0.15)"),p.addColorStop(1,"rgba(16, 185, 129, 0.00)")):(p.addColorStop(0,"rgba(255, 90, 90, 0.22)"),p.addColorStop(.5,"rgba(255, 210, 0, 0.08)"),p.addColorStop(1,"rgba(0, 255, 140, 0.01)")),p}let y=[],E=[];if(C==="area"){let m=[],u=[];if(g.length>0){m=[...h[g[0]]||[]];for(let p=1;p<g.length;p++){let t=h[g[p]]||[];for(let c=0;c<m.length;c++)m[c]+=t[c]||0}}if(x&&g.length>0){u=[...x[g[0]]||[]];for(let p=1;p<g.length;p++){let t=x[g[p]]||[];for(let c=0;c<u.length;c++)u[c]+=t[c]||0}}let v=s?"hsla(142, 70%, 50%, ":"hsla(140, 90%, 45%, ",f=s?"hsla(0, 0%, 100%, ":"hsla(0, 0%, 40%, ";y.push({label:"Gesamtverbrauch (Aktuell)",data:m,type:"line",backgroundColor:I,borderColor:v+"1)",borderWidth:2.5,fill:"origin",tension:.22,pointRadius:0,pointHoverRadius:4,order:1}),x&&u.length>0&&y.push({label:"Gesamtverbrauch (Vorperiode)",data:u,type:"line",backgroundColor:"transparent",borderColor:f+(s?"0.45)":"0.55)"),borderWidth:1.5,borderDash:[5,5],fill:!1,tension:.22,pointRadius:0,pointHoverRadius:3,order:2})}else g.forEach((m,u)=>{let v=T[m]||m,f=u*(360/Math.max(1,g.length))%360,p=s?`hsla(${f}, 100%, 65%, `:`hsla(${f}, 90%, 55%, `,t=C==="bar",c=s?t?`hsla(${f}, 90%, 55%, `:"hsla(0, 0%, 100%, ":`hsla(${f}, 20%, 45%, `,D=s?"0.45)":"0.55)",ne=t?c+"0.45)":c+D;E.push({name:v,color:p+"1)",compColor:ne}),y.push({label:v,data:h[m]||[],type:t?"bar":"line",backgroundColor:t?p+"0.95)":p+"0.05)",borderColor:p+"1)",borderWidth:t?1:2,borderRadius:t?6:0,borderSkipped:t?"middle":!1,fill:!1,tension:t?0:.22,pointRadius:0,pointHoverRadius:t?0:4,stack:"current",barPercentage:.8,categoryPercentage:.7,order:1}),x&&x[m]&&y.push({label:`${v} (Vorperiode)`,data:x[m]||[],type:t?"bar":"line",backgroundColor:t?c+"0.45)":"transparent",borderColor:t?s?"rgba(15,23,42,0.5)":"rgba(255,255,255,0.5)":c+D,borderWidth:t?1:1.25,borderRadius:t?6:0,borderSkipped:t?"middle":!1,borderDash:[5,5],fill:!1,tension:t?0:.22,pointRadius:0,pointHoverRadius:t?0:3,stack:"compare",barPercentage:.8,categoryPercentage:.7,order:2})});L&&L.destroy();let b=new Chart(a,{type:C==="bar"?"bar":"line",data:{labels:S,datasets:y},options:pe(d,o)});Y(b)}var te=!1;function ue(){if(te)return;let e=document.createElement("style");e.innerHTML=`
    .header {
      position: sticky !important;
      top: 0 !important;
      z-index: 1000 !important;
    }

    .period-container {
      position: relative;
      display: inline-flex;
      align-items: center;
    }

    .period-btn {
      padding: 0.8rem 1.4rem;
      border-radius: 999px;
      border: 1px solid var(--border, rgba(255,255,255,0.15));
      background: var(--card-bg, rgba(255,255,255,0.08));
      color: var(--text-main, #ffffff);
      cursor: pointer;
      font-size: 1.35rem;
      font-weight: 500;
    }

    .period-btn::after {
      content: " \u25BE";
      opacity: 0.7;
    }

    /* \u2728 Dropdown Styles */
    .period-dropdown {
      position: absolute !important;
      top: calc(100% + 0.5rem);
      right: 0;
      min-width: 240px;
      border-radius: 1.2rem;
      padding: 0.5rem;
      z-index: 99999 !important;
      max-height: 450px;
      overflow-y: auto;
      box-shadow: var(--shadow-md, 0 8px 24px rgba(0,0,0,0.2));

      background: var(--bg2, #ffffff);
      border: 1px solid var(--border, rgba(0, 0, 0, 0.08));
    }

    [data-theme="dark"] .period-dropdown {
      background: var(--bg2, rgba(13, 20, 38, 0.94));
      border: 1px solid var(--border, rgba(255, 255, 255, 0.12));
      box-shadow: var(--shadow-md, 0 8px 24px rgba(0,0,0,0.4));
    }

    .period-dropdown.hidden {
      display: none;
    }

    .dropdown-section {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-muted, #718096);
      padding: 0.6rem 1.2rem 0.2rem 1.2rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    /* Textfarbe der Eintr\xE4ge an dein natives CSS-Theme gekoppelt */
    .period-item {
      padding: 0.8rem 1.2rem;
      border-radius: 0.8rem;
      font-size: 1.35rem;
      color: var(--text-main, #2d3748);
      cursor: pointer;
    }

    .period-item:hover {
      background: rgba(128, 128, 128, 0.12);
    }

    .archive-select-box {
      padding: 0.4rem 1.2rem 0.8rem 1.2rem;
      border-bottom: 1px dashed var(--border, #edf2f7);
      margin-bottom: 0.4rem;
    }

    .archive-select {
      width: 100%;
      padding: 0.6rem;
      border-radius: 0.6rem;
      border: 1px solid var(--border, #cbd5e1);
      background: var(--bg-color, #ffffff);
      color: var(--text-main, #2d3748);
      font-size: 1.3rem;
      outline: none;
      cursor: pointer;
    }

    .period-item.custom-toggle {
      border-top: 1px dashed var(--border, #edf2f7);
      margin-top: 0.4rem;
      padding-top: 0.8rem;
      color: var(--primary, #3182ce);
      font-weight: 600;
    }

    .inline-range-box {
      padding: 0.8rem;
      margin-top: 0.4rem;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }

    .inline-range-box.hidden {
      display: none;
    }

    .inline-field {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }

    .inline-field label {
      font-size: 1.2rem;
      font-weight: 600;
      color: var(--text-muted, #718096);
    }

    .inline-range-box input[type="date"] {
      padding: 0.5rem;
      border-radius: 0.6rem;
      border: 1px solid var(--border, #cbd5e1);
      background-color: var(--bg-color, #f7fafc) !important;
      color: var(--text-main, #2d3748) !important;
      font-size: 1.25rem;
      outline: none;
      font-family: inherit;
    }

    [data-theme="dark"] .inline-range-box input[type="date"],
    [data-theme="dark"] .archive-select {
      background-color: #020617 !important;
      color: #f8fafc !important;
      border-color: #334155 !important;
      color-scheme: dark !important;
    }

    [data-theme="dark"] .inline-range-box input[type="date"]::-webkit-calendar-picker-indicator {
      filter: invert(1) !important;
      cursor: pointer;
      opacity: 0.8;
    }

    .inline-action-btn {
      width: 100%;
      padding: 0.7rem;
      border-radius: 0.6rem;
      border: none;
      background: var(--primary, #3182ce);
      color: #ffffff;
      font-size: 1.3rem;
      font-weight: 600;
      cursor: pointer;
    }

    .toggle { display: flex; align-items: center; gap: 0.7rem; cursor: pointer; font-size: 1.3rem; color: var(--text-main); }
    .toggle input { display: none; }
    .slider { position: relative; width: 3.6rem; height: 2rem; border-radius: 999px; background: #cbd5e1; transition: .2s ease; }
    .slider::before { content: ""; position: absolute; top: 0.2rem; left: 0.2rem; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: #ffffff; transition: .2s ease; }
    .toggle input:checked + .slider { background: var(--primary, #3182ce); }
    .toggle input:checked + .slider::before { transform: translateX(1.6rem); }
  `,document.head.appendChild(e),te=!0}function F(e){let i=new Date,n=new Date,a=new Date;if(n.setHours(0,0,0,0),a.setHours(23,59,59,999),e&&e.startsWith("jahr_")){let o=parseInt(e.split("_")[1]);n.setFullYear(o,0,1),a.setFullYear(o,11,31)}else switch(e){case"heute":break;case"gestern":n.setDate(i.getDate()-1),a.setDate(i.getDate()-1);break;case"woche":{let o=i.getDay(),s=i.getDate()-o+(o===0?-6:1);n.setDate(s);break}case"7tage":n.setDate(i.getDate()-6);break;case"30tage":n.setDate(i.getDate()-29);break;case"monat":n.setDate(1);break;case"jahr":n.setMonth(0,1);break}let d=o=>{let s=l=>String(l).padStart(2,"0");return`${o.getFullYear()}-${s(o.getMonth()+1)}-${s(o.getDate())}T${s(o.getHours())}:${s(o.getMinutes())}:${s(o.getSeconds())}`};return{from:d(n),to:d(a)}}function re(e){ue();let i=document.querySelector(".controls");if(!i)return;let n=localStorage.getItem("dash_range"),a=n?JSON.parse(n):null,d=localStorage.getItem("dash_compare")!=="false",o=localStorage.getItem("dash_btn_label")||"Heute",s={Heute:"heute",Gestern:"gestern","Diese Woche":"woche","Letzte 7 Tage":"7tage","Letzte 30 Tage":"30tage","Dieser Monat":"monat"},l;s[o]?l=F(s[o]):l=a||F("heute");let r=new Date().getFullYear(),k='<option value="" disabled selected>Jahr ausw\xE4hlen...</option>';for(let t=r;t>=2013;t--)k+=`<option value="jahr_${t}">Jahr ${t}</option>`;i.innerHTML=`
    <div class="period-container">
      <button class="period-btn" id="periodBtn">${o}</button>

      <div class="period-dropdown hidden" id="periodDropdown">
        <div class="dropdown-section">Zeitraum</div>
        <div class="period-item" data-key="heute">Heute</div>
        <div class="period-item" data-key="gestern">Gestern</div>
        <div class="period-item" data-key="woche">Diese Woche</div>
        <div class="period-item" data-key="7tage">Letzte 7 Tage</div>
        <div class="period-item" data-key="30tage">Letzte 30 Tage</div>
        <div class="period-item" data-key="monat">Dieser Monat</div>

        <div class="dropdown-section">Archiv</div>
        <div class="archive-select-box">
          <select class="archive-select" id="archiveSelect">
            ${k}
          </select>
        </div>

        <div class="period-item custom-toggle" id="customToggleItem">Benutzerdefiniert\u2026</div>

        <div class="inline-range-box hidden" id="inlineRangeBox">
          <div class="inline-field">
            <label>Von</label>
            <input type="date" id="inlineFromDate">
          </div>
          <div class="inline-field">
            <label>Bis</label>
            <input type="date" id="inlineToDate">
          </div>
          <button class="inline-action-btn" id="inlineApplyBtn">Anwenden</button>
        </div>
      </div>
    </div>

    <label class="toggle">
      <input type="checkbox" id="compareToggle" ${d?"checked":""}>
      <span class="slider"></span>
      <span>Vergleich Vorperiode</span>
    </label>
  `;let S=document.getElementById("periodBtn"),h=document.getElementById("periodDropdown"),g=document.getElementById("archiveSelect"),T=document.getElementById("customToggleItem"),x=document.getElementById("inlineRangeBox"),I=document.getElementById("inlineApplyBtn"),y=document.getElementById("compareToggle"),E=document.getElementById("inlineFromDate"),b=document.getElementById("inlineToDate"),m=t=>{t&&t.from&&t.to&&(E.value=t.from.split("T")[0],b.value=t.to.split("T")[0])},u=localStorage.getItem("dash_custom_from"),v=localStorage.getItem("dash_custom_to");o==="Individuell"&&u&&v?(E.value=u,b.value=v):m(l),S.onclick=t=>{t.stopPropagation(),h.classList.toggle("hidden")},document.addEventListener("click",()=>{h.classList.add("hidden")}),h.onclick=t=>t.stopPropagation();let f=t=>({from:t.from,to:t.to,compare:y.checked?1:0}),p=(t,c)=>{o=t,l=c,S.textContent=t,O(c,t),h.classList.add("hidden"),t!=="Individuell"&&m(c),e&&e(f(c))};h.querySelectorAll(".period-item:not(.custom-toggle)").forEach(t=>{t.onclick=()=>{let c=t.getAttribute("data-key"),D=F(c);g.value="",x.classList.add("hidden"),p(t.textContent,D)}}),g.onchange=()=>{let t=g.value;if(!t)return;let c=F(t);x.classList.add("hidden"),p(`Jahr ${t.split("_")[1]}`,c)},T.onclick=()=>{x.classList.toggle("hidden")},I.onclick=()=>{let t=E.value,c=b.value;if(!t||!c)return;localStorage.setItem("dash_custom_from",t),localStorage.setItem("dash_custom_to",c);let D={from:`${t}T00:00:00`,to:`${c}T23:59:59`};g.value="",p("Individuell",D)},y.onchange=()=>{let t=y.checked;R(t),e&&e(f(l))},O(l,o),R(d),e&&e(f(l))}var oe=!1;function ae(e){if(!oe){let s=document.createElement("style");s.innerHTML=`
            #summary {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
            }

            .kpi {
                padding: 1.4rem;
                border-radius: 1.0rem;
                transition: .25s ease;

                color: var(--text-main, #ffffff);
                background: var(--card-bg, rgba(255,255,255,0.08));
                border: 1px solid var(--border, rgba(255,255,255,0.10));
                box-shadow: var(--shadow-sm, 0 2px 8px rgba(0,0,0,0.1));
            }

            .kpi:hover {
                transform: translateY(-2px);
                background: var(--border, rgba(255,255,255,0.12));
            }

            .kpi-label {
                margin-bottom: 0.6rem;
                opacity: 0.7;
                font-size: 1.2rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                color: var(--text-main, #ffffff);
            }

            .kpi-value {
                font-size: 1.5rem;
                font-weight: 700;
                letter-spacing: -0.02em;
            }

            /* \u{1F3A8} Optimierte KPI-Farben f\xFCr perfekten Kontrast in beiden Themes */
            .kpi.total .kpi-value { color: #3b82f6; }
            [data-theme="dark"] .kpi.total .kpi-value { color: #60a5fa; }

            .kpi.avg .kpi-value { color: #10b981; }
            [data-theme="dark"] .kpi.avg .kpi-value { color: #34d399; }

            .kpi.peak .kpi-value { color: #d97706; }
            [data-theme="dark"] .kpi.peak .kpi-value { color: #f59e0b; }

            .kpi.cost .kpi-value { color: #db2777; }
            [data-theme="dark"] .kpi.cost .kpi-value { color: #f472b6; }

            .kpi.delta .kpi-value { color: #7c3aed; }
            [data-theme="dark"] .kpi.delta .kpi-value { color: #a78bfa; }
        `,document.head.appendChild(s),oe=!0}let i=e&&e.total!==void 0?e.total:0,n=e&&e.avg!==void 0?e.avg:0,a=e&&e.peak!==void 0?e.peak:0,d=e&&e.cost!==void 0?e.cost:0,o=e&&e.delta!==void 0?e.delta:0;document.getElementById("summary").innerHTML=`

        <div class="kpi total">
            <div class="kpi-label">Verbrauch</div>
            <div class="kpi-value">${i.toFixed(1)} kWh</div>
        </div>

        <div class="kpi avg">
            <div class="kpi-label">Mittelwert</div>
            <div class="kpi-value">${n.toFixed(2)} kW</div>
        </div>

        <div class="kpi peak">
            <div class="kpi-label">Lastspitzen</div>
            <div class="kpi-value">${a.toFixed(1)} kW</div>
        </div>

        <div class="kpi cost">
            <div class="kpi-label">Kosten</div>
            <div class="kpi-value">${d.toFixed(2)} \u20AC</div>
        </div>

        <div class="kpi delta">
            <div class="kpi-label">Differenz</div>
            <div class="kpi-value">${o>=0?"+":""}${o.toFixed(1)} %</div>
        </div>

    `}var P=null,A=null,j=1,N=null;async function z(){try{if(!P||!A){console.warn("loadAll() called before from/to set");return}let e="POST",i="api/dashboard",n={};if(e==="POST")n={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({node:$,from_ts:P,to_ts:A,compare:j})};else{let l=new URLSearchParams({node:$,from:P,to:A,compare:j});i+=`?${l.toString()}`,n={method:"GET"}}let a=await fetch(i,n);if(!a.ok)throw new Error("API error");let d=await a.json();console.log(d),N=d.timeseries,ae(d.kpis),ee({level:d.cards.level,node:d.cards.node,items:d.cards.items,stats:d.timeseries.current.stats,series:d.timeseries.current.series});let o=document.documentElement.getAttribute("data-theme")||"light";_(d.timeseries,o),M();let s=document.getElementById("header-update");if(s){let l=new Date,r=l.toLocaleDateString("sv-SE"),k=l.toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"});s.textContent=`${r} um ${k} Uhr`}}catch(e){console.error("Dashboard load failed:",e)}}document.addEventListener("DOMContentLoaded",()=>{re(({from:e,to:i,compare:n})=>{P=e,A=i,j=n?1:0,z()}),window.addEventListener("themeChanged",e=>{let i=e.detail;N&&_(N,i)}),setInterval(z,6e4)});var J={name:"\u2713 smartmeter-dashboard ",app:"hc_smet",version:"1.6.0"};console.info("%c "+J.name+"    %c \u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E Version: "+J.version+" \u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E ","color:#FFFFFF; background:#3498db;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0","color:#2c3e50; background:#ecf0f1;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0");console.log("[cards-layout] loaded \u2014 version:",J.version);})();
//# sourceMappingURL=app.bundle.js.map
