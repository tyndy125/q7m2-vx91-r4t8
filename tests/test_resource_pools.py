import unittest
from factory.domains.resource_pools import Pool,Resources
class ResourceTests(unittest.TestCase):
 def test_spend_and_restore(self):
  p=Pool(100,50);self.assertTrue(p.spend(20));self.assertFalse(p.spend(40));self.assertEqual(p.restore(90),70);self.assertEqual(p.current,100)
 def test_regeneration(self):
  p=Pool(10,1,2);self.assertEqual(p.tick(3),6);self.assertEqual(p.tick(3),3)
 def test_resize(self):
  p=Pool(100,50);p.set_maximum(200,True);self.assertEqual(p.current,100)
 def test_snapshot(self):
  r=Resources();r.add("health",100,50,3);r.add("mana",20)
  self.assertEqual(Resources.restore_snapshot(r.snapshot()).snapshot(),r.snapshot())
 def test_invalid(self):
  for fn in [lambda:Pool(10,11),lambda:Pool(-1,0),lambda:Pool(10,5).spend(-1),lambda:Resources().tick(-1)]:
   with self.assertRaises(ValueError):fn()
if __name__=="__main__":unittest.main()
