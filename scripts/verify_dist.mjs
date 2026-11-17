import fs from 'node:fs';import assert from 'node:assert/strict';import path from 'node:path';
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const files=walk('dist');assert(files.includes('dist/index.html'));
for(const file of files){assert(fs.statSync(file).size<25*1024*1024,`${file}: asset too large`);assert(!/^dist\/(work|state|logs)\//.test(file));if(/\.(json|js|html|css|txt|md)$/.test(file)){const s=fs.readFileSync(file,'utf8');assert(!s.includes('/Users/'),`${file}: local path leaked`);assert(!s.includes('artifact_id'),`${file}: generation state leaked`);}}
console.log(`Verified deployment boundary: ${files.length} static files, no raw sources or local state.`);
