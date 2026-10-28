/* Lotto Engine v2. Selection preferences and retrospective analysis, never predictions. */
(function(){
'use strict';
const NN={ultra:58,grand:55,super:49,mega:45,lotto:42};
const DAYS={ultra:[0,2,5],grand:[1,3,6],super:[0,2,4],mega:[1,3,5],lotto:[2,4,6]};
const cache=new Map();
const comb=(n,k)=>{if(k<0||k>n)return 0;let r=1;for(let i=1;i<=k;i++)r=r*(n-k+i)/i;return r};
const rng=s=>()=>{s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
const hash=s=>{let h=2166136261;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0};
function sample(N,rnd){const pool=Array.from({length:N},(_,i)=>i+1);for(let i=0;i<6;i++){const j=i+Math.floor(rnd()*(N-i));[pool[i],pool[j]]=[pool[j],pool[i]]}return pool.slice(0,6).sort((a,b)=>a-b)}
const overlap=(a,b)=>a.filter(n=>b.includes(n)).length;
const key=c=>c.slice().sort((a,b)=>a-b).join(',');
const validLine=(c,N)=>Array.isArray(c)&&c.length===6&&new Set(c).size===6&&c.every(n=>Number.isInteger(n)&&n>=1&&n<=N);
function clean(ds,g){const seen=new Map();let invalid=0,duplicates=0;
for(const d of ds){if(d.game!==g||!validLine(d.numbers,NN[g])||!/^\d{4}-\d{2}-\d{2}$/.test(d.date)||!Number.isFinite(Date.parse(d.date))||new Date(d.date).toISOString().slice(0,10)!==d.date){invalid++;continue}
if(seen.has(d.date)){duplicates++;continue}seen.set(d.date,{...d,numbers:d.numbers.slice().sort((a,b)=>a-b)})}
return{ds:[...seen.values()].sort((a,b)=>a.date.localeCompare(b.date)),invalid,duplicates}}
function describe(c,N,P){const sum=c.reduce((a,b)=>a+b,0),odd=c.filter(x=>x%2).length,spread=c[5]-c[0],pc=c.filter(x=>P.has(x)).length;
const z=(sum-3*(N+1))/Math.sqrt(6*(N+1)*(N-6)/12),t=Math.exp(-z*z/2)*(odd>=2&&odd<=4?1:.6)*Math.min(1,spread/(N*.6));
return{c:c.slice(),sum,odd,spread,pc,t,v:t}}
function backtest(ds,N){const warmup=20;if(ds.length<=warmup)return null;
const strategies=['frequency','recent','cold'].map(id=>({id,total:0,hits:0,best:0,trace:[]}));
const counts=Array(N+1).fill(0);ds.slice(0,warmup).forEach(d=>d.numbers.forEach(x=>counts[x]++));
for(let t=warmup;t<ds.length;t++){
 const recent=Array(N+1).fill(0);ds.slice(Math.max(0,t-10),t).forEach(d=>d.numbers.forEach(x=>recent[x]++));
 for(const s of strategies){const c=s.id==='recent'?recent:counts;
 const line=Array.from({length:N},(_,i)=>i+1).sort((a,b)=>(s.id==='cold'?c[a]-c[b]:c[b]-c[a])||a-b).slice(0,6);
 const matches=overlap(line,ds[t].numbers);s.total+=matches;s.hits+=matches>=3;s.best=Math.max(s.best,matches);s.trace.push({date:ds[t].date,line:line.slice().sort((a,b)=>a-b),matches})}
 ds[t].numbers.forEach(x=>counts[x]++);
}
const n=ds.length-warmup,base=36/N,se=Math.sqrt(6*(6/N)*(1-6/N)*(N-6)/(N-1)/n);
for(const s of strategies){s.mean=s.total/n;s.z=(s.mean-base)/se}
return{n,base,mean:strategies[0].mean,z:strategies[0].z,strategies,warmup}}
function analyze(raw,g,C,P=new Set()){
const N=NN[g];if(!N)throw new Error('Unknown lotto game');
const cleaned=clean(raw,g),ds=cleaned.ds,personal=[...P].filter(x=>Number.isInteger(x)&&x>0&&x<=N).sort((a,b)=>a-b);
P=new Set(personal);const saved=(C.sets?.[g]||[]).filter(c=>validLine(c,N)),pz=C.prizeEst?.[g]||{};
const signature=JSON.stringify([g,ds.map(d=>[d.date,d.numbers,d.jackpot,d.winners]),personal,saved,pz,cleaned.invalid,cleaned.duplicates]);
if(cache.has(signature))return cache.get(signature);
const seed=hash(JSON.stringify([g,ds.map(d=>[d.date,d.numbers]),personal,saved])),rnd=rng(seed),n=ds.length,pr=6/N,E=n*pr,cnt=Array(N+1).fill(0);
ds.forEach(d=>d.numbers.forEach(x=>cnt[x]++));
const chiOf=c=>E?c.slice(1).reduce((a,x)=>a+(x-E)**2/E,0):0,chi=chiOf(cnt),sd=Math.sqrt(n*pr*(1-pr));
// Simulate draws without replacement. Sparse counts and within-draw dependence are retained.
let p=null;const simulations=199;if(n>=20){let extreme=0;const sim=rng(hash('audit'+g+JSON.stringify(ds.map(d=>[d.date,d.numbers]))));
for(let r=0;r<simulations;r++){const c=Array(N+1).fill(0);for(let i=0;i<n;i++)sample(N,sim).forEach(x=>c[x]++);if(chiOf(c)>=chi-1e-9)extreme++}p=(extreme+1)/(simulations+1)}
const zs=Array.from({length:N},(_,i)=>({n:i+1,c:cnt[i+1],z:sd?(cnt[i+1]-E)/sd:0})).sort((a,b)=>b.z-a.z||a.n-b.n);
const latest=ds.at(-1),total=comb(N,6),jackpot=latest?.jackpot??pz[6]??0;
const odds=[3,4,5,6].map(k=>({k,p:comb(6,k)*comb(N-6,6-k)/total,prize:k===6?jackpot:pz[k]||0}));
const ev=odds.filter(o=>o.k<6).reduce((a,o)=>a+o.p*o.prize,0),evJ=ev+odds[3].p*jackpot;
// Start with uniform samples, then diversify the portfolio. No frequency weighting or win scores.
const candidates=new Map(),excluded=new Set(saved.map(key));
for(let i=0;i<1600;i++){const c=sample(N,rnd),k=key(c);if(!excluded.has(k))candidates.set(k,describe(c,N,P))}
const pool=[...candidates.values()],picks=[];
const labels=['Personal mix','Balanced spread','Spread option 3','Spread option 4','Spread option 5'];
while(picks.length<5){let best=null,bestScore=-Infinity;
 for(const candidate of pool){if(picks.includes(candidate)||picks.some(p=>overlap(p.c,candidate.c)>2))continue;
 const used=new Set(picks.flatMap(p=>p.c)),fresh=candidate.c.filter(x=>!used.has(x)).length;
 const preference=picks.length===0&&personal.length>=2?(candidate.pc>=2&&candidate.pc<=3?1:0):0;
 const score=candidate.t+fresh*.45+preference*2;
 if(score>bestScore){best=candidate;bestScore=score}}
 if(!best)break;best.label=picks.length===0&&personal.length<2?'Balanced starter':labels[picks.length];picks.push(best)
}
const distinct=new Set(picks.flatMap(x=>x.c)).size,maxOverlap=Math.max(0,...picks.flatMap((p,i)=>picks.slice(i+1).map(q=>overlap(p.c,q.c))));
let expected=0;if(n){for(let t=Date.parse(ds[0].date);t<=Date.parse(latest.date);t+=86400000)if(DAYS[g].includes(new Date(t).getUTCDay()))expected++}
const result={n,chi,df:N-1,p,simulations:p===null?0:simulations,flags:zs.filter(a=>Math.abs(a.z)>2).length,expFlags:N*.0455,top:zs.slice(0,3),bot:zs.slice(-3).reverse(),odds,ev,evJ,bt:backtest(ds,N),picks,distinct,maxOverlap,
 quality:{invalid:cleaned.invalid,duplicates:cleaned.duplicates,expected,missing:Math.max(0,expected-n),first:ds[0]?.date,last:latest?.date},seed};
if(cache.size>=64)cache.delete(cache.keys().next().value);cache.set(signature,result);return result
}
globalThis.Engine={analyze,comb,validLine,overlap,version:'2.0'};
})();
