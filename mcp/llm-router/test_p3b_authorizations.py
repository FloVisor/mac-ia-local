"""New P3-B adversarial checks, simulated inference only; no production broker."""
import concurrent.futures,hashlib,json,sqlite3,tempfile,time,unittest,threading
from authorization import Authorizations,Denied

class P3B(unittest.TestCase):
 def test_simulated_bound_one_use_and_concurrent(self):
  with tempfile.TemporaryDirectory() as root:
   dbpath=root+'/broker.db';db=sqlite3.connect(dbpath);a=Authorizations(db)
   data={'task':'synthetic public task','parameters':{'max_tokens':16}}
   binding=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
   issue=dict(identity='openclaw-pro',task='one-task',model='paid-openrouter/glm-5.3',data_hash=binding,max_usd=.01,expires=time.time()+60,decision='approved')
   base={k:issue[k] for k in ['identity','task','model','data_hash','max_usd']}|{'budget_remaining':1}
   for decision in ['deny','expired','',None]:
    with self.assertRaises(Denied):a.issue(**(issue|{'decision':decision}))
   token=a.issue(**issue)
   for mismatch in [{'identity':'openclaw-perso'},{'task':'other'},{'model':'paid/task-advanced'},{'data_hash':'mutated'},{'max_usd':.02},{'budget_remaining':None}]:
    with self.assertRaises(Denied):a.consume(token=token,**(base|mismatch))
   calls=[];lock=threading.Lock()
   def fake_provider(permit):
    with lock:calls.append({'model':base['model'],'actual_cost_usd':.004,'limit_usd':permit['max_usd']})
    return {'text':'synthetic result','cost_usd':.004}
   def consume(_):
    conn=sqlite3.connect(dbpath,timeout=5)
    try:
     auth=Authorizations(conn)
     try:
      permit=auth.consume(token=token,**base);fake_provider(permit);return 1
     except Denied:return 0
    finally:conn.close()
   with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:self.assertEqual(sum(pool.map(consume,range(8))),1)
   self.assertEqual(calls,[{'model':base['model'],'actual_cost_usd':.004,'limit_usd':.01}])
   with self.assertRaises(Denied):a.consume(token=token,**base)
   revoked=a.issue(**issue);a.revoke(revoked)
   with self.assertRaises(Denied):a.consume(token=revoked,**base)
   expired=a.issue(**(issue|{'expires':time.time()+.03}));time.sleep(.04)
   with self.assertRaises(Denied):a.consume(token=expired,**base)
   db.close()
