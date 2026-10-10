import unittest
from factory.domains.tick_scheduler import TickScheduler
class SchedulerTests(unittest.TestCase):
 def test_order(self):
  s=TickScheduler();s.schedule(10,"a");s.schedule(5,"b");s.schedule(5,"c")
  self.assertEqual([e.kind for e in s.due(5)],["b","c"]);self.assertEqual(s.due(9),[]);self.assertEqual(s.due(10)[0].kind,"a")
 def test_cancel(self):
  s=TickScheduler();i=s.schedule(1,"a");self.assertTrue(s.cancel(i));self.assertFalse(s.cancel(i))
 def test_limit(self):
  s=TickScheduler()
  for _ in range(3):s.schedule(1,"a")
  self.assertEqual(len(s.due(1,2)),2);self.assertEqual(len(s.due(1)),1)
 def test_snapshot(self):
  s=TickScheduler();s.schedule(3,"a","payload")
  self.assertEqual(TickScheduler.restore(s.snapshot()).snapshot(),s.snapshot())
 def test_invalid(self):
  s=TickScheduler()
  for f in [lambda:s.schedule(-1,"a"),lambda:s.schedule(1,""),lambda:s.due(-1),lambda:TickScheduler.restore({"sequence":0,"pending":[{"tick":0,"sequence":0,"kind":"x","payload":""}]})]:
   with self.assertRaises(ValueError):f()
if __name__=="__main__":unittest.main()
