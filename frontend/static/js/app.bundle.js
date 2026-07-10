(()=>{var W=!1;function V(e){if(!W){let s=document.createElement("style");s.innerHTML=`
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
        `,document.head.appendChild(s),W=!0}let i=e&&e.total!==void 0?e.total:0,n=e&&e.avg!==void 0?e.avg:0,a=e&&e.peak!==void 0?e.peak:0,d=e&&e.cost!==void 0?e.cost:0,r=e&&e.delta!==void 0?e.delta:0;document.getElementById("summary").innerHTML=`

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
            <div class="kpi-value">${r>=0?"+":""}${r.toFixed(1)} %</div>
        </div>

    `}var M=null;function K(e){M=e}var z=localStorage.getItem("dash_node")||"HOME",G=localStorage.getItem("dash_breadcrumb"),w=G?JSON.parse(G):["Haus"],Y=localStorage.getItem("dash_nodes"),B=Y?JSON.parse(Y):["HOME"],q=localStorage.getItem("dash_range"),ie=q?JSON.parse(q):null,se=localStorage.getItem("dash_compare")!=="false";function H(e){z=e,localStorage.setItem("dash_node",e)}function Z(e,i){w.push(e),B.push(i),localStorage.setItem("dash_breadcrumb",JSON.stringify(w)),localStorage.setItem("dash_nodes",JSON.stringify(B))}function X(e){w=w.slice(0,e+1),B=B.slice(0,e+1),z=B[e],H(z),localStorage.setItem("dash_breadcrumb",JSON.stringify(w)),localStorage.setItem("dash_nodes",JSON.stringify(B))}function O(e,i){ie=e,localStorage.setItem("dash_range",JSON.stringify(e)),i&&localStorage.setItem("dash_btn_label",i)}function R(e){se=e,localStorage.setItem("dash_compare",e)}function U(){return!w||w.length===0?"Haus":w[w.length-1]}var Q=!1;function de(){if(Q)return;let e=document.createElement("style");e.innerHTML=`
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
    `,document.head.appendChild(e),Q=!0}function ee(e,i){H(e),Z(i,e),L(),$()}function le(e){X(e),L(),$()}function L(){de();let e=document.getElementById("breadcrumb");e&&(e.className="breadcrumb",e.innerHTML="",w.forEach((i,n)=>{let a=document.createElement("div");a.className=n===w.length-1?"crumb active":"crumb";let d=n===0?'<span class="crumb-icon">\u{1F3E0}</span>':"";if(a.innerHTML=`
            ${d}
            <span>
                ${i}
            </span>
        `,a.addEventListener("click",()=>{le(n)}),e.appendChild(a),n<w.length-1){let r=document.createElement("div");r.className="crumb-divider",r.innerHTML="\u2192",e.appendChild(r)}}))}var te=!1;function ce(){if(te)return;let e=document.createElement("style");e.innerHTML=`
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
    `,document.head.appendChild(e),te=!0}function me(e,i,n){if(!i||i.length<2)return;let a=e.getContext("2d"),d=e.offsetWidth,r=e.offsetHeight,s=window.devicePixelRatio||1;e.width=d*s,e.height=r*s,a.scale(s,s),a.clearRect(0,0,d,r);let c=Math.floor(d/3),o=i;if(i.length>c){o=[];let m=i.length/c;for(let u=0;u<c;u++){let v=Math.floor(u*m),f=Math.floor((u+1)*m),p=0,t=0;for(let l=v;l<f;l++)p+=i[l],t++;o.push(p/t)}}let y=Math.min(...o),h=Math.max(...o)-y||1,g=o.map(m=>(m-y)/h),T=d/(g.length-1),x=document.documentElement.getAttribute("data-theme")==="dark",I=n||(x?"hsla(28, 100%, 58%, 1)":"#2b6cb0"),k=n||(x?"hsla(28, 100%, 60%, 1)":"#4299e1"),D=n?n.replace(/,\s*[\d.]+\)$/,", 0.28)"):x?"rgba(255, 119, 0, 0.28)":"rgba(66, 153, 225, 0.25)",b=a.createLinearGradient(0,0,0,r);b.addColorStop(0,D),b.addColorStop(1,"rgba(0, 0, 0, 0)"),a.beginPath(),g.forEach((m,u)=>{let v=u*T,f=r-m*(r-10)-5;u===0?a.moveTo(v,f):a.lineTo(v,f)}),a.lineTo(d,r),a.lineTo(0,r),a.closePath(),a.fillStyle=b,a.fill(),a.beginPath(),g.forEach((m,u)=>{let v=u*T,f=r-m*(r-10)-5;u===0?a.moveTo(v,f):a.lineTo(v,f)}),a.lineWidth=1.6,a.strokeStyle=I,a.shadowColor=k,a.shadowBlur=x?10:2,a.lineJoin="round",a.lineCap="round",a.stroke(),a.shadowBlur=0}function re(e){ce();let i=document.getElementById("cards");if(!i)return;i.innerHTML="";let n=e.stats||{},a=e.series||{},d=e.items||[],r=document.documentElement.getAttribute("data-theme")==="dark",s=Object.keys(a),c=Math.max(1,s.length);d.forEach((o,y)=>{let S=o.level==4,h=n[o.id]||{current:0,delta:0,min:0,max:0,avg:0},g=Array.isArray(a[o.id])?a[o.id]:[],T=s.indexOf(o.id),I=(T>=0?T:y)*(360/c)%360,k=r?`hsla(${I}, 100%, 65%, 1)`:`hsla(${I}, 90%, 55%, 1)`,D=r?`hsla(${I}, 80%, 55%, 0.25)`:`hsla(${I}, 70%, 50%, 0.15)`,b=document.createElement("div");S?b.className="card no-click":b.className="card",r&&(b.style.background="rgba(30, 41, 59, 0.22)"),b.style.borderTop=`3px solid ${k}`,b.setAttribute("data-active",h.current>0?"true":"false");let m=h.delta>=0;b.innerHTML=`
            <div class="card-header">
                <div>
                    <div class="card-title">${o.name}</div>
                    <div class="card-value">
                        ${(o.value??0).toFixed(1)}
                        <span class="card-unit">kWh</span>
                    </div>
                </div>
                <div class="card-delta" style="color: ${m?"#00FFC2":"#FF7A7A"};">
                    ${m?"+":""}${(o.delta??0).toFixed(1)}%
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
        `,S||b.addEventListener("click",()=>{ee(o.id,o.name)}),i.appendChild(b);let u=b.querySelector(".sparkline");u&&g.length>0&&me(u,g,k)})}var C="area";function pe(e,i){let n=i==="dark",a=n?"#ffffff":"#1e293b",d=n?"#f1f5f9":"#475569",r=n?"rgba(255, 255, 255, 0.05)":"rgba(0,0,0,0.04)",s=n?"rgba(15, 23, 42, 0.98)":"rgba(255,255,255,0.96)",c=n?"rgba(56, 189, 248, 0.4)":"rgba(0,0,0,0.08)",o=n?"#ffffff":"#1e293b",y=n?"#f8fafc":"#475569",S=C==="bar";return{responsive:!0,maintainAspectRatio:!1,animation:!1,interaction:{intersect:!1,mode:"index"},layout:{padding:{left:30,right:20,top:0,bottom:10}},plugins:{legend:{display:!1},title:{display:!0,text:e,align:"start",color:a,FullSize:!1,font:{size:18,weight:"600"},padding:{top:10,bottom:10}},tooltip:{backgroundColor:s,borderColor:c,borderWidth:1.5,titleColor:o,bodyColor:y,padding:12,displayColors:C!=="area",boxBorderRadius:6}},scales:{x:{stacked:S,ticks:{color:d,autoSkip:!0,maxTicksLimit:6,font:{size:11,weight:"500"}},grid:{display:!1}},y:{stacked:S,beginAtZero:!0,ticks:{color:d,font:{size:11,weight:"500"}},grid:{color:r,drawBorder:!1}}}}}function _(e,i="light"){let n=document.getElementById("energyChart");if(!e?.current)return;let a=n.getContext("2d"),d="Verbrauch f\xFCr "+U(),r=localStorage.getItem("theme")||i,s=r==="dark",c=document.getElementById("dashboardCard");c&&(c.style.position="relative",c.style.padding="1.5rem",c.style.borderRadius="1.4rem",c.style.background="var(--card-bg)",c.style.border="1px solid var(--border)",c.style.boxShadow=s?"var(--shadow-md)":"var(--shadow-sm)");let o=document.getElementById("chartModeBtn"),y={bar:"\u{1F4CA}",line:"\u{1F4C8}",area:"\u{1F308}"};!o&&c?(o=document.createElement("button"),o.id="chartModeBtn",o.textContent=y[C],o.style.position="absolute",o.style.top="1.2rem",o.style.left="12px",o.style.width="42px",o.style.height="42px",o.style.display="flex",o.style.alignItems="center",o.style.justifyContent="center",o.style.fontSize="1.3rem",o.style.padding="0",o.style.borderRadius="999px",o.style.border="1px solid var(--border)",o.style.background="rgba(128,128,128,0.06)",o.style.color="var(--text-main)",o.style.cursor="pointer",o.style.transition="all .2s ease",o.onclick=()=>{C=C==="bar"?"line":C==="line"?"area":"bar",o.textContent=y[C],_(e,r)},c.appendChild(o)):o&&(o.textContent=y[C],o.style.color="var(--text-main)",o.style.borderColor="var(--border)"),n.style.width="100%",n.style.height="380px";let S=e.current.time||[],h=e.current.series||{},g=Object.keys(h),T=e.current.labels||{},x=e.compare?.series||e.previous?.series||null;function I(m){let u=m.chart,{ctx:v,chartArea:f}=u;if(!f)return"rgba(16, 185, 129, 0.15)";let p=v.createLinearGradient(0,f.top,0,f.bottom);return s?(p.addColorStop(0,"rgba(244, 63, 94, 0.35)"),p.addColorStop(.5,"rgba(245, 158, 11, 0.15)"),p.addColorStop(1,"rgba(16, 185, 129, 0.00)")):(p.addColorStop(0,"rgba(255, 90, 90, 0.22)"),p.addColorStop(.5,"rgba(255, 210, 0, 0.08)"),p.addColorStop(1,"rgba(0, 255, 140, 0.01)")),p}let k=[],D=[];if(C==="area"){let m=[],u=[];if(g.length>0){m=[...h[g[0]]||[]];for(let p=1;p<g.length;p++){let t=h[g[p]]||[];for(let l=0;l<m.length;l++)m[l]+=t[l]||0}}if(x&&g.length>0){u=[...x[g[0]]||[]];for(let p=1;p<g.length;p++){let t=x[g[p]]||[];for(let l=0;l<u.length;l++)u[l]+=t[l]||0}}let v=s?"hsla(142, 70%, 50%, ":"hsla(140, 90%, 45%, ",f=s?"hsla(0, 0%, 100%, ":"hsla(0, 0%, 40%, ";k.push({label:"Gesamtverbrauch (Aktuell)",data:m,type:"line",backgroundColor:I,borderColor:v+"1)",borderWidth:2.5,fill:"origin",tension:.22,pointRadius:0,pointHoverRadius:4,order:1}),x&&u.length>0&&k.push({label:"Gesamtverbrauch (Vorperiode)",data:u,type:"line",backgroundColor:"transparent",borderColor:f+(s?"0.45)":"0.55)"),borderWidth:1.5,borderDash:[5,5],fill:!1,tension:.22,pointRadius:0,pointHoverRadius:3,order:2})}else g.forEach((m,u)=>{let v=T[m]||m,f=u*(360/Math.max(1,g.length))%360,p=s?`hsla(${f}, 100%, 65%, `:`hsla(${f}, 90%, 55%, `,t=C==="bar",l=s?t?`hsla(${f}, 90%, 55%, `:"hsla(0, 0%, 100%, ":`hsla(${f}, 20%, 45%, `,E=s?"0.45)":"0.55)",ne=t?l+"0.45)":l+E;D.push({name:v,color:p+"1)",compColor:ne}),k.push({label:v,data:h[m]||[],type:t?"bar":"line",backgroundColor:t?p+"0.95)":p+"0.05)",borderColor:p+"1)",borderWidth:t?1:2,borderRadius:t?6:0,borderSkipped:t?"middle":!1,fill:!1,tension:t?0:.22,pointRadius:0,pointHoverRadius:t?0:4,stack:"current",barPercentage:.8,categoryPercentage:.7,order:1}),x&&x[m]&&k.push({label:`${v} (Vorperiode)`,data:x[m]||[],type:t?"bar":"line",backgroundColor:t?l+"0.45)":"transparent",borderColor:t?s?"rgba(15,23,42,0.5)":"rgba(255,255,255,0.5)":l+E,borderWidth:t?1:1.25,borderRadius:t?6:0,borderSkipped:t?"middle":!1,borderDash:[5,5],fill:!1,tension:t?0:.22,pointRadius:0,pointHoverRadius:t?0:3,stack:"compare",barPercentage:.8,categoryPercentage:.7,order:2})});M&&M.destroy();let b=new Chart(a,{type:C==="bar"?"bar":"line",data:{labels:S,datasets:k},options:pe(d,r)});K(b)}var oe=!1;function ue(){if(oe)return;let e=document.createElement("style");e.innerHTML=`
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
  `,document.head.appendChild(e),oe=!0}function F(e){let i=new Date,n=new Date,a=new Date;if(n.setHours(0,0,0,0),a.setHours(23,59,59,999),e&&e.startsWith("jahr_")){let r=parseInt(e.split("_")[1]);n.setFullYear(r,0,1),a.setFullYear(r,11,31)}else switch(e){case"heute":break;case"gestern":n.setDate(i.getDate()-1),a.setDate(i.getDate()-1);break;case"woche":{let r=i.getDay(),s=i.getDate()-r+(r===0?-6:1);n.setDate(s);break}case"7tage":n.setDate(i.getDate()-6);break;case"30tage":n.setDate(i.getDate()-29);break;case"monat":n.setDate(1);break;case"jahr":n.setMonth(0,1);break}let d=r=>{let s=c=>String(c).padStart(2,"0");return`${r.getFullYear()}-${s(r.getMonth()+1)}-${s(r.getDate())}T${s(r.getHours())}:${s(r.getMinutes())}:${s(r.getSeconds())}`};return{from:d(n),to:d(a)}}function ae(e){ue();let i=document.querySelector(".controls");if(!i)return;let n=localStorage.getItem("dash_range"),a=n?JSON.parse(n):null,d=localStorage.getItem("dash_compare")!=="false",r=localStorage.getItem("dash_btn_label")||"Heute",s={Heute:"heute",Gestern:"gestern","Diese Woche":"woche","Letzte 7 Tage":"7tage","Letzte 30 Tage":"30tage","Dieser Monat":"monat"},c;s[r]?c=F(s[r]):c=a||F("heute");let o=new Date().getFullYear(),y='<option value="" disabled selected>Jahr ausw\xE4hlen...</option>';for(let t=o;t>=2013;t--)y+=`<option value="jahr_${t}">Jahr ${t}</option>`;i.innerHTML=`
    <div class="period-container">
      <button class="period-btn" id="periodBtn">${r}</button>

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
            ${y}
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
  `;let S=document.getElementById("periodBtn"),h=document.getElementById("periodDropdown"),g=document.getElementById("archiveSelect"),T=document.getElementById("customToggleItem"),x=document.getElementById("inlineRangeBox"),I=document.getElementById("inlineApplyBtn"),k=document.getElementById("compareToggle"),D=document.getElementById("inlineFromDate"),b=document.getElementById("inlineToDate"),m=t=>{t&&t.from&&t.to&&(D.value=t.from.split("T")[0],b.value=t.to.split("T")[0])},u=localStorage.getItem("dash_custom_from"),v=localStorage.getItem("dash_custom_to");r==="Individuell"&&u&&v?(D.value=u,b.value=v):m(c),S.onclick=t=>{t.stopPropagation(),h.classList.toggle("hidden")},document.addEventListener("click",()=>{h.classList.add("hidden")}),h.onclick=t=>t.stopPropagation();let f=t=>({from:t.from,to:t.to,compare:k.checked?1:0}),p=(t,l)=>{r=t,c=l,S.textContent=t,O(l,t),h.classList.add("hidden"),t!=="Individuell"&&m(l),e&&e(f(l))};h.querySelectorAll(".period-item:not(.custom-toggle)").forEach(t=>{t.onclick=()=>{let l=t.getAttribute("data-key"),E=F(l);g.value="",x.classList.add("hidden"),p(t.textContent,E)}}),g.onchange=()=>{let t=g.value;if(!t)return;let l=F(t);x.classList.add("hidden"),p(`Jahr ${t.split("_")[1]}`,l)},T.onclick=()=>{x.classList.toggle("hidden")},I.onclick=()=>{let t=D.value,l=b.value;if(!t||!l)return;localStorage.setItem("dash_custom_from",t),localStorage.setItem("dash_custom_to",l);let E={from:`${t}T00:00:00`,to:`${l}T23:59:59`};g.value="",p("Individuell",E)},k.onchange=()=>{let t=k.checked;R(t),e&&e(f(c))},O(c,r),R(d),e&&e(f(c))}var P=null,A=null,j=1,N=null;async function $(){try{if(!P||!A){console.warn("loadAll() called before from/to set");return}let e="POST",i="api/dashboard",n={};if(e==="POST")n={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({node:z,from_ts:P,to_ts:A,compare:j})};else{let s=new URLSearchParams({node:z,from:P,to:A,compare:j});i+=`?${s.toString()}`,n={method:"GET"}}let a=await fetch(i,n);if(!a.ok)throw new Error("API error");let d=await a.json();console.log(d),N=d.timeseries,V(d.kpis),re({level:d.cards.level,node:d.cards.node,items:d.cards.items,stats:d.timeseries.current.stats,series:d.timeseries.current.series});let r=document.documentElement.getAttribute("data-theme")||"light";_(d.timeseries,r),L()}catch(e){console.error("Dashboard load failed:",e)}}document.addEventListener("DOMContentLoaded",()=>{ae(({from:e,to:i,compare:n})=>{P=e,A=i,j=n?1:0,$()}),window.addEventListener("themeChanged",e=>{let i=e.detail;N&&_(N,i)}),setInterval($,6e4)});var J={name:"\u2713 smartmeter-dashboard ",app:"hc_smet",version:"1.6.0"};console.info("%c "+J.name+"    %c \u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E Version: "+J.version+" \u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E ","color:#FFFFFF; background:#3498db;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0","color:#2c3e50; background:#ecf0f1;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0");console.log("[cards-layout] loaded \u2014 version:",J.version);})();
//# sourceMappingURL=app.bundle.js.map
