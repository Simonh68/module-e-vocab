'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {parseGroup,canCloze}=require('../datasets/band2.cjs'),{createProvider}=require('../vocab-provider.cjs');
test('Band II parser keeps English meanings when supplied',()=>{const html='<script>const words='+JSON.stringify([{serial:1,en:'aid',pos:'Verb',record_sense_en:'help',synonyms:[],ex_en:'They aid us.'}])+ ';</script>';const x=parseGroup(html,1);assert.equal(x[0].meaning,'help');});
test('Band II parser can use a source example as an English cloze fallback',()=>{const html='<script>const words='+JSON.stringify([{serial:2,en:'lift',pos:'Verb',record_sense_en:'',synonyms:[],ex_en:'Please lift the box.'}])+ ';</script>';const x=parseGroup(html,1);assert.equal(x[0].meaning,'');assert.equal(canCloze(x[0].word,x[0].example),true);});
test('provider exposes four swappable dataset ids',()=>{const p=createProvider({fetchImpl:async()=>{throw new Error('unused')}});assert.deepEqual(p.list().map(x=>x.id),['band3','band2-core1','band2-core2','band2-all']);});
