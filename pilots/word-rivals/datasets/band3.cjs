'use strict';
const fs=require('node:fs'),path=require('node:path');
function loadBand3(){
  const file=path.join(__dirname,'../../../data/vocabulary-master.json');
  const raw=JSON.parse(fs.readFileSync(file,'utf8'));
  const seen=new Set(),items=[];
  for(let i=0;i<raw.length;i++){
    const r=raw[i],word=String(r.en||r.official_entry||'').trim(),meaning=String(r.record_sense_en||r.support_text||'').trim();
    if(!word||!meaning||meaning.length<3||word.toLowerCase()===meaning.toLowerCase())continue;
    const key=word.toLowerCase()+'|'+meaning.toLowerCase();if(seen.has(key))continue;seen.add(key);
    items.push({id:String(r.source_entry_id||('B3-'+i)),word,pos:String(r.pos||r.grammar||'').trim(),meaning,example:String(r.ex_en||'').trim(),group:String(r.group||'').trim()});
  }
  return{id:'band3',label:'Band III · All A–D',items,source:{repository:'Simonh68/module-e-vocab',file:'data/vocabulary-master.json'}};
}
module.exports={loadBand3};
