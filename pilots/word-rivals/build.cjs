'use strict';
const fs=require('node:fs'),path=require('node:path');
const dir=__dirname;
const content=fs.readFileSync(path.join(dir,'content.cjs'),'utf8');
const core=fs.readFileSync(path.join(dir,'core.cjs'),'utf8');
const offline=`<script>window.WRCore=(()=>{const mods={};function run(name,src){const module={exports:{}};src(module,(n)=>mods[n]);mods[name]=module.exports;}run('./content.cjs',function(module,require){${content}\n});run('./core.cjs',function(module,require){${core}\n});return mods['./core.cjs'];})();</script>`;
const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
fs.writeFileSync(path.join(dir,'demo.html'),html.replace('<!--OFFLINE_CORE-->',offline));
console.log('Built standalone demo.html (no network or external assets required).');
