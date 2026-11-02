const assert=require('node:assert/strict');
require('./engine.js');require('./feed.js');
(async()=>{
const data={draws:[{game:'super',date:'2026-11-01',numbers:[1,2,3,4,5,6]}]};
assert.ok(FeedNetwork.validResults(data));
assert.ok(!FeedNetwork.validResults({draws:[{...data.draws[0],numbers:[1,1,2,3,4,5]}]}));
assert.ok(!FeedNetwork.validResults({draws:[{...data.draws[0],date:'2026-02-30'}]}));
let calls=[];
const fetcher=async url=>{calls.push(url);return url==='live'?{ok:false,status:503}:{ok:true,json:async()=>data}};
assert.deepEqual(await FeedNetwork.loadJSON('live','local',{fetcher,validate:FeedNetwork.validResults}),data);
assert.deepEqual(calls,['live','local']);assert.match(FeedNetwork.notice,/fallback/);
await FeedNetwork.loadJSON('settings',null,{fetcher,trackNotice:false});assert.match(FeedNetwork.notice,/fallback/);
await assert.rejects(FeedNetwork.readJSON('hang',{timeout:10,fetcher:()=>new Promise(()=>{})}),/timed out/);
await assert.rejects(FeedNetwork.loadJSON('bad',null,{fetcher:async()=>({ok:true,json:async()=>({draws:'broken'})}),validate:FeedNetwork.validResults}),/Invalid data/);
assert.deepEqual(data.draws[0].numbers,[1,2,3,4,5,6]);
console.log('Passed: bounded timeout, live-to-local fallback, validation and retained fallback notice.');
})().catch(e=>{console.error(e);process.exitCode=1});
