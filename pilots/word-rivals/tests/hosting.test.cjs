'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {makeServer}=require('../server.cjs');
const {createPolicy}=require('../hosting.cjs');
test('public mode requires canonical HTTPS origin',()=>{assert.throws(()=>makeServer({production:true}));for(const u of ['http://example.test','https://example.test/path'])assert.throws(()=>makeServer({production:true,publicOrigin:u}));});
test('health endpoint exposes no room data',async t=>{const x=makeServer();await new Promise(r=>x.server.listen(0,'127.0.0.1',r));t.after(()=>new Promise(r=>{x.server.closeAllConnections();x.server.close(r)}));const res=await fetch('http://127.0.0.1:'+x.server.address().port+'/health');const j=await res.json();assert.equal(j.ok,true);assert.equal(j.mode,'battle-room');assert.ok(Array.isArray(j.datasets));assert.ok(j.datasets.includes('band3'));assert.ok(j.datasets.includes('band2-core1'));assert.equal(j.rooms,undefined);});

test('production POST accepts same-origin Fetch Metadata even with proxy-altered Origin',()=>{
 const policy=createPolicy({production:true,publicOrigin:'https://example.test'});
 const res={headers:{},setHeader(k,v){this.headers[k]=v},writeHead(s){this.status=s},end(x){this.body=x}};
 const req={method:'POST',url:'/api/create',headers:{host:'example.test',origin:'https://proxy.invalid','sec-fetch-site':'same-origin','content-length':'2'}};
 assert.equal(policy.guard(req,res),true);
});
test('production POST still rejects cross-site requests',()=>{
 const policy=createPolicy({production:true,publicOrigin:'https://example.test'});
 const res={headers:{},setHeader(k,v){this.headers[k]=v},writeHead(s){this.status=s},end(x){this.body=x}};
 const req={method:'POST',url:'/api/create',headers:{host:'example.test',origin:'https://evil.invalid','sec-fetch-site':'cross-site','content-length':'2'}};
 assert.equal(policy.guard(req,res),false);assert.equal(res.status,403);
});
