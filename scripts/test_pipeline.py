import pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).parent));import ppt_pipeline as p
class ProductionGuardTests(unittest.TestCase):
 def test_unresolved_submission_is_never_resubmitted(self):
  s={'topics':{'F01':{'status':'submitting'}}}
  with patch.object(p,'cli',side_effect=AssertionError('must not call API')):
   self.assertFalse(p.submit(s,{'code':'F01'}))
 def test_no_poll_inside_twenty_minutes(self):
  s={'topics':{'F01':{'status':'queued','submitted_at':p.now()-1190,'notebook_id':'n'}},'last_poll':{}}
  with patch.object(p,'cli',side_effect=AssertionError('premature polling')):p.poll(s)
 def test_recent_poll_blocks_repeat(self):
  s={'topics':{'F01':{'status':'queued','submitted_at':p.now()-1300,'notebook_id':'n'}},'last_poll':{'n':p.now()-20}}
  with patch.object(p,'cli',side_effect=AssertionError('excessive polling')):p.poll(s)
 def test_review_pending_is_not_downloaded_again(self):
  with patch.object(p,'cli',side_effect=AssertionError('must not download')):p.download({'topics':{'F01':{'status':'review_pending'}}})
 def test_other_project_capacity_blocks_submission(self):
  s={'topics':{},'accounts':{}}
  t={'code':'F01','outline':[{'page':i} for i in range(1,16)]}
  with patch.object(p,'sibling',return_value=(10,0,0)),patch.object(p,'ensure_source',side_effect=AssertionError('capacity must be checked before upload')):
   self.assertFalse(p.submit(s,t))
 def test_cooling_account_blocks_mutation(self):
  s={'topics':{},'accounts':{'default':{'cooldown_until':p.now()+1000}}}
  with patch.object(p,'ensure_source',side_effect=AssertionError('cooldown ignored')):
   self.assertFalse(p.submit(s,{'code':'F01'}))
 def test_repeated_generation_limits_stop_new_mutations_but_allow_reads(self):
  s={}
  with patch.object(p,'now',return_value=1000):
   p.apply_rate_backoff(s,'account-b','slides','Rate limited, wait a few minutes')
   self.assertEqual(s['accounts']['account-b']['generation_cooldown_until'],1180)
  with patch.object(p,'now',return_value=1300):
   p.apply_rate_backoff(s,'account-b','slides','Rate limited, wait a few minutes')
   self.assertEqual(s['accounts']['account-b']['generation_cooldown_until'],19300)
   self.assertNotIn('cooldown_until',s['accounts']['account-b'])
   self.assertNotIn('default',s['accounts'])
 def test_explicit_quota_limit_gets_five_hour_hold(self):
  s={}
  with patch.object(p,'now',return_value=1000):
   p.apply_rate_backoff(s,'default','slides','429 RESOURCE_EXHAUSTED')
   self.assertEqual(s['accounts']['default']['generation_cooldown_until'],19000)
if __name__=='__main__':unittest.main()
