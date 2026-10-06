'use strict';
const fs=require('node:fs'),path=require('node:path');
fs.copyFileSync(path.join(__dirname,'index.html'),path.join(__dirname,'demo.html'));
console.log('Built demo.html shell.');
