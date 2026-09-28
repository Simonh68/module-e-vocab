'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),http=require('node:http');
const {makeServer}=require('../server.cjs');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function setup(options={}){
 const {server,rooms,stop}=makeServer(options);await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base=`http://127.0.0.1:${server.address().port}`,connections=[];
 async function call(route,body,cookie='',headers={}){
  return new Promise((resolve,reject)=>{
   const bytes=body===undefined?null:Buffer.from(JSON.stringify(body));
   const req=http.request(new URL(route,base),{method:bytes===null?'GET':'POST',headers:{'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{}),...(bytes===null?{}:{'Content-Length':bytes.length}),...headers}},res=>{
    const chunks=[];res.on('data',chunk=>chunks.push(chunk));res.on('end',()=>{
     const txt=Buffer.concat(chunks).toString('utf8');let value;try{value=JSON.parse(txt);}catch{value=txt;}
     resolve({status:res.statusCode,headers:new Headers(res.headers),cookie:res.headers['set-cookie']?.[0]?.split(';')[0],body:value});
    });
   });req.on('error',reject);req.end(bytes);
  });
 }

 async function events(code,cookie){return new Promise((resolve,reject)=>{
  const q=http.get(base+`/events?room=${code}`,{headers:{Cookie:cookie}},res=>{let buffer='';connections.push(res);res.on('data',chunk=>{buffer+=chunk;});res.once('data',()=>resolve({q,res,text:()=>buffer}));});q.on('error',reject);connections.push(q);
 });}
 async function close(){for(const c of connections)c.destroy();server.closeAllConnections();await new Promise(r=>server.close(r));}
 return{server,rooms,base,call,events,close,stop};
}
test('public mode fails closed without a canonical HTTPS origin',()=>{
 assert.throws(()=>makeServer({production:true}),/required/);
 for(const url of ['http://example.test','https://example.test/path','https://user:pass@example.test','https://example.test/?x=1'])assert.throws(()=>makeServer({production:true,publicOrigin:url}));
});
test('HTTPS ingress uses secure HttpOnly cookie, exact Origin, and rejects spoofed host',async t=>{
 const s=await setup({production:true,publicOrigin:'https://example.test'});t.after(()=>s.close());
 const h={Host:'example.test',Origin:'https://example.test'};
 let r=await s.call('/api/create',{},'',h);assert.equal(r.status,201);assert.match(r.headers.get('set-cookie'),/; Secure/);assert.match(r.headers.get('set-cookie'),/HttpOnly; SameSite=Strict/);
 assert.match(r.body.code,/^[0-9A-F]{12}$/);
 assert.equal((await s.call('/api/create',{},'',{Host:'example.test'})).status,403);
 assert.equal((await s.call('/api/create',{},'',{...h,Origin:'https://evil.test','X-Forwarded-Host':'example.test'})).status,403);
 assert.equal((await s.call('/api/create',{},'',{...h,Host:'evil.test'})).status,403);
 assert.equal((await s.call('/api/create',{},'',{...h,'Sec-Fetch-Site':'cross-site'})).status,403);
 assert.equal((await s.call('/health')).status,200);
 assert.equal(s.rooms.size,1);
});
test('crawler exclusion and hashed script policy apply to pages and errors',async t=>{
 const s=await setup();t.after(()=>s.close());
 for(const route of ['/','/demo.html','/not-found']){
  const r=await s.call(route);assert.match(r.headers.get('x-robots-tag'),/noindex/);assert.equal(r.headers.get('referrer-policy'),'no-referrer');
  const script=r.headers.get('content-security-policy').split(';').find(x=>x.includes('script-src'));assert.ok(!script.includes('unsafe-inline'));assert.match(script,/sha256-/);
 }
 const robots=await s.call('/robots.txt');assert.equal(robots.status,200);assert.match(robots.body,/Disallow: \//);
});
test('invalid JSON shapes and personal-data fields are rejected without creating rooms',async t=>{
 const s=await setup();t.after(()=>s.close());
 for(const body of [null,[],7,{name:'not-a-real-student'},{email:'synthetic@example.invalid'}])assert.equal((await s.call('/api/create',body)).status,400);
 assert.equal((await s.call('/api/create',{padding:'x'.repeat(3000)})).status,413);
 assert.equal(s.rooms.size,0);
});
test('admission throttles are global and store no client identifier',async t=>{
 const s=await setup({createLimit:2,joinLimit:2});t.after(()=>s.close());
 assert.equal((await s.call('/api/create',{})).status,201);assert.equal((await s.call('/api/create',{})).status,201);assert.equal((await s.call('/api/create',{})).status,429);assert.equal(s.rooms.size,2);
 for(let i=0;i<2;i++)assert.equal((await s.call('/api/join',{code:'FFFFFFFFFFFF'})).status,404);
 assert.equal((await s.call('/api/join',{code:'FFFFFFFFFFFF'})).status,429);
});
test('room hard cap rejects new rooms while existing participants can still join',async t=>{
 const s=await setup({maxRooms:2});t.after(()=>s.close());const a=await s.call('/api/create',{});await s.call('/api/create',{});
 assert.equal((await s.call('/api/create',{})).status,503);assert.equal((await s.call('/api/join',{code:a.body.code})).status,200);
});
test('two simultaneous guests cannot take the same last player slot',async t=>{
 const s=await setup();t.after(()=>s.close());const h=await s.call('/api/create',{});
 const results=await Promise.all([s.call('/api/join',{code:h.body.code}),s.call('/api/join',{code:h.body.code})]);
 assert.deepEqual(results.map(r=>r.status).sort(),[200,409]);assert.equal(s.rooms.get(h.body.code).players.length,2);
});
test('10 concurrent rooms have independent players, turns and event streams',async t=>{
 const s=await setup();t.after(()=>s.close());
 const games=await Promise.all(Array.from({length:10},async()=>{
  const h=await s.call('/api/create',{}),code=h.body.code,g=await s.call('/api/join',{code});
  const links=[await s.events(code,h.cookie),await s.events(code,g.cookie)];
  const start=await s.call('/api/action?room='+code,{type:'start'},h.cookie);assert.equal(start.status,200);
  return{code,cookies:[h.cookie,g.cookie],links};
 }));
 await pause(100);
 for(let i=0;i<games.length;i++){
  const x=games[i],r=s.rooms.get(x.code);const other=games[(i+1)%games.length];
  assert.equal((await s.call('/api/state?room='+x.code,undefined,other.cookies[0])).status,403);
  const out=await s.call('/api/action?room='+x.code,{type:'pass',matchId:r.matchId,version:r.game.version},x.cookies[r.game.active]);assert.equal(out.status,200);
  assert.equal(out.body.game.turn,1);assert.ok(out.body.revision>0);
 }
 assert.equal(s.rooms.size,10);
 for(const x of games)for(const link of x.links){assert.ok(link.text().includes(x.code));for(const y of games)if(y.code!==x.code)assert.ok(!link.text().includes(y.code));}
});
