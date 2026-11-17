import {execFileSync} from 'node:child_process';import {resolve} from 'node:path';import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const portfolio=process.env.XIAOSANG_PORTFOLIO_DIR||resolve(root,'../holynova.github.io');
execFileSync('git',['diff','--quiet','HEAD','--'],{cwd:root,stdio:'inherit'});
execFileSync('npx',['--yes','wrangler@4.128.0','deploy',...(process.argv.includes('--dry-run')?['--dry-run']:[]),'--config','wrangler.jsonc'],{cwd:portfolio,env:{...process.env,WUJUN_STUDY_DIST:resolve(root,'dist')},stdio:'inherit'});
