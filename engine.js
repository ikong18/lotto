/* Analysis engine: pure mathematics. Nothing here can raise the odds of any ticket; it measures, tests and ranks. */
(function(){
const erf=x=>{const s=Math.sign(x);x=Math.abs(x);const t=1/(1+.3275911*x);return s*(1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-.284496736)*t+.254829592)*t*Math.exp(-x*x))};
const Phi=z=>.5*(1+erf(z/Math.SQRT2)),comb=(n,k)=>{let r=1;for(let i=1;i<=k;i++)r=r*(n-k+i)/i;return r};
const NN={ultra:58,super:49};
const rng=s=>()=>{s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
const hash=s=>{let h=2166136261;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0};
function typical(c,N){const s=c.reduce((a,b)=>a+b,0),z=(s-3*(N+1))/Math.sqrt(6*(N+1)*(N-6)/12),odd=c.filter(x=>x%2).length,bands=new Set(c.map(x=>Math.ceil(x/(N/5)))).size,cons=c.some((x,i)=>i&&x-c[i-1]===1);
return{t:Math.exp(-z*z/2)*comb(6,odd)/20*Math.min(1,bands/4)*(cons?.85:1),sum:s,odd}}
function analyze(ds,g,C,P){
const N=NN[g],n=ds.length,pr=6/N,E=n*pr,cnt=Array(N+1).fill(0);ds.forEach(d=>d.numbers.forEach(x=>cnt[x]++));
let chi=0;for(let i=1;i<=N;i++)chi+=(cnt[i]-E)**2/E;
const df=N-1,p=1-Phi((Math.cbrt(chi/df)-(1-2/(9*df)))/Math.sqrt(2/(9*df))),sd=Math.sqrt(n*pr*(1-pr));
const zs=[...Array(N)].map((_,i)=>({n:i+1,c:cnt[i+1],z:(cnt[i+1]-E)/sd})).sort((a,b)=>b.z-a.z);
const tot=comb(N,6),pz=C.prizeEst[g],odds=[3,4,5,6].map(k=>({k,p:comb(6,k)*comb(N-6,6-k)/tot,prize:pz[k]||0}));
const ev=odds.filter(o=>o.k<6).reduce((a,o)=>a+o.p*o.prize,0),evJ=ev+odds[3].p*odds[3].prize;
let bt=null;if(n>8){let sum=0,m=0;for(let t=8;t<n;t++){const c=Array(N+1).fill(0);ds.slice(0,t).forEach(d=>d.numbers.forEach(x=>c[x]++));
const pick=[...Array(N)].map((_,i)=>i+1).sort((a,b)=>c[b]-c[a]||a-b).slice(0,6);sum+=pick.filter(x=>ds[t].numbers.includes(x)).length;m++}
const mean=sum/m,base=36/N,se=Math.sqrt(6*pr*(1-pr)*(N-6)/(N-1)/m);bt={mean,base,z:(mean-base)/se,n:m}}
const post=i=>(cnt[i]+pr*40)/(n+40),rnd=rng(hash(g+(n?ds[n-1].date:''))),R=()=>1+Math.floor(rnd()*N);
const score=c=>{c=c.slice().sort((a,b)=>a-b);const t=typical(c,N),pc=c.filter(x=>P.has(x)).length,low=c.filter(x=>x<=31).length,fi=c.reduce((a,x)=>a+post(x),0)/6/pr;
return{c,v:t.t*(1-.08*Math.max(0,low-3))*(pc>=2&&pc<=3?1:.2)*(1+.05*(fi-1)),t:t.t,sum:t.sum,odd:t.odd,pc}};
const found={};for(let r=0;r<60;r++){let c=[];while(c.length<6){const x=R();if(!c.includes(x))c.push(x)}let cur=score(c),best=cur;
for(let i=0;i<500;i++){const nc=cur.c.slice();nc[Math.floor(rnd()*6)]=R();if(new Set(nc).size<6)continue;const s=score(nc);if(s.v>cur.v||rnd()<.02)cur=s;if(cur.v>best.v)best=cur}found[best.c.join()]=best}
const picks=Object.values(found).sort((a,b)=>b.v-a.v).slice(0,5);
return{n,chi,df,p,flags:zs.filter(a=>Math.abs(a.z)>2).length,expFlags:N*.0455,top:zs.slice(0,3),bot:zs.slice(-3).reverse(),odds,ev,evJ,bt,picks}}
globalThis.Engine={analyze}})();
