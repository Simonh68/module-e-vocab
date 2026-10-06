'use strict';
const ROUNDS_PER_PLAYER=6;
function rng(seed){let s=seed>>>0;return()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
function shuffle(a,r){a=[...a];for(let i=a.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function cloze(item){const i=item.example.toLowerCase().indexOf(item.word.toLowerCase());if(i<0)return null;return item.example.slice(0,i)+'_____'+item.example.slice(i+item.word.length);}
function makeQuestion(g){
 const items=g.dataset.items,r=rng(g.seed+g.turn*104729+17),target=items[Math.floor(r()*items.length)];
 let mode='meaning',prompt=target.word,pool=items.filter(x=>x.id!==target.id&&x.meaning&&x.meaning.toLowerCase()!==String(target.meaning||'').toLowerCase()),answer=target.meaning;
 if(!answer||pool.length<3){mode='cloze';prompt=cloze(target);pool=items.filter(x=>x.id!==target.id&&x.word.toLowerCase()!==target.word.toLowerCase());answer=target.word;if(!prompt)throw new Error('Dataset item has no usable English clue');}
 const distractors=shuffle(pool,r).slice(0,3);
 const choices=shuffle([{id:target.id,text:answer},...distractors.map(x=>({id:x.id,text:mode==='meaning'?x.meaning:x.word}))],r);
 return{targetId:target.id,mode,prompt,word:target.word,pos:target.pos,choices,correctId:target.id};
}
function createGame(dataset,seed,playerCount,starter=0){
 if(!dataset||!Array.isArray(dataset.items)||dataset.items.length<4)throw new Error('Invalid vocabulary dataset');
 if(!Number.isSafeInteger(seed)||!Number.isInteger(playerCount)||playerCount<2||playerCount>6||starter<0||starter>=playerCount)throw new Error('Invalid game setup');
 const g={dataset,seed:seed>>>0,playerCount,starter,active:starter,turn:0,totalTurns:playerCount*ROUNDS_PER_PLAYER,version:0,phase:'playing',scores:Array(playerCount).fill(0),streaks:Array(playerCount).fill(0),correct:Array(playerCount).fill(0),answered:Array(playerCount).fill(0),feedback:null,question:null};
 g.question=makeQuestion(g);return g;
}
function leaders(g){const m=Math.max(...g.scores);return g.scores.map((s,i)=>s===m?i:null).filter(i=>i!==null);}
function apply(g,actor,a){
 if(!a||!Number.isInteger(a.version)||a.version!==g.version)throw new Error('Stale move; refresh');
 if(g.phase==='over')throw new Error('The game has finished');if(actor!==g.active)throw new Error('Not your turn');
 if(a.type!=='answer'||typeof a.choiceId!=='string')throw new Error('Invalid action');if(!g.question.choices.some(c=>c.id===a.choiceId))throw new Error('Unknown choice');
 const ok=a.choiceId===g.question.correctId,power=(g.turn+1)%5===0,beforeLeader=Math.max(...g.scores.filter((_,i)=>i!==actor)),comeback=g.scores[actor]+150<beforeLeader;
 if(ok){g.streaks[actor]++;g.correct[actor]++;let gain=100+Math.min(4,g.streaks[actor]-1)*25;if(power)gain*=2;if(comeback)gain+=50;g.scores[actor]+=gain;g.feedback={actor,ok:true,gain,power,comeback,streak:g.streaks[actor],answer:g.question.choices.find(c=>c.id===g.question.correctId).text,word:g.question.word};}
 else{g.streaks[actor]=0;g.feedback={actor,ok:false,gain:0,power,comeback:false,streak:0,answer:g.question.choices.find(c=>c.id===g.question.correctId).text,word:g.question.word};}
 g.answered[actor]++;g.turn++;if(g.turn>=g.totalTurns){g.phase='over';g.question=null}else{g.active=(g.active+1)%g.playerCount;g.question=makeQuestion(g)}g.version++;return g;
}
function publicState(g){
 const q=g.question?{mode:g.question.mode,prompt:g.question.prompt,word:g.question.word,pos:g.question.pos,choices:g.question.choices.map(c=>({...c})),power:(g.turn+1)%5===0}:null;
 return{version:g.version,phase:g.phase,active:g.active,turn:g.turn,totalTurns:g.totalTurns,scores:[...g.scores],streaks:[...g.streaks],correct:[...g.correct],answered:[...g.answered],question:q,feedback:g.feedback?{...g.feedback}:null,winners:g.phase==='over'?leaders(g):[],dataset:{id:g.dataset.id,label:g.dataset.label},source:g.dataset.source};
}
module.exports={createGame,apply,publicState,ROUNDS_PER_PLAYER,makeQuestion,cloze};
