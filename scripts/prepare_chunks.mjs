import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const plan=read('src/data/plan.json');
const contentDir='work/content';
fs.mkdirSync('src/data/topics',{recursive:true});
fs.mkdirSync('public/topics',{recursive:true});
const index=[]; const search=[];
for(const [i,[code,category,title]] of plan.roadmap.entries()) {
 let path=`${contentDir}/${code}.json`; if(!fs.existsSync(path))path=`src/data/topics/${code}.json`; if(!fs.existsSync(path))continue;
 const raw=read(path);
 if(raw.outline.length!==15||raw.outline.some((p,i)=>p.page!==i+1))throw Error(`${code}: outline must have 15 pages`);
 if(raw.sources.length<8||raw.sources.some(s=>!plan.scope.includes(s.course)))throw Error(`${code}: invalid sources`);
 const item={...raw,id:i+1,sources:raw.sources.map(({course,title,url})=>({course,title,url}))};
 const json=JSON.stringify(item); fs.writeFileSync(`src/data/topics/${code}.json`,json); if(json.includes('/Users/'))throw Error(`${code}: local path leakage`);
 const hash=crypto.createHash('sha256').update(json).digest('hex').slice(0,12);
 const url=`/topics/${code}-${hash}.json`; fs.writeFileSync(`public${url}`,json);
 index.push({id:i+1,code,category,title:raw.title,question:raw.question,concepts:raw.concepts,courses:[...new Set(raw.sources.map(s=>s.course))],sourceCount:raw.sources.length,url});
 search.push({code,text:[raw.title,raw.question,raw.thesis,raw.plain,...raw.concepts,...raw.sections.map(s=>s.title+' '+s.body),...raw.sources.map(s=>s.title+' '+s.course)].join(' ')});
}
if(!index.length)throw Error('No reviewed content');
const live=new Set(index.map(x=>x.url.split('/').pop()));
for(const file of fs.readdirSync('public/topics'))if(file.endsWith('.json')&&!live.has(file))fs.unlinkSync(`public/topics/${file}`);
fs.writeFileSync('src/data/index.json',JSON.stringify({planned:42,topics:index}));
fs.writeFileSync('public/search.json',JSON.stringify(search));
console.log(`Prepared ${index.length}/42 topic articles`);
