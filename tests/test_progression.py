import unittest
from factory.domains.progression import LevelTable,Progress
class ProgressTests(unittest.TestCase):
 def test_thresholds(self):
  t=LevelTable((0,100,300));self.assertEqual(t.level(0),1);self.assertEqual(t.level(100),2);self.assertEqual(t.level(300),3)
 def test_gain_multiple(self):
  p=Progress(LevelTable((0,10,20,40)));self.assertEqual(p.grant(25),(2,3));self.assertEqual(p.level,3)
 def test_cap(self):
  p=Progress(LevelTable((0,10)),100);self.assertIsNone(p.table.next_required(p.xp))
 def test_snapshot(self):
  p=Progress(LevelTable((0,10)),3);self.assertEqual(Progress.restore(p.snapshot()).snapshot(),p.snapshot())
 def test_invalid(self):
  for fn in [lambda:LevelTable((1,)),lambda:LevelTable((0,10,10)),lambda:Progress(LevelTable((0,)), -1),lambda:Progress(LevelTable((0,))).grant(-1)]:
   with self.assertRaises(ValueError):fn()
if __name__=="__main__":unittest.main()
