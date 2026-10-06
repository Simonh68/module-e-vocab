'use strict';
const BASE='https://simonh68.github.io/E-Vocab-Band-II/groups/';
function canCloze(word,example){if(!word||!example)return false;return example.toLowerCase().includes(word.toLowerCase());}
function parseGroup(html,group){
  const m=html.match(/const words=(\[[\s\S]*?\]);/);if(!m)throw new Error('Band II group '+group+' has no embedded word data');
  const raw=JSON.parse(m[1]),items=[];
  for(const r of raw){
    const word=String(r.en||'').trim(),example=String(r.ex_en||'').trim();
    let meaning=String(r.record_sense_en||'').trim();
    if(!meaning&&Array.isArray(r.synonyms)&&r.synonyms.length)meaning=r.synonyms.map(String).join('; ');
    if(!word||(!meaning&&!canCloze(word,example)))continue;
    items.push({id:'B2-'+String(r.serial),word,pos:String(r.pos||'').trim(),meaning,example,group:'G'+String(group).padStart(2,'0')});
  }
  return items;
}
async function loadBand2({fetchImpl=globalThis.fetch,core='all'}={}){
  if(typeof fetchImpl!=='function')throw new Error('Band II loader needs fetch');
  const groups=core==='core1'?Array.from({length:20},(_,i)=>i+1):core==='core2'?Array.from({length:20},(_,i)=>i+21):Array.from({length:40},(_,i)=>i+1);
  const all=[];
  for(const n of groups){
    const url=BASE+'group-'+String(n).padStart(2,'0')+'.html';
    const res=await fetchImpl(url);if(!res.ok)throw new Error('Band II source unavailable: group '+n);
    all.push(...parseGroup(await res.text(),n));
  }
  const seen=new Set(),items=all.filter(x=>{if(seen.has(x.id))return false;seen.add(x.id);return true;});
  const suffix=core==='core1'?'Core I':core==='core2'?'Core II':'All';
  return{id:'band2-'+core,label:'Band II · '+suffix,items,source:{repository:'Simonh68/E-Vocab-Band-II',url:BASE,groups}};
}
module.exports={loadBand2,parseGroup,canCloze};
