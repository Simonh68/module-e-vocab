'use strict';
const {loadBand3}=require('./datasets/band3.cjs');
const {loadBand2}=require('./datasets/band2.cjs');
const DEFINITIONS=[
 {id:'band3',label:'Band III · All A–D'},
 {id:'band2-core1',label:'Band II · Core I'},
 {id:'band2-core2',label:'Band II · Core II'},
 {id:'band2-all',label:'Band II · All'}
];
function validate(ds){if(!ds||!Array.isArray(ds.items)||ds.items.length<4)throw new Error('Vocabulary dataset must contain at least four usable items');for(const x of ds.items)if(!x.id||!x.word||(!x.meaning&&!x.example))throw new Error('Invalid vocabulary item');return ds;}
function createProvider({fetchImpl=globalThis.fetch}={}){
 const cache=new Map();
 async function load(id='band3'){
  if(cache.has(id))return cache.get(id);
  const p=(async()=>{
   if(id==='band3')return validate(loadBand3());
   if(id==='band2-core1')return validate(await loadBand2({fetchImpl,core:'core1'}));
   if(id==='band2-core2')return validate(await loadBand2({fetchImpl,core:'core2'}));
   if(id==='band2-all')return validate(await loadBand2({fetchImpl,core:'all'}));
   throw new Error('Unknown vocabulary dataset');
  })();cache.set(id,p);try{return await p}catch(e){cache.delete(id);throw e}
 }
 return{load,list:()=>DEFINITIONS.map(x=>({...x})),clear:()=>cache.clear()};
}
module.exports={createProvider,DEFINITIONS,validate};
