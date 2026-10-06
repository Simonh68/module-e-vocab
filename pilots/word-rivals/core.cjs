'use strict';
const {words,source}=require('./content.cjs');
const ROUNDS_PER_PLAYER=6;
function rng(seed){let s=seed>>>0;return()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
function shuffle(a,r){a=[...a];for(let i=a.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function makeQuestion(g){
 const r=rng(g.seed+g.turn*104729+17);
 const target=words[Math.floor(r()*words.length)];
 const pool=shuffle(words.filter(w=>w.id!==target.id&&w.definition.toLowerCase()!==target.definition.toLowerCase()),r).slice(0,3);
 const choices=shuffle([target,...pool],r).map(w=>({id:w.id,text:w.definition}));
 return {wordId:target.id,word:target.en,pos:target.pos,choices,correctId:target.id};
}
function createGame(seed,playerCount,starter=0){
 if(!Number.isSafeInteger(seed)||!Number.isInteger(playerCount)||playerCount<2||playerCount>6||starter<0||starter>=playerCount)throw new Error('Invalid game setup');
 const g={seed:seed>>>0,playerCount,starter,active:starter,turn:0,totalTurns:playerCount*ROUNDS_PER_PLAYER,version:0,phase:'playing',
 scores:Array(playerCount).fill(0),streaks:Array(playerCount).fill(0),correct:Array(playerCount).fill(0),answered:Array(playerCount).fill(0),feedback:null,question:null};
 g.question=makeQuestion(g);return g;
}
function leaders(g){const m=Math.max(...g.scores);return g.scores.map((s,i)=>s===m?i:null).filter(i=>i!==null);}
function apply(g,actor,a){
 if(!a||!Number.isInteger(a.version)||a.version!==g.version)throw new Error('Stale move; refresh');
 if(g.phase==='over')throw new Error('The game has finished');
 if(actor!==g.active)throw new Error('Not your turn');
 if(a.type!=='answer'||typeof a.choiceId!=='string')throw new Error('Invalid action');
 if(!g.question.choices.some(c=>c.id===a.choiceId))throw new Error('Unknown choice');
 const ok=a.choiceId===g.question.correctId;
 const power=(g.turn+1)%5===0;
 const beforeLeader=Math.max(...g.scores.filter((_,i)=>i!==actor));
 const comeback=g.scores[actor]+150<beforeLeader;
 if(ok){
   g.streaks[actor]++;
   g.correct[actor]++;
   let gain=100+Math.min(4,g.streaks[actor]-1)*25;
   if(power)gain*=2;
   if(comeback)gain+=50;
   g.scores[actor]+=gain;
   g.feedback={actor,ok:true,gain,power,comeback,streak:g.streaks[actor],answer:g.question.choices.find(c=>c.id===g.question.correctId).text,word:g.question.word};
 }else{
   g.streaks[actor]=0;
   g.feedback={actor,ok:false,gain:0,power,comeback:false,streak:0,answer:g.question.choices.find(c=>c.id===g.question.correctId).text,word:g.question.word};
 }
 g.answered[actor]++;g.turn++;
 if(g.turn>=g.totalTurns){g.phase='over';g.question=null;}
 else{g.active=(g.active+1)%g.playerCount;g.question=makeQuestion(g);}
 g.version++;return g;
}
function publicState(g){
 const q=g.question?{word:g.question.word,pos:g.question.pos,choices:g.question.choices.map(c=>({...c})),power:(g.turn+1)%5===0}:null;
 return {version:g.version,phase:g.phase,active:g.active,turn:g.turn,totalTurns:g.totalTurns,scores:[...g.scores],streaks:[...g.streaks],correct:[...g.correct],answered:[...g.answered],question:q,feedback:g.feedback?{...g.feedback}:null,winners:g.phase==='over'?leaders(g):[],source};
}
module.exports={createGame,apply,publicState,ROUNDS_PER_PLAYER};
