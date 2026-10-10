import unittest
from factory.domains.quest_tracker import Objective,Quest
class QuestTests(unittest.TestCase):
 def test_progress(self):
  q=Quest((Objective("kill",3),));self.assertEqual(q.advance("kill",2),2);self.assertFalse(q.complete);self.assertEqual(q.advance("kill",10),1);self.assertTrue(q.complete)
 def test_multiple(self):
  q=Quest((Objective("a",1),Objective("b",2)));q.advance("a");self.assertFalse(q.complete);q.advance("b",2);self.assertTrue(q.complete)
 def test_claim_once(self):
  q=Quest((Objective("a",1),));q.advance("a");self.assertTrue(q.claim());self.assertFalse(q.claim())
 def test_snapshot(self):
  q=Quest((Objective("a",2),));q.advance("a");self.assertEqual(Quest.restore(q.snapshot()).snapshot(),q.snapshot())
 def test_invalid(self):
  for fn in [lambda:Quest((Objective("a",1),Objective("a",2))),lambda:Objective("a",0),lambda:Quest((Objective("a",1),)).advance("x")]:
   with self.assertRaises(ValueError):fn()
if __name__=="__main__":unittest.main()
