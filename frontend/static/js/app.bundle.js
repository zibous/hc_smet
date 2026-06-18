(()=>{var J=!1;function W(e){if(!J){let o=document.createElement("style");o.innerHTML=`
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

                // \u2600\uFE0F\u{1F319} NATIVE THEME VARIABLES (Ersetzt harte Farben)
                color: var(--text-main, #ffffff);
                background: var(--card-bg, rgba(255,255,255,0.08));
                border: 1px solid var(--border, rgba(255,255,255,0.10));

                backdrop-filter: blur(18px);
                -webkit-backdrop-filter: blur(18px);
                box-shadow: 0 6px 18px rgba(0,0,0,0.15);
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
        `,document.head.appendChild(o),J=!0}let a=e&&e.total!==void 0?e.total:0,t=e&&e.avg!==void 0?e.avg:0,l=e&&e.peak!==void 0?e.peak:0,s=e&&e.cost!==void 0?e.cost:0,n=e&&e.delta!==void 0?e.delta:0;document.getElementById("summary").innerHTML=`

        <div class="kpi total">
            <div class="kpi-label">Verbrauch</div>
            <div class="kpi-value">${a.toFixed(1)} kWh</div>
        </div>

        <div class="kpi avg">
            <div class="kpi-label">Mittelwert</div>
            <div class="kpi-value">${t.toFixed(2)} kW</div>
        </div>

        <div class="kpi peak">
            <div class="kpi-label">Lastspitzen</div>
            <div class="kpi-value">${l.toFixed(1)} kW</div>
        </div>

        <div class="kpi cost">
            <div class="kpi-label">Kosten</div>
            <div class="kpi-value">${s.toFixed(2)} \u20AC</div>
        </div>

        <div class="kpi delta">
            <div class="kpi-label">Differenz</div>
            <div class="kpi-value">${n>=0?"+":""}${n.toFixed(1)} %</div>
        </div>

    `}var F=null;function Z(e){F=e}var D=localStorage.getItem("dash_node")||"HOME",G=localStorage.getItem("dash_breadcrumb"),y=G?JSON.parse(G):["Haus"],Y=localStorage.getItem("dash_nodes"),B=Y?JSON.parse(Y):["HOME"],q=localStorage.getItem("dash_range"),ie=q?JSON.parse(q):null,se=localStorage.getItem("dash_compare")!=="false";function P(e){D=e,localStorage.setItem("dash_node",e)}function K(e,a){y.push(e),B.push(a),localStorage.setItem("dash_breadcrumb",JSON.stringify(y)),localStorage.setItem("dash_nodes",JSON.stringify(B))}function U(e){y=y.slice(0,e+1),B=B.slice(0,e+1),D=B[e],P(D),localStorage.setItem("dash_breadcrumb",JSON.stringify(y)),localStorage.setItem("dash_nodes",JSON.stringify(B))}function N(e,a){ie=e,localStorage.setItem("dash_range",JSON.stringify(e)),a&&localStorage.setItem("dash_btn_label",a)}function R(e){se=e,localStorage.setItem("dash_compare",e)}function X(){return!y||y.length===0?"Haus":y[y.length-1]}var Q=!1;function de(){if(Q)return;let e=document.createElement("style");e.innerHTML=`
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

            // \u2600\uFE0F\u{1F319} NATIVE THEME VARIABLES (Ersetzt harte Farben)
            color: var(--text-main, rgba(255,255,255,0.92));
            background: var(--card-bg, rgba(255,255,255,0.08));
            border: 1px solid var(--border, rgba(255,255,255,0.10));

            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow: 0 4px 14px rgba(0,0,0,0.15);
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
    `,document.head.appendChild(e),Q=!0}function ee(e,a){P(e),K(a,e),L(),M()}function le(e){U(e),L(),M()}function L(){de();let e=document.getElementById("breadcrumb");e&&(e.className="breadcrumb",e.innerHTML="",y.forEach((a,t)=>{let l=document.createElement("div");l.className=t===y.length-1?"crumb active":"crumb";let s=t===0?'<span class="crumb-icon">\u{1F3E0}</span>':"";if(l.innerHTML=`
            ${s}
            <span>
                ${a}
            </span>
        `,l.addEventListener("click",()=>{le(t)}),e.appendChild(l),t<y.length-1){let n=document.createElement("div");n.className="crumb-divider",n.innerHTML="\u2192",e.appendChild(n)}}))}var te=!1;function ce(){if(te)return;let e=document.createElement("style");e.innerHTML=`
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

            // \u2600\uFE0F\u{1F319} NATIVE THEME VARIABLES (Ersetzt harte Farben)
            color: var(--text-main, #ffffff);
            background: var(--card-bg, rgba(255,255,255,0.10));
            border: 1px solid var(--border, rgba(255,255,255,0.10));

            backdrop-filter: blur(22px);
            -webkit-backdrop-filter: blur(22px);

            box-shadow:
                0 8px 24px rgba(0,0,0,0.12),
                inset 0 1px 0 rgba(255,255,255,0.05);

            transition:
                transform .25s ease,
                box-shadow .25s ease,
                background .25s ease;
        }

        .card:hover {
            transform: translateY(-4px);
            border-color: var(--primary, #3182ce);
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
            backdrop-filter: blur(10px);
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
    `,document.head.appendChild(e),te=!0}function pe(e,a){if(!a||a.length<2)return;let t=e.getContext("2d"),l=e.offsetWidth,s=e.offsetHeight,n=window.devicePixelRatio||1;e.width=l*n,e.height=s*n,t.scale(n,n),t.clearRect(0,0,l,s);let o=Math.floor(l/3),d=a;if(a.length>o){d=[];let x=a.length/o;for(let m=0;m<o;m++){let b=Math.floor(m*x),f=Math.floor((m+1)*x),v=0,c=0;for(let r=b;r<f;r++)v+=a[r],c++;d.push(v/c)}}let i=Math.min(...d),g=Math.max(...d)-i||1,h=d.map(x=>(x-i)/g),u=l/(h.length-1),E=document.documentElement.getAttribute("data-theme")==="dark",k=E?"hsla(28, 100%, 58%, 1)":"#2b6cb0",z=E?"hsla(28, 100%, 60%, 1)":"#4299e1",S=E?"rgba(255, 119, 0, 0.28)":"rgba(66, 153, 225, 0.25)",I=t.createLinearGradient(0,0,0,s);I.addColorStop(0,S),I.addColorStop(1,"rgba(0, 0, 0, 0)"),t.beginPath(),h.forEach((x,m)=>{let b=m*u,f=s-x*(s-10)-5;m===0?t.moveTo(b,f):t.lineTo(b,f)}),t.lineTo(l,s),t.lineTo(0,s),t.closePath(),t.fillStyle=I,t.fill(),t.beginPath(),h.forEach((x,m)=>{let b=m*u,f=s-x*(s-10)-5;m===0?t.moveTo(b,f):t.lineTo(b,f)}),t.lineWidth=1.6,t.strokeStyle=k,t.shadowColor=z,t.shadowBlur=E?10:2,t.lineJoin="round",t.lineCap="round",t.stroke(),t.shadowBlur=0}function re(e){ce();let a=document.getElementById("cards");if(!a)return;a.innerHTML="";let t=e.stats||{},l=e.series||{},s=e.items||[],n=document.documentElement.getAttribute("data-theme")==="dark";s.forEach(o=>{let d=o.level==4,i=t[o.id]||{current:0,delta:0,min:0,max:0,avg:0},w=Array.isArray(l[o.id])?l[o.id]:[],g=document.createElement("div");d?g.className="card no-click":g.className="card",n&&(g.style.background="rgba(30, 41, 59, 0.22)"),g.setAttribute("data-active",i.current>0?"true":"false");let h=i.delta>=0;g.innerHTML=`
            <div class="card-header">
                <div>
                    <div class="card-title">${o.name}</div>
                    <div class="card-value">
                        ${(o.value??0).toFixed(1)}
                        <span class="card-unit">kWh</span>
                    </div>
                </div>
                <div class="card-delta" style="color: ${h?"#00FFC2":"#FF7A7A"};">
                    ${h?"+":""}${(o.delta??0).toFixed(1)}%
                </div>
            </div>

            <div class="sparkline-wrapper">
                <canvas class="sparkline"></canvas>
            </div>

            <div class="card-stats">
                <div class="stat">
                    <div class="stat-label">Min</div>
                    <div class="stat-value">${(i.min??0).toFixed(1)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Max</div>
                    <div class="stat-value">${(i.max??0).toFixed(1)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Schnitt</div>
                    <div class="stat-value">${(i.avg??0).toFixed(1)}</div>
                </div>
            </div>
        `,d||g.addEventListener("click",()=>{ee(o.id,o.name)}),a.appendChild(g);let u=g.querySelector(".sparkline");u&&w.length>0&&pe(u,w)})}var C="area";function me(e,a){let t=a==="dark",l=t?"#ffffff":"#1e293b",s=t?"#f1f5f9":"#475569",n=t?"rgba(255, 255, 255, 0.05)":"rgba(0,0,0,0.04)",o=t?"rgba(15, 23, 42, 0.98)":"rgba(255,255,255,0.96)",d=t?"rgba(56, 189, 248, 0.4)":"rgba(0,0,0,0.08)",i=t?"#ffffff":"#1e293b",w=t?"#f8fafc":"#475569",g=C==="bar";return{responsive:!0,maintainAspectRatio:!1,animation:!1,interaction:{intersect:!1,mode:"index"},layout:{padding:{left:30,right:20,top:0,bottom:10}},plugins:{legend:{display:!1},title:{display:!0,text:e,align:"start",color:l,FullSize:!1,font:{size:18,weight:"600"},padding:{top:10,bottom:10}},tooltip:{backgroundColor:o,borderColor:d,borderWidth:1.5,titleColor:i,bodyColor:w,padding:12,displayColors:C!=="area",boxBorderRadius:6}},scales:{x:{stacked:g,ticks:{color:s,autoSkip:!0,maxTicksLimit:6,font:{size:11,weight:"500"}},grid:{display:!1}},y:{stacked:g,beginAtZero:!0,ticks:{color:s,font:{size:11,weight:"500"}},grid:{color:n,drawBorder:!1}}}}}function A(e,a="light"){let t=document.getElementById("energyChart");if(!e?.current)return;let l=t.getContext("2d"),s="Verbrauch f\xFCr "+X(),n=localStorage.getItem("theme")||a,o=n==="dark",d=document.getElementById("dashboardCard");d&&(d.style.position="relative",d.style.padding="1.5rem",d.style.borderRadius="1.4rem",d.style.background=o?"rgba(30, 41, 59, 0.25)":"var(--card-bg)",d.style.border="1px solid var(--border)",d.style.backdropFilter="blur(22px)",d.style.webkitBackdropFilter="blur(22px)",d.style.boxShadow=o?"0 20px 40px rgba(0,0,0,0.5)":"0 10px 30px rgba(0,0,0,0.15)");let i=document.getElementById("chartModeBtn"),w={bar:"\u{1F4CA}",line:"\u{1F4C8}",area:"\u{1F308}"};!i&&d?(i=document.createElement("button"),i.id="chartModeBtn",i.textContent=w[C],i.style.position="absolute",i.style.top="1.2rem",i.style.left="12px",i.style.width="42px",i.style.height="42px",i.style.display="flex",i.style.alignItems="center",i.style.justifyContent="center",i.style.fontSize="1.3rem",i.style.padding="0",i.style.borderRadius="999px",i.style.border="1px solid var(--border)",i.style.background="rgba(128,128,128,0.06)",i.style.color="var(--text-main)",i.style.cursor="pointer",i.style.backdropFilter="blur(10px)",i.style.transition="all .2s ease",i.onclick=()=>{C=C==="bar"?"line":C==="line"?"area":"bar",i.textContent=w[C],A(e,n)},d.appendChild(i)):i&&(i.textContent=w[C],i.style.color="var(--text-main)",i.style.borderColor="var(--border)"),t.style.width="100%",t.style.height="380px";let g=e.current.time||[],h=e.current.series||{},u=Object.keys(h),E=e.current.labels||{},k=e.compare?.series||e.previous?.series||null;function z(m){let b=m.chart,{ctx:f,chartArea:v}=b;if(!v)return"rgba(16, 185, 129, 0.15)";let c=f.createLinearGradient(0,v.top,0,v.bottom);return o?(c.addColorStop(0,"rgba(244, 63, 94, 0.35)"),c.addColorStop(.5,"rgba(245, 158, 11, 0.15)"),c.addColorStop(1,"rgba(16, 185, 129, 0.00)")):(c.addColorStop(0,"rgba(255, 90, 90, 0.22)"),c.addColorStop(.5,"rgba(255, 210, 0, 0.08)"),c.addColorStop(1,"rgba(0, 255, 140, 0.01)")),c}let S=[],I=[];if(C==="area"){let m=[],b=[];if(u.length>0){m=[...h[u[0]]||[]];for(let c=1;c<u.length;c++){let r=h[u[c]]||[];for(let p=0;p<m.length;p++)m[p]+=r[p]||0}}if(k&&u.length>0){b=[...k[u[0]]||[]];for(let c=1;c<u.length;c++){let r=k[u[c]]||[];for(let p=0;p<b.length;p++)b[p]+=r[p]||0}}let f=o?"hsla(142, 70%, 50%, ":"hsla(140, 90%, 45%, ",v=o?"hsla(0, 0%, 100%, ":"hsla(0, 0%, 40%, ";S.push({label:"Gesamtverbrauch (Aktuell)",data:m,type:"line",backgroundColor:z,borderColor:f+"1)",borderWidth:2.5,fill:"origin",tension:.22,pointRadius:0,pointHoverRadius:4,order:1}),k&&b.length>0&&S.push({label:"Gesamtverbrauch (Vorperiode)",data:b,type:"line",backgroundColor:"transparent",borderColor:v+(o?"0.45)":"0.55)"),borderWidth:1.5,borderDash:[5,5],fill:!1,tension:.22,pointRadius:0,pointHoverRadius:3,order:2})}else u.forEach((m,b)=>{let f=E[m]||m,v=b*(360/Math.max(1,u.length))%360,c=o?`hsla(${v}, 100%, 65%, `:`hsla(${v}, 90%, 55%, `,r=C==="bar",p=o?r?`hsla(${v}, 90%, 55%, `:"hsla(0, 0%, 100%, ":`hsla(${v}, 20%, 45%, `,T=o?"0.45)":"0.55)",ne=r?p+"0.45)":p+T;I.push({name:f,color:c+"1)",compColor:ne}),S.push({label:f,data:h[m]||[],type:r?"bar":"line",backgroundColor:r?c+"0.95)":c+"0.05)",borderColor:c+"1)",borderWidth:r?1:2,borderRadius:r?6:0,borderSkipped:r?"middle":!1,fill:!1,tension:r?0:.22,pointRadius:0,pointHoverRadius:r?0:4,stack:"current",barPercentage:.8,categoryPercentage:.7,order:1}),k&&k[m]&&S.push({label:`${f} (Vorperiode)`,data:k[m]||[],type:r?"bar":"line",backgroundColor:r?p+"0.45)":"transparent",borderColor:r?o?"rgba(15,23,42,0.5)":"rgba(255,255,255,0.5)":p+T,borderWidth:r?1:1.25,borderRadius:r?6:0,borderSkipped:r?"middle":!1,borderDash:[5,5],fill:!1,tension:r?0:.22,pointRadius:0,pointHoverRadius:r?0:3,stack:"compare",barPercentage:.8,categoryPercentage:.7,order:2})});F&&F.destroy();let x=new Chart(l,{type:C==="bar"?"bar":"line",data:{labels:g,datasets:S},options:me(s,n)});Z(x)}var ae=!1;function ue(){if(ae)return;let e=document.createElement("style");e.innerHTML=`
    .header {
      position: relative !important;
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
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
    }

    .period-btn::after {
      content: " \u25BE";
      opacity: 0.7;
    }

    /* \u2728 NEU: Mattiertes, blickdichtes VisionOS-Glas f\xFCr das Dropdown gegen Durchscheinen */
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

      /* Starke Unsch\xE4rfe und massiver Schatten f\xFCr r\xE4umliche Abhebung */
      backdrop-filter: blur(35px) saturate(160%);
      -webkit-backdrop-filter: blur(35px) saturate(160%);
      box-shadow: 0 20px 50px rgba(0,0,0,0.35);

      /* Theme-Weiche: Sattes Dunkelblau nachts, deckendes Milchwei\xDF tags\xFCber */
      background: rgba(255, 255, 255, 0.88);
      border: 1px solid rgba(0, 0, 0, 0.08);
    }

    [data-theme="dark"] .period-dropdown {
      background: rgba(13, 20, 38, 0.94);
      border: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: 0 25px 60px rgba(0,0,0,0.65);
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
  `,document.head.appendChild(e),ae=!0}function $(e){let a=new Date,t=new Date,l=new Date;if(t.setHours(0,0,0,0),l.setHours(23,59,59,999),e&&e.startsWith("jahr_")){let n=parseInt(e.split("_")[1]);t.setFullYear(n,0,1),l.setFullYear(n,11,31)}else switch(e){case"heute":break;case"gestern":t.setDate(a.getDate()-1),l.setDate(a.getDate()-1);break;case"woche":{let n=a.getDay(),o=a.getDate()-n+(n===0?-6:1);t.setDate(o);break}case"7tage":t.setDate(a.getDate()-6);break;case"30tage":t.setDate(a.getDate()-29);break;case"monat":t.setDate(1);break;case"jahr":t.setMonth(0,1);break}let s=n=>{let o=d=>String(d).padStart(2,"0");return`${n.getFullYear()}-${o(n.getMonth()+1)}-${o(n.getDate())}T${o(n.getHours())}:${o(n.getMinutes())}:${o(n.getSeconds())}`};return{from:s(t),to:s(l)}}function oe(e){ue();let a=document.querySelector(".controls");if(!a)return;let t=localStorage.getItem("dash_range"),l=t?JSON.parse(t):null,s=localStorage.getItem("dash_compare")!=="false",n=localStorage.getItem("dash_btn_label")||"Heute",o={Heute:"heute",Gestern:"gestern","Diese Woche":"woche","Letzte 7 Tage":"7tage","Letzte 30 Tage":"30tage","Dieser Monat":"monat"},d;o[n]?d=$(o[n]):d=l||$("heute");let i=new Date().getFullYear(),w='<option value="" disabled selected>Jahr ausw\xE4hlen...</option>';for(let r=i;r>=2013;r--)w+=`<option value="jahr_${r}">Jahr ${r}</option>`;a.innerHTML=`
    <div class="period-container">
      <button class="period-btn" id="periodBtn">${n}</button>

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
            ${w}
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
      <input type="checkbox" id="compareToggle" ${s?"checked":""}>
      <span class="slider"></span>
      <span>Vergleich Vorperiode</span>
    </label>
  `;let g=document.getElementById("periodBtn"),h=document.getElementById("periodDropdown"),u=document.getElementById("archiveSelect"),E=document.getElementById("customToggleItem"),k=document.getElementById("inlineRangeBox"),z=document.getElementById("inlineApplyBtn"),S=document.getElementById("compareToggle"),I=document.getElementById("inlineFromDate"),x=document.getElementById("inlineToDate"),m=r=>{r&&r.from&&r.to&&(I.value=r.from.split("T")[0],x.value=r.to.split("T")[0])},b=localStorage.getItem("dash_custom_from"),f=localStorage.getItem("dash_custom_to");n==="Individuell"&&b&&f?(I.value=b,x.value=f):m(d),g.onclick=r=>{r.stopPropagation(),h.classList.toggle("hidden")},document.addEventListener("click",()=>{h.classList.add("hidden")}),h.onclick=r=>r.stopPropagation();let v=r=>({from:r.from,to:r.to,compare:S.checked?1:0}),c=(r,p)=>{n=r,d=p,g.textContent=r,N(p,r),h.classList.add("hidden"),r!=="Individuell"&&m(p),e&&e(v(p))};h.querySelectorAll(".period-item:not(.custom-toggle)").forEach(r=>{r.onclick=()=>{let p=r.getAttribute("data-key"),T=$(p);u.value="",k.classList.add("hidden"),c(r.textContent,T)}}),u.onchange=()=>{let r=u.value;if(!r)return;let p=$(r);k.classList.add("hidden"),c(`Jahr ${r.split("_")[1]}`,p)},E.onclick=()=>{k.classList.toggle("hidden")},z.onclick=()=>{let r=I.value,p=x.value;if(!r||!p)return;localStorage.setItem("dash_custom_from",r),localStorage.setItem("dash_custom_to",p);let T={from:`${r}T00:00:00`,to:`${p}T23:59:59`};u.value="",c("Individuell",T)},S.onchange=()=>{let r=S.checked;R(r),e&&e(v(d))},N(d,n),R(s),e&&e(v(d))}var _=null,H=null,O=1,j=null;async function M(){try{if(!_||!H){console.warn("loadAll() called before from/to set");return}let e="POST",a="api/dashboard",t={};if(e==="POST")t={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({node:D,from_ts:_,to_ts:H,compare:O})};else{let o=new URLSearchParams({node:D,from:_,to:H,compare:O});a+=`?${o.toString()}`,t={method:"GET"}}let l=await fetch(a,t);if(!l.ok)throw new Error("API error");let s=await l.json();console.log(s),j=s.timeseries,W(s.kpis),re({level:s.cards.level,node:s.cards.node,items:s.cards.items,stats:s.timeseries.current.stats,series:s.timeseries.current.series});let n=document.documentElement.getAttribute("data-theme")||"light";A(s.timeseries,n),L()}catch(e){console.error("Dashboard load failed:",e)}}document.addEventListener("DOMContentLoaded",()=>{oe(({from:e,to:a,compare:t})=>{_=e,H=a,O=t?1:0,M()}),window.addEventListener("themeChanged",e=>{let a=e.detail;j&&A(j,a)}),setInterval(M,6e4)});var V={name:"\u2713 smartmeter-dashboard ",app:"hc_smet",version:"1.6.0"};console.info("%c "+V.name+"    %c \u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E Version: "+V.version+" \u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E\u25AA\uFE0E ","color:#FFFFFF; background:#3498db;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0","color:#2c3e50; background:#ecf0f1;display:inline-block;font-size:12px;font-weight:200;padding: 4px 0 4px 0");console.log("[cards-layout] loaded \u2014 version:",V.version);})();
//# sourceMappingURL=app.bundle.js.map
