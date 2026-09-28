'use strict';
const {words,pairs,source}=require('./content.cjs');
const BY_ID=new Map(words.map(w=>[w.id,w]));
const TOTAL_TURNS=12;
function rng(seed){let s=seed>>>0;return()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
function shuffled(list,random){const a=[...list];for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function score(game){return [0,1].map(p=>{const tiles=game.board.filter(t=>t.owner===p).length;let lines=0;for(let n=0;n<4;n++){if([0,1,2,3].every(k=>game.board[n*4+k].owner===p))lines++;if([0,1,2,3].every(k=>game.board[k*4+n].owner===p))lines++;}return{tiles,lines,total:tiles+2*lines};});}
function buildMissions(g){
 const random=rng(g.seed+g.turn*7919), eligible=g.board.filter(t=>t.owner!==g.active);
 const single=shuffled(eligible,random).slice(0,3).map((t,i)=>{const w=BY_ID.get(t.id);return{id:`${g.turn}-s${i}`,kind:t.owner===null?'single':'rival',title:t.owner===null?'Precision move':'Take it back',count:1,clue:w.context,targets:[t.id]};});
 const links=shuffled(pairs.filter(p=>p.ids.every(id=>eligible.some(t=>t.id===id))),random);
 // Pair options use authored semantic links, never arbitrary automatically generated pairs.
 const result=single.slice(0,links.length?2:3);
 if(links.length){const p=links[0];result.push({id:`${g.turn}-link`,kind:'link',title:p.title,count:2,clue:p.clue,targets:[...p.ids]});}
 return result;
}
function createGame(seed,starter=0){
 if(!Number.isSafeInteger(seed)||![0,1].includes(starter))throw new Error('Invalid game setup');
 const g={seed:seed>>>0,starter,active:starter,turn:0,version:0,phase:'choose',board:shuffled(words,rng(seed)).map(w=>({id:w.id,owner:null})),missions:[],selected:null,feedback:null,moves:[0,0]};
 g.missions=buildMissions(g);return g;
}
function checkActor(g,actor){if(actor!==g.active)throw new Error('Not your turn');}
function apply(g,actor,action){
 if(!action||!Number.isInteger(action.version)||action.version!==g.version)throw new Error('Stale move; refresh the board');
 if(g.phase==='over')throw new Error('The game has finished');
 if(action.type==='continue'){
  if(g.phase!=='review')throw new Error('No result to continue from');
  checkActor(g,actor);
  g.feedback=null;g.selected=null;
  if(g.turn>=TOTAL_TURNS){g.phase='over';g.missions=[];}
  else{g.phase='choose';g.missions=buildMissions(g);}
 } else {
  checkActor(g,actor);
  if(action.type==='choose'){
   if(g.phase!=='choose')throw new Error('A mission is already locked');
   const m=g.missions.find(m=>m.id===action.missionId);if(!m)throw new Error('Unknown mission');
   g.selected=m.id;g.phase='answer';
  } else if(action.type==='answer'){
   if(g.phase!=='answer')throw new Error('Choose a mission first');
   const m=g.missions.find(m=>m.id===g.selected), ids=action.ids;
   if(!Array.isArray(ids)||ids.length!==m.count||new Set(ids).size!==ids.length||ids.some(id=>!g.board.some(t=>t.id===id&&t.owner!==actor)))throw new Error('Select the required number of available words');
   const ok=ids.every(id=>m.targets.includes(id)),captured=[],stolen=[];
   if(ok)for(const id of ids){const t=g.board.find(t=>t.id===id);if(t.owner!==null)stolen.push(id);t.owner=actor;captured.push(id);}
   g.feedback={actor,ok,chosen:[...ids],correct:[...m.targets],captured,stolen,clue:m.clue,title:m.title};
   g.moves[actor]++;g.turn++;g.active=1-actor;g.phase='review';
  } else if(action.type==='pass'){
   if(!['choose','answer'].includes(g.phase))throw new Error('Cannot pass now');
   g.feedback={actor,ok:false,passed:true,chosen:[],correct:[],captured:[],stolen:[]};
   g.moves[actor]++;g.turn++;g.active=1-actor;g.phase='review';
  } else throw new Error('Unknown action');
 }
 g.version++;return g;
}
function publicState(g){
 const scores=score(g), max=Math.max(...scores.map(s=>s.total));
 const feedback=g.feedback?{...g.feedback,words:g.feedback.correct.map(id=>{const {context,...w}=BY_ID.get(id);return w;})}:null;
 return{version:g.version,phase:g.phase,active:g.active,starter:g.starter,turn:g.turn,totalTurns:TOTAL_TURNS,moves:[...g.moves],scores,
  board:g.board.map(t=>({id:t.id,en:BY_ID.get(t.id).en,pos:BY_ID.get(t.id).pos,owner:t.owner})),
  missions:g.missions.map(({targets,...m})=>m),selected:g.selected,feedback,
  winners:g.phase==='over'?scores.map((s,i)=>s.total===max?i:null).filter(i=>i!==null):[],
  review:g.phase==='over'?words.map(({context,...w})=>w):[],source:{repository:source.repository,commit:source.commit}};
}
module.exports={createGame,apply,publicState,score,buildMissions,TOTAL_TURNS};
