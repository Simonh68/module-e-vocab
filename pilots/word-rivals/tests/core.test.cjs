'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),core=require('../core.cjs');
const meaningDataset={id:'meaning',label:'Meaning set',source:{test:true},items:[
{id:'a',word:'aid',pos:'Verb',meaning:'help or support',example:'They aid the team.'},
{id:'b',word:'total',pos:'Adjective',meaning:'complete or whole',example:'The total cost rose.'},
{id:'c',word:'concept',pos:'Noun',meaning:'an idea',example:'This concept is useful.'},
{id:'d',word:'damage',pos:'Noun',meaning:'harm or injury',example:'The storm caused damage.'},
{id:'e',word:'rapid',pos:'Adjective',meaning:'very fast',example:'There was rapid growth.'}
]};
const clozeDataset={id:'cloze',label:'Cloze set',source:{test:true},items:[
{id:'a',word:'aid',pos:'Verb',meaning:'',example:'They aid the team.'},
{id:'b',word:'total',pos:'Adjective',meaning:'',example:'The total cost rose.'},
{id:'c',word:'concept',pos:'Noun',meaning:'',example:'This concept is useful.'},
{id:'d',word:'damage',pos:'Noun',meaning:'',example:'The storm caused damage.'},
{id:'e',word:'rapid',pos:'Adjective',meaning:'',example:'There was rapid growth.'}
]};
test('one engine accepts different datasets',()=>{for(const ds of [meaningDataset,clozeDataset]){const g=core.createGame(ds,123,2);assert.equal(g.dataset.id,ds.id);assert.equal(g.question.choices.length,4);}});
test('meaning datasets show a word and four English meanings',()=>{const g=core.createGame(meaningDataset,2,2);assert.equal(g.question.mode,'meaning');assert.ok(meaningDataset.items.some(x=>x.word===g.question.prompt));assert.ok(g.question.choices.every(x=>typeof x.text==='string'&&x.text));});
test('datasets without definitions fall back to English cloze questions',()=>{const g=core.createGame(clozeDataset,3,2);assert.equal(g.question.mode,'cloze');assert.match(g.question.prompt,/_____/);assert.equal(g.question.choices.length,4);});
test('public state hides the answer key and keeps dataset identity',()=>{const g=core.createGame(meaningDataset,4,2),p=core.publicState(g);assert.equal(p.question.correctId,undefined);assert.equal(p.dataset.id,'meaning');});
test('scoring and turn rotation do not depend on dataset',()=>{const g=core.createGame(meaningDataset,5,3),id=g.question.correctId;core.apply(g,0,{type:'answer',choiceId:id,version:0});assert.equal(g.scores[0],100);assert.equal(g.active,1);});
test('complete match remains six turns per player',()=>{const g=core.createGame(clozeDataset,7,4);while(g.phase!=='over')core.apply(g,g.active,{type:'answer',choiceId:g.question.correctId,version:g.version});assert.deepEqual(g.answered,[6,6,6,6]);assert.equal(g.turn,24);});
