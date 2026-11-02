/* Bounded data requests; a failed response never replaces a working results snapshot. */
(function(){
const FeedNetwork={notice:''};
async function readJSON(url,{timeout=8000,fetcher=fetch}={}){
 const controller=new AbortController();let timer;
 try{return await Promise.race([
  fetcher(url,{signal:controller.signal,cache:'no-store'}).then(async r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}),
  new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Request timed out'))},timeout)})
 ])}finally{clearTimeout(timer)}
}
async function response(url,options={},timeout=8000){const controller=new AbortController();let timer;
 try{return await Promise.race([fetch(url,{...options,signal:controller.signal}),new Promise((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('Request timed out'))},timeout)})])}finally{clearTimeout(timer)}
}
function validResults(data){const max={ultra:58,grand:55,super:49,mega:45,lotto:42};
 return data&&Array.isArray(data.draws)&&data.draws.every(d=>d&&max[d.game]&&/^\d{4}-\d{2}-\d{2}$/.test(d.date)&&Number.isFinite(Date.parse(d.date))&&new Date(d.date).toISOString().slice(0,10)===d.date&&Engine.validLine(d.numbers,max[d.game])&&(d.jackpot==null||(Number.isFinite(d.jackpot)&&d.jackpot>=0))&&(d.winners==null||(Number.isInteger(d.winners)&&d.winners>=0)));
}
async function loadJSON(primary,fallback,{validate=()=>true,trackNotice=true,...options}={}){
 let failure;
 for(const [i,url] of [...new Set([primary,fallback].filter(Boolean))].entries()){
  try{const data=await readJSON(url,options);if(!validate(data))throw Error('Invalid data');if(trackNotice)FeedNetwork.notice=i?'Showing the deployed fallback because the live repository feed could not be reached.':'';return data}catch(e){failure=e}
 }
 throw failure||Error('No feed available');
}
globalThis.FeedNetwork=Object.assign(FeedNetwork,{readJSON,loadJSON,validResults,response});
})();
