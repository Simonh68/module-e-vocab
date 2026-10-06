'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {makeServer}=require('../server.cjs');
const sets={
 band3:{id:'band3',label:'Band III',source:{test:true},items:['aid','total','concept','damage','rapid'].map((w,i)=>({id:'b3'+i,word:w,pos:'Word',meaning:'meaning '+i,example:w+' appears here.'}))},
 'band2-core1':{id:'band2-core1',label:'Band II Core I',source:{test:true},items:['lift','remove','weekly','mosque','petrol'].map((w,i)=>({id:'b2'+i,word:w,pos:'Word',meaning:'',example:'We use '+w+' here.'}))}
};
function mockProvider(){return{list:()=>Object.values(sets).map(x=>({id:x.id,label:x.label})),load:async id=>{if(!sets[id])throw new Error('Unknown vocabulary dataset');return sets[id]}}}
async function setup(){const x=makeServer({vocabProvider:mockProvider()});await new Promise(r=>x.server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+x.server.address().port;async function api(path,body,cookie=''){const r=await fetch(base+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{})},body:body===undefined?undefined:JSON.stringify(body)});return{status:r.status,cookie:r.headers.get('set-cookie')?.split(';')[0],body:await r.json()}}return{...x,api,close:()=>new Promise(r=>{x.server.closeAllConnections();x.server.close(r)})};}
test('room creation chooses a dataset without changing room mechanics',async t=>{const s=await setup();t.after(()=>s.close());const a=await s.api('/api/create',{datasetId:'band3'}),b=await s.api('/api/create',{datasetId:'band2-core1'});assert.equal(a.status,201);assert.equal(b.status,201);assert.equal(a.body.dataset.id,'band3');assert.equal(b.body.dataset.id,'band2-core1');});
test('default remains Band III for backward compatibility',async t=>{const s=await setup();t.after(()=>s.close());const a=await s.api('/api/create',{});assert.equal(a.body.dataset.id,'band3');});
test('unknown datasets fail without creating a room',async t=>{const s=await setup();t.after(()=>s.close());const a=await s.api('/api/create',{datasetId:'nope'});assert.equal(a.status,400);assert.equal(s.rooms.size,0);});
test('personal-data fields remain rejected',async t=>{const s=await setup();t.after(()=>s.close());assert.equal((await s.api('/api/create',{name:'student'})).status,400);});
