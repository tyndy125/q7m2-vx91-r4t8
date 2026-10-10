import unittest
from factory.domains.status_effects import Effects
class EffectTests(unittest.TestCase):
 def test_expiry(self):
  s=Effects();s.apply("poison",10,5,-2);self.assertEqual(s.total_modifier(11),-2);self.assertIsNone(s.get("poison",15))
 def test_stacking(self):
  s=Effects();s.apply("buff",0,10,3);s.apply("buff",1,10,3,"stack",3);self.assertEqual(s.total_modifier(2),6)
 def test_refresh(self):
  s=Effects();s.apply("buff",0,10,3);s.apply("buff",2,10,99);self.assertEqual(s.total_modifier(3),3);self.assertEqual(s.get("buff",11).expires,12)
 def test_dispel_and_purge(self):
  s=Effects();s.apply("a",0,1);s.apply("b",0,2);self.assertEqual(s.purge(1),1);self.assertTrue(s.dispel("b"))
 def test_roundtrip(self):
  s=Effects();s.apply("a",0,10,3);self.assertEqual(Effects.restore_snapshot(s.snapshot()).snapshot(),s.snapshot())
 def test_invalid(self):
  with self.assertRaises(ValueError):Effects().apply("a",0,2,policy="unknown")
if __name__=="__main__":unittest.main()
