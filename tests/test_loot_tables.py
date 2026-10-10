import unittest
from random import Random
from factory.domains.loot_tables import Drop,LootTable
class LootTests(unittest.TestCase):
 def test_deterministic(self):
  t=LootTable([Drop("a",2),Drop("b",3,1,4)])
  self.assertEqual(t.roll(Random(42),20),t.roll(Random(42),20))
 def test_unique(self):
  t=LootTable([Drop("a",1,unique=True),Drop("b",1,unique=True)])
  self.assertEqual(set(t.roll(Random(1),10)),{"a","b"})
 def test_exclusions(self):
  t=LootTable([Drop("a",1),Drop("b",1)])
  self.assertEqual(t.roll(Random(1),3,{"a"}),{"b":3})
 def test_quantities(self):
  t=LootTable([Drop("a",1,3,3)])
  self.assertEqual(t.roll(Random(1),2),{"a":6})
 def test_roundtrip(self):
  t=LootTable([Drop("a",2,0,5,True)])
  self.assertEqual(LootTable.restore_snapshot(t.snapshot()).snapshot(),t.snapshot())
 def test_invalid(self):
  for fn in [lambda:Drop("a",0),lambda:LootTable([]),lambda:LootTable([Drop("a",1),Drop("a",2)]),lambda:LootTable([Drop("a",1)]).roll(Random(1),-1)]:
   with self.assertRaises(ValueError):fn()
if __name__=="__main__":unittest.main()
