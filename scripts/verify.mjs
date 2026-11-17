import fs from 'node:fs';
import assert from 'node:assert/strict';
import {esc,article,directory} from '../src/render.js';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const {topics}=read('src/data/index.json');const slides=read('src/data/slides.json');const plan=read('src/data/plan.json');
assert.equal(new Set(topics.map(t=>t.code)).size,topics.length);
for(const t of topics){
 const path=`public${t.url}`;const raw=fs.readFileSync(path,'utf8');assert(!raw.includes('/Users/'));assert(!raw.includes('source_id'));const d=JSON.parse(raw);
 assert.equal(d.code,t.code);assert(d.sources.length>=8);assert(d.sections.length>=4);assert.equal(d.outline.length,15);
 for(const [i,p] of d.outline.entries()){assert.equal(p.page,i+1);assert(p.title);assert(p.points.length>=1);}
 for(const s of [...d.sections,...d.outline])for(const n of s.sourceRefs)assert(n>=1&&n<=d.sources.length,`${t.code}: invalid ref ${n}`);
 for(const s of d.sources){assert(plan.scope.includes(s.course));assert.equal(new URL(s.url).hostname,'github.com');}
 const html=article(d,slides[t.id]);assert(html.includes(d.title));assert(html.includes('查看 '+d.sources.length+' 篇原课'));if(!slides[t.id])assert(!html.includes('data-open-slides'));
 if(slides[t.id]){const deck=slides[t.id];assert.equal(deck.pages,15);assert(fs.existsSync(`public${deck.pdfUrl}`));for(let n=1;n<=15;n++)assert(fs.existsSync(`public${deck.prefix}${n}.webp`));}
}
assert.equal(esc('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');
assert(directory([],null,{}).includes('没有找到'));
console.log(`Verified ${topics.length} topic schemas, source boundaries, references and ${Object.keys(slides).length} decks.`);
