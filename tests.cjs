const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
require('./engine.js');
const config=JSON.parse(fs.readFileSync('sets.json'));
for(const [g,max] of Object.entries({ultra:58,grand:55,super:49,mega:45,lotto:42})){
  for(const draws of [[],JSON.parse(fs.readFileSync('results.json')).draws.filter(d=>d.game===g)]){
    const a=Engine.analyze(draws,g,config,new Set(config.personal));
    assert.ok(Number.isFinite(a.chi));
    assert.ok(a.p===null||(a.p>=0&&a.p<=1));
    assert.ok(a.picks.length>0);
    for(const p of a.picks){assert.equal(new Set(p.c).size,6);assert.ok(p.c.every(n=>Number.isInteger(n)&&n>=1&&n<=max));}
    assert.deepEqual(a.picks,Engine.analyze(draws,g,config,new Set(config.personal)).picks);
  }
}
const html=fs.readFileSync('index.html','utf8');
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
new vm.Script(script);
const app={innerHTML:''};
const ctx={Engine,location:{hostname:"localhost",pathname:"/"},console,Date,Set,Math,JSON,Number,String,Array,Object,Promise,URL,window:{},document:{querySelector:()=>app,querySelectorAll:()=>[],addEventListener:()=>{}},fetch:()=>new Promise(()=>{}),addEventListener:()=>{},setInterval:()=>{},matchMedia:()=>({matches:true}),localStorage:{},requestAnimationFrame:()=>{}};
vm.createContext(ctx);vm.runInContext(script,ctx);
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
