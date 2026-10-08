'use strict';
const {loadBand3}=require('./datasets/band3.cjs');const {loadBand2}=require('./datasets/band2.cjs');
function validate(ds,field){if(!ds||!Array.isArray(ds.items)||ds.items.filter(x=>x.word&&x[field]).length<4)throw new Error('Vocabulary dataset must contain at least four usable items');ds.items=ds.items.filter(x=>x.word&&x[field]);return ds}
function createProvider({fetchImpl=globalThis.fetch}={}){let pair=null;async function loadGame(){if(pair)return pair;pair=Promise.all([loadBand2({fetchImpl,core:'all'}),Promise.resolve(loadBand3())]).then(([band2,band3])=>({band2:validate(band2,'meaningHe'),band3:validate(band3,'meaning')}));try{return await pair}catch(e){pair=null;throw e}}return{loadGame,list:()=>[{id:'band2',label:'Band II · safe'},{id:'band3',label:'Band III · high risk'}],clear:()=>{pair=null}}}
module.exports={createProvider,validate};
