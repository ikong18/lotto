const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
require('./engine.js');
const config=JSON.parse(fs.readFileSync('sets.json'));
for(const [g,max] of Object.entries({ultra:58,grand:55,super:49,mega:45,lotto:42})){
  for(const draws of [[],JSON.parse(fs.readFileSync('results.json')).draws.filter(d=>d.game===g)]){
    const a=Engine.analyze(draws,g,config,new Set(config.personal));
    assert.ok(Number.isFinite(a.chi));
    assert.ok(a.p===null||(a.p>=0&&a.p<=1));
    assert.equal(a.picks.length,5);assert.ok(a.maxOverlap<=2);for(const p of a.picks)assert.ok(!(config.sets[g]||[]).some(c=>c.slice().sort((a,b)=>a-b).join()===p.c.join()));
    for(const p of a.picks){assert.equal(new Set(p.c).size,6);assert.ok(p.c.every(n=>Number.isInteger(n)&&n>=1&&n<=max));}
    assert.deepEqual(a.picks,Engine.analyze(draws,g,config,new Set(config.personal)).picks);
  }
}
const html=fs.readFileSync('index.html','utf8');
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
new vm.Script(script);
const app={innerHTML:''};
const ctx={Engine,location:{hostname:"localhost",pathname:"/"},console,Date,Set,Math,JSON,Number,String,Array,Object,Promise,URL,window:{},document:{querySelector:()=>app,querySelectorAll:()=>[],addEventListener:()=>{}},fetch:()=>new Promise(()=>{}),addEventListener:()=>{},setInterval:()=>{},matchMedia:()=>({matches:true}),localStorage:{},requestAnimationFrame:()=>{}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('tickets.js','utf8'),ctx);vm.runInContext(script,ctx);
vm.runInContext(`C=${JSON.stringify(config)}; R=[]; EM={draw:true,weekly:true,onlyWins:false}; P=new Set(C.personal);`,ctx);
for(const recorded of [[],JSON.parse(fs.readFileSync('results.json')).draws]){
vm.runInContext('R='+JSON.stringify(recorded),ctx);
for(const game of ['all','ultra','grand','super','mega','lotto'])for(const view of ['results','upcoming','budget','engine','mynumbers','settings','history','overview','numbers']){
 vm.runInContext(`game='${game}';view='${view}';render()`,ctx);
 assert.ok(app.innerHTML.length>0,`${game}/${view}`);
 assert.ok(!/NaN|Infinity/.test(app.innerHTML),`${game}/${view} finite output`);
}
}
vm.runInContext(`const d={sets:structuredClone(C.sets),prizeEst:C.prizeEst,personal:[],costPerPlay:25};d.sets.grand=[[1,1,2,3,4,5]];if(!valid(d).length)throw Error('Grand validation missing')`,Object.assign(ctx,{structuredClone}));
console.log('Passed: engine invariants, repeatability, all empty-history views and five-game validation.');

// Every exact-match probability is hypergeometric, including losing outcomes.
for(const N of [42,45,49,55,58]){
 const total=Engine.comb(N,6);assert.ok(Math.abs(Array.from({length:7},(_,k)=>Engine.comb(6,k)*Engine.comb(N-6,6-k)/total).reduce((a,b)=>a+b)-1)<1e-12);
}
assert.equal(Engine.comb(49,6),13983816);
const history=Array.from({length:28},(_,i)=>({game:'super',date:new Date(Date.UTC(2026,0,i+1)).toISOString().slice(0,10),numbers:[1,2,3,4,5,6]}));
const audit=Engine.analyze(history,'super',config,new Set());
assert.ok(audit.p!==null&&audit.p<=.01,'extreme repeated draws detected');
const altered=history.map(d=>({...d,numbers:d.numbers.slice()}));altered[27].numbers=[40,41,42,43,44,45];
const changed=Engine.analyze(altered,'super',config,new Set());
assert.deepEqual(audit.bt.strategies.map(s=>s.trace.at(-1).line),changed.bt.strategies.map(s=>s.trace.at(-1).line),'held-out result must not change the line tested against it');
assert.notEqual(audit.seed,changed.seed,'corrected numbers invalidate suggestions');
const messy=Engine.analyze([...history,history[0],{game:'super',date:'2026-02-30',numbers:[1,2,3,4,5,6]}],'super',config,new Set());
assert.equal(messy.n,28);assert.equal(messy.quality.duplicates,1);assert.equal(messy.quality.invalid,1);
const repriced=structuredClone(config);repriced.prizeEst.super[3]=999;
assert.deepEqual(Engine.analyze(history,'super',repriced,new Set()).picks,audit.picks,'prize edits should not change selections');
// Slip identity is order independent; expired entries cannot migrate to a new draw.
vm.runInContext(`
if(ticketId('super',123,[6,5,4,3,2,1])!==ticketId('super',123,[1,2,3,4,5,6]))throw Error('duplicate identity');
SLIP=[{game:'super',draw:1,numbers:[1,2,3,4,5,6]}];
if(activeSlip().length)throw Error('expired slip included');
`,ctx);
console.log('Passed: portfolio diversity, exact odds, audit calibration, holdout isolation, input cleanup, cache invalidation and slip expiry.');

(async()=>{
const memory=new Map(),clipboard=[];
const localStorage={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v)};
const build=()=>{const context={...ctx,localStorage,navigator:{clipboard:{writeText:async t=>clipboard.push(t)}}};vm.createContext(context);vm.runInContext(fs.readFileSync('tickets.js','utf8'),context);vm.runInContext(script,context);vm.runInContext(`C=${JSON.stringify(config)};R=[];EM={};P=new Set(C.personal);view='mynumbers';game='all';render();`,context);return context};
const first=build();
await vm.runInContext(`ticketAction('toggle',[...TICKETS.keys()][0])`,first);
assert.equal(JSON.parse(memory.get('lotto-slip-v1')).length,1);
assert.ok(app.innerHTML.includes('1 line · PHP 25'));
const second=build();assert.equal(vm.runInContext('activeSlip().length',second),1,'slip survives reload');
await vm.runInContext(`ticketAction('copy')`,second);
assert.ok(clipboard[0].includes('Total PHP 25'));assert.ok(/2026/.test(clipboard[0]));
assert.ok(clipboard[0].includes('ordinary line'));
await vm.runInContext(`ticketAction('remove',ticketId(SLIP[0].game,SLIP[0].draw,SLIP[0].numbers))`,second);
assert.equal(vm.runInContext('activeSlip().length',second),0);
assert.ok(app.innerHTML.includes('0 lines · PHP 0'));
console.log('Passed: slip selection, cost totals, storage reload, copy with draw identity and removal.');
})().catch(e=>{console.error(e);process.exitCode=1});
