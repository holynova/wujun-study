import fs from 'node:fs';import {execFileSync} from 'node:child_process';
const pkg=JSON.parse(fs.readFileSync('package.json','utf8'));
fs.writeFileSync('dist/release.json',JSON.stringify({project:'wujun-study',version:pkg.version,commit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),topics:42,decks:Object.keys(JSON.parse(fs.readFileSync('src/data/slides.json','utf8'))).length})+'\n');
