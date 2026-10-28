/* Receipt preview is a print-only checklist. It never selects numbers or changes a plan. */
const receiptEscape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const receiptMoney=n=>'PHP '+Number(n).toFixed(2);
function receiptLines(plan,scope='pending',category='all',now=Date.now()){
 if(!validWeekPlan(plan))return [];
 const today=new Date(now+288e5).toISOString().slice(0,10);
 return plan.lines.filter(x=>(category==='all'||x.game===category)&&(scope==='all'||(plan.weekStart===planWeek(now)&&planState(x,now)==='planned'&&(scope!=='today'||x.betAt.slice(0,10)===today)))).slice().sort((a,b)=>a.drawAt.localeCompare(b.drawAt)||a.game.localeCompare(b.game));
}
function receiptMarkup(plan,lines,scope='pending',now=Date.now()){
 const label={pending:'Pending upcoming bets',today:'Today’s pending bets',all:'Full week · includes status marks'}[scope]||'Selected lines';
 let h=`<div class="receipt-heading"><strong>LOTTO TRACKER</strong><p>PERSONAL BETTING CHECKLIST<br>NOT AN OFFICIAL LOTTERY TICKET</p></div><div class="receipt-meta"><p>Week: ${receiptEscape(plan.weekStart)} to ${receiptEscape(plan.weekEnd)}</p><p>${label}</p><p>Printed: ${receiptEscape(ticketDate(now))} · PH</p></div>`;
 if(!lines.length)return h+'<p class="receipt-empty">No lines match this selection.<br>Choose another category or scope.</p>';
 for(const g of GS){const group=lines.filter(x=>x.game===g);if(!group.length)continue;
 h+=`<section class="receipt-category"><h3>${receiptEscape(NAME[g])}</h3>${group.map((x,i)=>`<div class="receipt-line"><div class="receipt-between"><b>LINE ${i+1}</b><span>${receiptEscape({planned:'PLANNED',placed:'MARKED PLACED',skip:'SKIPPED',missed:'EXPIRED / NOT PLACED'}[planState(x,now)])}</span></div><p>Bet: ${receiptEscape(ticketDate(Date.parse(x.betAt)))}</p><p>Draw: ${receiptEscape(ticketDate(Date.parse(x.drawAt)))}</p><p class="receipt-numbers">${x.numbers.slice().sort((a,b)=>a-b).map(pad).join(' - ')}</p><div class="receipt-between"><span>1 ordinary line</span><b>${receiptMoney(x.cost)}</b></div></div>`).join('')}<div class="receipt-between receipt-subtotal"><span>${group.length} line${group.length===1?'':'s'} · subtotal</span><b>${receiptMoney(group.reduce((v,x)=>v+x.cost,0))}</b></div></section>`}
 const total=lines.reduce((v,x)=>v+x.cost,0);
 return h+`<div class="receipt-total receipt-between"><span>${lines.length} LINES · TOTAL</span><strong>${receiptMoney(total)}</strong></div><p class="receipt-note">Auto plan weekly cap: PHP 300.00<br>This receipt totals the displayed lines only.<br>All dates and times are Philippine time.<br>Betting times are suggestions; verify outlet cut-off and PCSO schedule.</p><div class="receipt-bottom">CHECK GAME · DATE · NUMBERS<br>Printing does not purchase a ticket.<br>Keep the official outlet ticket as proof.</div>`;
}
function refreshReceipt(){const dialog=document.getElementById('receipt-preview');if(!dialog)return;
 const scope=dialog.querySelector('#receipt-scope').value,category=dialog.querySelector('#receipt-category').value,lines=receiptLines(WEEKLY,scope,category);
 dialog.querySelector('.receipt-paper').innerHTML=receiptMarkup(WEEKLY,lines,scope);
 dialog.querySelector('[data-receipt-print]').disabled=lines.length===0;
}
function openPlanReceipt(){if(!WEEKLY||!validWeekPlan(WEEKLY))return;
 document.getElementById('receipt-preview')?.close();document.getElementById('receipt-preview')?.remove();
 const dialog=document.createElement('dialog');dialog.id='receipt-preview';dialog.setAttribute('aria-labelledby','receipt-title');
 dialog.innerHTML=`<div class="receipt-toolbar"><div><h2 id="receipt-title">Print Auto Plan</h2><p class="cap">Numbers grouped by category · receipt preview</p></div><button class="btn" data-receipt-close aria-label="Close print preview">Close</button></div><div class="receipt-controls"><label>Include<select id="receipt-scope" class="tx"><option value="pending">Pending upcoming bets</option><option value="today">Today’s pending bets</option><option value="all">Full week (all statuses)</option></select></label><label>Category<select id="receipt-category" class="tx"><option value="all">All games</option>${GS.map(g=>`<option value="${g}" ${game===g?'selected':''}>${receiptEscape(NAME[g])}</option>`).join('')}</select></label><button class="btn chosen" data-receipt-print>Print / Save PDF</button></div><p class="cap receipt-print-help">80 mm receipt-style layout. Choose your printer’s paper size or Save as PDF in the print dialog. Only the receipt is printed.</p><div class="receipt-stage"><div class="receipt-paper"></div></div>`;
 dialog.addEventListener('change',refreshReceipt);
 dialog.addEventListener('click',e=>{if(e.target.closest('[data-receipt-close]'))dialog.close();if(e.target.closest('[data-receipt-print]'))window.print()});
 dialog.addEventListener('close',()=>{document.body.classList.remove('receipt-preview-open');dialog.remove()});
 document.body.appendChild(dialog);refreshReceipt();document.body.classList.add('receipt-preview-open');dialog.showModal();
}
