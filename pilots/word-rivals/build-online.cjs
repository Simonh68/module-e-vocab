'use strict';
const fs=require('node:fs'),path=require('node:path');
fs.copyFileSync(path.join(__dirname,'index.html'),path.join(__dirname,'online.html'));
console.log('Built online.html from English-only room quiz UI.');
