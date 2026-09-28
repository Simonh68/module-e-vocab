'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),http=require('node:http');
const {makeServer}=require('../server.cjs');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function setup(){const {server,rooms,clean}=makeServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;const streams=[];
 async function api(url,body,cookie='',extra={}){const r=await fetch(base+url,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{}),...extra},...(body===undefined?{}:{body:JSON.stringify(body)})});return{status:r.status,cookie:r.headers.get('set-cookie')?.split(';')[0],body:await r.json()};}
 async function events(code,cookie){return await new Promise((resolve,reject)=>{const q=http.get(base+`/events?room=${code}`,{headers:{Cookie:cookie}},r=>{r.once('data',()=>resolve({request:q,response:r}));r.on('data',()=>{});streams.push(r);});q.on('error',reject);streams.push(q);});}
 async function close(){for(const s of streams)s.destroy();server.closeAllConnections();await new Promise(r=>server.close(r));}
 return{server,rooms,clean,base,api,events,close};}
test('two independent sessions, server authority, privacy, reconnect and expiry',async t=>{
 const s=await setup();t.after(()=>s.close());
 const host=await s.api('/api/create',{});assert.equal(host.status,201);const code=host.body.code,c0=host.cookie;
 assert.match(code,/^[0-9A-F]{12}$/);assert.ok(c0);assert.ok(!JSON.stringify(host.body).includes('token'));
 assert.equal((await s.api('/api/state?room='+code)).status,403);
 const guest=await s.api('/api/join',{code}),c1=guest.cookie;assert.equal(guest.body.you,1);
 assert.equal((await s.api('/api/join',{code})).status,409);
 await s.events(code,c0);await s.events(code,c1);
 await pause(100);let start=await s.api('/api/action?room='+code,{type:'start'},c0);assert.equal(start.status,200);
 assert.equal(start.body.game.board.length,16);assert.ok(start.body.game.missions.every(m=>!m.targets));
 const r=s.rooms.get(code),actor=r.game.active,ca=actor===0?c0:c1,cb=actor===0?c1:c0;
 await pause(100);assert.equal((await s.api('/api/action?room='+code,{type:'pass',version:r.game.version,matchId:r.matchId},cb)).status,400);
 const m=r.game.missions[0];await pause(100);
 assert.equal((await s.api('/api/action?room='+code,{type:'choose',missionId:m.id,version:r.game.version,matchId:r.matchId},ca)).status,200);
 await pause(100);const version=r.game.version;
 const ans=await s.api('/api/action?room='+code,{type:'answer',ids:m.targets,version,matchId:r.matchId},ca);assert.equal(ans.status,200);assert.equal(ans.body.game.feedback.ok,true);
 await pause(100);assert.equal((await s.api('/api/action?room='+code,{type:'answer',ids:m.targets,version,matchId:r.matchId},ca)).status,400);
 assert.equal((await s.api('/api/state?room='+code,undefined,ca)).body.game.turn,1);
 const reconnect=await s.api('/api/join',{code},ca);assert.equal(reconnect.body.you,actor);assert.equal(reconnect.body.game.turn,1);
 assert.equal((await s.api('/api/action?room='+code,{type:'pass'},ca,{Origin:'https://other.example'})).status,403);
 r.created=Date.now()-2*60*60*1000-1;s.clean();assert.equal(s.rooms.size,0);
 assert.equal((await s.api('/api/state?room='+code,undefined,c0)).status,404);
});
test('malformed room, unavailable source code and unauthenticated start',async t=>{const s=await setup();t.after(()=>s.close());assert.equal((await s.api('/api/join',{code:'123'})).status,400);assert.equal((await s.api('/core.cjs')).status,404);assert.equal((await s.api('/api/action?room=12345678',{type:'start'})).status,404);});

test('complete online match, disconnection pause, rematch consent and stale-match rejection',async t=>{
 const s=await setup();t.after(()=>s.close());
 const host=await s.api('/api/create',{}),code=host.body.code;
 const guest=await s.api('/api/join',{code}),cookies=[host.cookie,guest.cookie];
 const connections=[await s.events(code,cookies[0]),await s.events(code,cookies[1])];
 const path='/api/action?room='+code;
 assert.equal((await s.api(path,{type:'start'},cookies[0])).status,200);
 const room=s.rooms.get(code),firstMatch=room.matchId,firstStarter=room.starter;
 async function action(player,payload){await pause(90);return s.api(path,{...payload,version:room.game.version,matchId:room.matchId},cookies[player]);}
 connections[1].response.destroy();connections[1].request.destroy();await pause(60);
 assert.equal((await action(room.game.active,{type:'pass'})).status,409);
 assert.equal(room.game.turn,0);
 connections[1]=await s.events(code,cookies[1]);
 while(room.game.phase!=='over'){
  const actor=room.game.active;
  if(room.game.phase==='review'){
   assert.equal((await action(actor,{type:'continue'})).status,200);
  }else{
   const mission=room.game.missions.find(m=>m.count===2)||room.game.missions[0];
   assert.equal((await action(actor,{type:'choose',missionId:mission.id})).status,200);
   assert.equal((await action(actor,{type:'answer',ids:mission.targets})).status,200);
  }
 }
 assert.deepEqual(room.game.moves,[6,6]);
 assert.equal((await action(0,{type:'rematch'})).status,200);
 assert.equal(room.game.phase,'over');assert.equal(room.matchId,firstMatch);
 assert.equal((await action(1,{type:'rematch'})).status,200);
 assert.notEqual(room.matchId,firstMatch);assert.equal(room.game.starter,1-firstStarter);
 assert.equal(room.game.turn,0);
 await pause(90);
 assert.equal((await s.api(path,{type:'pass',version:0,matchId:firstMatch},cookies[room.game.active])).status,409);
 assert.equal(room.game.turn,0);
});
