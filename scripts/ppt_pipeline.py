#!/usr/bin/env python3
"""Resumable, paced NotebookLM production; never publishes an unreviewed deck."""
import argparse,contextlib,datetime as dt,fcntl,hashlib,json,os,pathlib,re,signal,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'state/production.json'
PYTHON=os.environ.get('NLM_PYTHON',str(pathlib.Path.home()/'.local/share/uv/tools/notebooklm-mcp-cli/bin/python3'))
FIRST=['F01','F02','F03','F04','F05','F06','C02','E01','D01','W02','T01','P02']
ACTIVE={'queued','submitting'}
STOP=False
def request_stop(*_):
 global STOP
 STOP=True
signal.signal(signal.SIGTERM,request_stop)
signal.signal(signal.SIGINT,request_stop)
def log(s):print(dt.datetime.now().strftime('%H:%M:%S'),s,flush=True)
def now():return time.time()
def read(p,default):return json.loads(p.read_text()) if p.exists() else default
def save(s):
 STATE.parent.mkdir(exist_ok=True)
 with (STATE.parent/'runner.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(s,ensure_ascii=False,indent=2));tmp.replace(STATE)
def env(profile):
 e=os.environ.copy();e.update(NLM_PROFILE=profile,NOTEBOOKLM_RATE_LIMIT_MAX_RETRIES='0',PYTHONUNBUFFERED='1')
 if not e.get('HTTPS_PROXY'):
  out=subprocess.run(['scutil','--proxy'],capture_output=True,text=True).stdout
  if re.search(r'HTTPSEnable\s*:\s*1',out):
   host=re.search(r'HTTPSProxy\s*:\s*(\S+)',out);port=re.search(r'HTTPSPort\s*:\s*(\d+)',out)
   if host and port:e['HTTPS_PROXY']=e['HTTP_PROXY']=f'http://{host[1]}:{port[1]}'
 return e
def cli(s,args,profile='default',as_json=True,timeout=120):
 delay=max(0,15-(now()-s.get('last_cli',0)))
 if delay:time.sleep(delay)
 s['last_cli']=now();save(s)
 cmd=[PYTHON,str(ROOT/'scripts/nlm_once.py'),*args]
 # download subcommands select profile only via the root option + env.
 cmd+=['--profile',profile] if args[0]!='download' else []
 if args[0]=='download':cmd=[PYTHON,str(ROOT/'scripts/nlm_once.py'),'--profile',profile,*args]
 try:r=subprocess.run(cmd,env=env(profile),text=True,capture_output=True,timeout=timeout)
 except subprocess.TimeoutExpired:raise RuntimeError('CLI timed out; mutation remains unresolved until reconciliation')
 stamp=str(int(now()));(ROOT/'state'/f'last-{args[0]}-{stamp}.txt').write_text(r.stdout+'\n'+r.stderr)
 if r.returncode:
  msg=(r.stderr+r.stdout)[-1500:]
  if any(x in msg.lower() for x in ['429','resource_exhausted','rate limited']):s.setdefault('accounts',{}).setdefault(profile,{})['cooldown_until']=now()+18000;save(s)
  raise RuntimeError(msg)
 if not as_json:return r.stdout
 try:return json.loads(r.stdout)
 except ValueError:raise RuntimeError('Non-JSON response retained in state; reconcile before retry')
def unpack(raw,key):return raw if isinstance(raw,list) else raw.get(key,[])
def identifier(obj):return obj.get('notebook_id') or obj.get('source_id') or obj.get('artifact_id') or obj.get('id')
def sibling(s,profile='default'):
 """Read only: share capacity and pacing with existing production projects."""
 count=0;last=0;cool=0
 for p in [ROOT.parent/'bernstein-ypc/state/progress.json']:
  d=read(p,{})
  account=d.get('accounts',{}).get(profile,{})
  def stamp(v):
   try:return dt.datetime.fromisoformat(v).timestamp() if v else 0
   except (ValueError,TypeError):return 0
  last=max(last,stamp(account.get('last_submit_at')));cool=max(cool,stamp(account.get('cooldown_until')))
  count+=sum(1 for r in d.get('episodes',{}).values() if r.get('profile')==profile and r.get('slide_status') in ACTIVE)
 return count,last,cool

def ensure_notebook(s,category,profile):
 n=s['notebooks'].setdefault(category,{'title':'吴军专题学习｜'+category,'profile':profile})
 if n.get('id'):return n['id']
 items=unpack(cli(s,['notebook','list','--json'],profile),'notebooks');found=next((x for x in items if x.get('title')==n['title']),None)
 if not found:
  if n.get('status')=='submitting':raise RuntimeError('Unresolved notebook creation; do not duplicate')
  n['status']='submitting';save(s);found=cli(s,['notebook','create',n['title'],'--json'],profile)
 n['id']=identifier(found)
 if not n['id']:raise RuntimeError('Notebook response has no ID')
 n['status']='ready';save(s);return n['id']
def ensure_source(s,r,topic):
 profile=r['profile'];nb=ensure_notebook(s,topic['category'],profile);r['notebook_id']=nb
 if r.get('source_id'):return
 title='wujun-'+topic['code']+'｜'+topic['title'];items=unpack(cli(s,['source','list',nb,'--json'],profile),'sources');found=next((x for x in items if x.get('title')==title),None)
 if not found:
  if r.get('source_status')=='submitting':raise RuntimeError('Unresolved source upload; do not duplicate')
  if len(items)>=50:raise RuntimeError('Notebook capacity reached')
  r['source_status']='submitting';r['source_upload_sha256']=hashlib.sha256((ROOT/'work/sources'/f"{topic['code']}.md").read_bytes()).hexdigest();save(s)
  found=cli(s,['source','add',nb,'--file',str(ROOT/'work/sources'/f"{topic['code']}.md"),'--title',title,'--wait','--wait-timeout','90','--json'],profile,timeout=120)
 r['source_id']=identifier(found)
 if not r['source_id']:raise RuntimeError('Source response has no ID')
 r['source_status']='ready';r['source_sha256']=hashlib.sha256((ROOT/'work/sources'/f"{topic['code']}.md").read_bytes()).hexdigest();save(s)
def focus(t):
 refs={}
 for source in t['sources']:
  label=re.split(r'[｜丨]| - ',source['title'])[0]
  refs.setdefault(source['course'],[]).append(label)
 short='；'.join(course+'：'+'、'.join(labels) for course,labels in refs.items())
 return (f"标识 wujun-{t['code']}。为吴军课程专题《{t['title']}》制作详细学习幻灯片。必须恰好15页，包含第1页封面和第15页来源；严格逐页执行来源中15页提纲，不额外增加目录、过渡或致谢页。"
 '采用《丁丁历险记》清线漫画风格：清楚的黑色轮廓、鲜明平涂色块、连贯场景与简洁中文旁白；每页一个主要观点，以图解解释机制，避免大段文字堆叠。'
 '所有可见文字必须是简体中文，包括封面、标题、图表标签、气泡、姓名及结尾来源。16:9横版，字清楚可读。'
 '只依据绑定的这一份来源，保留人物、时间、数字、条件和观点归属，不编造数据、直接引语或结论。区分吴军观点与专题编辑归纳，历史案例不能写成当前事实或投资建议。'
 '第15页用可读的中文课程名称与讲次列来源，按课程分组，不要堆砌全部长标题或长网址。禁止显示文件名、本地路径或内部标识。来源简表：'+short)
def submit(s,t):
 code=t['code'];r=s['topics'].setdefault(code,{'status':'pending','attempts':{},'failed_artifact_ids':[]})
 profile=r.setdefault('profile','default' if code[0] in 'FCDEW' else 'account-b');account=s.setdefault('accounts',{}).setdefault(profile,{})
 if now()<account.get('cooldown_until',0):return False
 if r['status'] not in {'pending','failed'}:return False
 if not (ROOT/'work/sources'/f'{code}.ready').exists():return False
 if len(t.get('outline',[]))!=15 or [x.get('page') for x in t['outline']]!=list(range(1,16)):raise RuntimeError('Invalid 15-page source outline')
 today=dt.date.today().isoformat()
 if r['attempts'].get(today,0)>=3 or now()<r.get('next_attempt',0):return False
 other,_,cool=sibling(s,profile)
 if now()<cool or sum(x['status'] in ACTIVE and x.get('profile','default')==profile for x in s['topics'].values())+other>=8:return False
 ensure_source(s,r,t)
 # Every fresh/retry submission reconciles against the source before writing.
 artifacts=[]
 if r.get('submitted_at'):
  if now()-r['submitted_at']<1200:return False
  artifacts=unpack(cli(s,['studio','status',r['notebook_id'],'--full','--json','--limit','100'],profile),'artifacts')
 if len(artifacts)>=80:raise RuntimeError('Notebook artifact capacity reached')
 matches=[a for a in artifacts if (r['source_id'] in a.get('source_ids',[]) or f'标识 wujun-{code}' in json.dumps(a,ensure_ascii=False)) and identifier(a) not in r['failed_artifact_ids']]
 live=[a for a in matches if str(a.get('status')).lower() not in {'failed','error','4'}]
 if live:r.update(status='queued',artifact_id=identifier(live[-1]),submitted_at=now()-1200);save(s);return True
 other,last,cool=sibling(s,profile)
 if now()<max(cool,account.get('cooldown_until',0),last+60,account.get('last_submit',0)+60):return False
 if sum(x['status'] in ACTIVE and x.get('profile','default')==profile for x in s['topics'].values())+other>=8:return False
 r.update(status='submitting',submitted_at=now());account['last_submit']=now();r['attempts'][today]=r['attempts'].get(today,0)+1;save(s)
 try:raw=cli(s,['slides','create',r['notebook_id'],'--source-ids',r['source_id'],'--format','detailed_deck','--length','default','--language','zh-CN','--focus',focus(t),'--confirm','--json'],profile)
 except Exception:save(s);raise
 aid=identifier(raw)
 if not aid:raise RuntimeError('Slide creation unresolved: response has no artifact ID')
 r.update(status='queued',artifact_id=aid);save(s);log(f'{code}: submitted {aid}');return True

def poll(s):
 due=[(code,r) for code,r in s['topics'].items() if r['status'] in ACTIVE and now()-r.get('submitted_at',now())>=1200]
 for nb in dict.fromkeys(r['notebook_id'] for _,r in due):
  profile=next(r.get('profile','default') for _,r in due if r['notebook_id']==nb)
  if now()<s.get('accounts',{}).get(profile,{}).get('cooldown_until',0):continue
  if now()-s['last_poll'].get(nb,0)<300:continue
  s['last_poll'][nb]=now();save(s);arts=unpack(cli(s,['studio','status',nb,'--full','--json','--limit','100'],profile),'artifacts')
  for code,r in due:
   if r['notebook_id']!=nb:continue
   match=[a for a in arts if identifier(a) not in r['failed_artifact_ids'] and (identifier(a)==r.get('artifact_id') or r['source_id'] in a.get('source_ids',[]) or f'标识 wujun-{code}' in json.dumps(a,ensure_ascii=False))]
   if not match:continue # Uncertain submission remains blocked; never automatically duplicate it.
   a=match[-1];status=str(a.get('status')).lower();r['artifact_id']=identifier(a)
   if status in {'failed','error','4'}:
    r['failed_artifact_ids'].append(identifier(a));r.update(status='failed',next_attempt=now()+60);log(f'{code}: remote failed, item-only backoff')
   elif status in {'completed','complete','ready','3'}:
    r['status']='download_pending';log(f'{code}: remote deck ready')
   else:r['status']='queued'
   save(s)

def download(s):
 for code,r in s['topics'].items():
  if r['status']!='download_pending':continue
  path=ROOT/'work/slides'/f'{code}-original.pdf';path.parent.mkdir(exist_ok=True)
  if not path.exists():
   part=path.with_suffix('.part.pdf');cli(s,['download','slide-deck',r['notebook_id'],'--id',r['artifact_id'],'--output',str(part),'--no-progress'],r.get('profile','default'),as_json=False,timeout=180)
   if not part.read_bytes().startswith(b'%PDF-'):raise RuntimeError('Downloaded file is not PDF')
   part.replace(path)
  from pypdf import PdfReader
  pages=len(PdfReader(path).pages);r['pages']=pages;r['status']='review_pending' if pages==15 else 'page_count_mismatch';save(s);log(f'{code}: downloaded {pages} pages; needs visual/source review')

def step():
 s=read(STATE,{'topics':{},'notebooks':{},'last_poll':{}})
 poll(s);download(s)
 content=[json.loads(p.read_text()) for p in (ROOT/'work/content').glob('*.json')]
 content.sort(key=lambda t:(FIRST.index(t['code']) if t['code'] in FIRST else 100,t['code']))
 for t in content:
  try:
   if submit(s,t):return True
  except Exception as e:
   log(t['code']+': action unresolved: '+str(e)[:250])
 return False

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--minutes',type=int,default=0);args=parser.parse_args();STATE.parent.mkdir(exist_ok=True)
 with (STATE.parent/'cycle.lock').open('w') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Another production cycle owns the lock')
  end=now()+args.minutes*60
  while True:
   try:step()
   except Exception as e:log('Paused action: '+str(e)[:450])
   if STOP or (STATE.parent/'pause-production').exists() or now()>=end:break
   time.sleep(45)
if __name__=='__main__':main()
