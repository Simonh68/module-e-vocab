'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const core=require('../core.cjs'),content=require('../content.cjs');
const action=(g,a)=>core.apply(g,g.active,{...a,version:g.version});
test('16 distinct, source-traceable Band III records; no invented difficulty levels',()=>{
 assert.equal(content.words.length,16);assert.equal(new Set(content.words.map(w=>w.id)).size,16);
 for(const w of content.words){assert.match(w.id,/^A[123]-\d{3}$/);assert.ok(w.definition&&w.example&&w.pos);assert.ok(w.sourceFile);}
 assert.equal(content.source.commit,'912053cc5030cd6be4a936e642f34775fd07fb67');
});
test('eight manually authored pairs cover every pilot word once',()=>{const ids=content.pairs.flatMap(p=>p.ids);assert.equal(ids.length,16);assert.equal(new Set(ids).size,16);assert.deepEqual([...ids].sort(),content.words.map(w=>w.id).sort());});
test('seeded layouts are reproducible, other seeds shuffle',()=>{assert.deepEqual(core.createGame(42),core.createGame(42));assert.notDeepEqual(core.createGame(42).board,core.createGame(43).board);});
test('online state does not expose seed, solutions, full corpus or tokens',()=>{
 const p=core.publicState(core.createGame(9));assert.equal(p.seed,undefined);assert.ok(p.missions.every(m=>!('targets'in m)));assert.ok(p.board.every(t=>!('definition'in t)));assert.equal(p.review.length,0);
});
test('the other player cannot act; no mutation on rejection',()=>{const g=core.createGame(3),before=JSON.stringify(g);assert.throws(()=>core.apply(g,1,{type:'pass',version:0}),/Not your turn/);assert.equal(JSON.stringify(g),before);});
test('stale and duplicate submissions cannot change the board',()=>{const g=core.createGame(3),v=g.version;action(g,{type:'choose',missionId:g.missions[0].id});assert.throws(()=>core.apply(g,0,{type:'pass',version:v}),/Stale/);});
test('one correct word is captured, turn changes, and source feedback is shown',()=>{
 const g=core.createGame(8),m=g.missions.find(m=>m.count===1);action(g,{type:'choose',missionId:m.id});action(g,{type:'answer',ids:m.targets});
 assert.equal(g.board.find(t=>t.id===m.targets[0]).owner,0);assert.equal(g.active,1);assert.equal(g.phase,'review');assert.equal(g.moves[0],1);assert.ok(core.publicState(g).feedback.words[0].example);
});
test('two correct linked words are captured together',()=>{const g=core.createGame(4),m=g.missions.find(m=>m.count===2);action(g,{type:'choose',missionId:m.id});action(g,{type:'answer',ids:m.targets});assert.equal(g.board.filter(t=>t.owner===0).length,2);});
test('a wrong linked answer captures neither word',()=>{const g=core.createGame(4),m=g.missions.find(m=>m.count===2);action(g,{type:'choose',missionId:m.id});const wrong=g.board.find(t=>!m.targets.includes(t.id)).id;action(g,{type:'answer',ids:[m.targets[0],wrong]});assert.equal(g.board.filter(t=>t.owner!==null).length,0);assert.equal(g.feedback.ok,false);});
test('duplicate or unknown word IDs are rejected without consuming a turn',()=>{const g=core.createGame(4),m=g.missions.find(m=>m.count===2);action(g,{type:'choose',missionId:m.id});assert.throws(()=>action(g,{type:'answer',ids:[m.targets[0],m.targets[0]]}));assert.throws(()=>action(g,{type:'answer',ids:['x','y']}));assert.equal(g.turn,0);});
test('missions lock on choice; no switching after seeing the board',()=>{const g=core.createGame(1);action(g,{type:'choose',missionId:g.missions[0].id});assert.throws(()=>action(g,{type:'choose',missionId:g.missions[1].id}),/already locked/);});
test('taking enemy territory removes its ownership, not just adding points',()=>{const g=core.createGame(3),id=g.missions[0].targets[0];g.board.find(t=>t.id===id).owner=1;action(g,{type:'choose',missionId:g.missions[0].id});action(g,{type:'answer',ids:[id]});assert.equal(g.board.find(t=>t.id===id).owner,0);assert.deepEqual(g.feedback.stolen,[id]);});
test('own territory is not eligible for selection',()=>{const g=core.createGame(3),m=g.missions[0];g.board.find(t=>t.id===m.targets[0]).owner=0;action(g,{type:'choose',missionId:m.id});assert.throws(()=>action(g,{type:'answer',ids:m.targets}));});
test('complete rows and columns each add two points; no diagonal bonus',()=>{const g=core.createGame(0);g.board.forEach((t,i)=>t.owner=i<4?0:null);assert.deepEqual(core.score(g)[0],{tiles:4,lines:1,total:6});g.board.forEach((t,i)=>t.owner=[0,5,10,15].includes(i)?0:null);assert.equal(core.score(g)[0].total,4);});
test('100 full games end with exactly six turns each and a valid result',()=>{
 for(let seed=0;seed<100;seed++){const g=core.createGame(seed,seed%2);while(g.phase!=='over'){
  if(g.phase==='review'){action(g,{type:'continue'});continue;}
  assert.ok(g.missions.length>0);for(const m of g.missions){assert.equal(m.targets.length,m.count);assert.ok(m.targets.every(id=>g.board.some(t=>t.id===id&&t.owner!==g.active)));}
  const m=g.missions[(seed+g.turn)%g.missions.length];action(g,{type:'choose',missionId:m.id});action(g,{type:'answer',ids:m.targets});
 }assert.deepEqual(g.moves,[6,6]);assert.equal(g.turn,12);assert.ok(core.publicState(g).winners.length);}
});
test('all passes produce an honest tie; completed games reject extra actions',()=>{const g=core.createGame(7);while(g.phase!=='over')action(g,{type:g.phase==='review'?'continue':'pass'});assert.deepEqual(core.publicState(g).winners,[0,1]);assert.throws(()=>action(g,{type:'pass'}),/finished/);});
