'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {makeServer}=require('../server.cjs');
test('public mode requires canonical HTTPS origin',()=>{assert.throws(()=>makeServer({production:true}));for(const u of ['http://example.test','https://example.test/path'])assert.throws(()=>makeServer({production:true,publicOrigin:u}));});
test('health endpoint exposes no room data',async t=>{const x=makeServer();await new Promise(r=>x.server.listen(0,'127.0.0.1',r));t.after(()=>new Promise(r=>{x.server.closeAllConnections();x.server.close(r)}));const res=await fetch('http://127.0.0.1:'+x.server.address().port+'/health');const j=await res.json();assert.equal(j.ok,true);assert.equal(j.mode,'battle-room');assert.ok(Array.isArray(j.datasets));assert.ok(j.datasets.includes('band3'));assert.ok(j.datasets.includes('band2-core1'));assert.equal(j.rooms,undefined);});
