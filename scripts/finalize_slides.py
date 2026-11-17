#!/usr/bin/env python3
"""Build only explicitly reviewed decks, then mark local completion."""
import fcntl,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
with (ROOT/'state/cycle.lock').open('w') as lock:
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Pause production before building or publishing')
 subprocess.run([sys.executable,str(ROOT/'scripts/build_slides.py')],check=True)
 slides=json.loads((ROOT/'src/data/slides.json').read_text());statefile=ROOT/'state/production.json';s=json.loads(statefile.read_text());plan=json.loads((ROOT/'src/data/plan.json').read_text())
 for i,(code,*_) in enumerate(plan['roadmap'],1):
  r=s['topics'].get(code);deck=slides.get(str(i))
  if not r or r['status'] not in {'reviewed','complete'} or not deck:continue
  if deck['pages']!=15:raise SystemExit(f'{code}: wrong page count')
  if not all((ROOT/'public'/f"{deck['prefix'].lstrip('/')}{n}.webp").is_file() for n in range(1,16)):raise SystemExit(f'{code}: missing slide image')
  r['status']='complete';r['publication_status']='unverified'
 with (ROOT/'state/runner.lock').open('w') as writer:
  fcntl.flock(writer,fcntl.LOCK_EX);tmp=statefile.with_suffix('.tmp');tmp.write_text(json.dumps(s,ensure_ascii=False,indent=2));tmp.replace(statefile)
 print('Local completion:',sum(r['status']=='complete' for r in s['topics'].values()))
