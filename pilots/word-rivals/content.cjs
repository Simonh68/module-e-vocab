'use strict';
const fs=require('node:fs'),path=require('node:path');
const masterPath=path.join(__dirname,'../../data/vocabulary-master.json');
const raw=JSON.parse(fs.readFileSync(masterPath,'utf8'));
const words=raw.map((r,i)=>{
  const en=String(r.en||r.official_entry||'').trim();
  const definition=String(r.record_sense_en||r.support_text||'').trim();
  const pos=String(r.pos||r.grammar||'').trim();
  const id=String(r.source_entry_id||('B3-'+i)).trim();
  const group=String(r.group||'').trim();
  return {id,en,definition,pos,group};
}).filter(w=>w.en&&w.definition&&w.definition.length>2&&w.definition.toLowerCase()!==w.en.toLowerCase());
const seen=new Set();
const unique=words.filter(w=>{const k=w.en.toLowerCase()+'|'+w.definition.toLowerCase();if(seen.has(k))return false;seen.add(k);return true;});
if(unique.length<40) throw new Error('Band III corpus is too small for the room game');
module.exports={words:unique,source:{repository:'Simonh68/module-e-vocab',file:'data/vocabulary-master.json'}};
