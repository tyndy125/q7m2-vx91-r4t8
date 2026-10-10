import unittest
from factory.domains.inventory import Inventory
class InventoryTests(unittest.TestCase):
 def test_stack(self):
  i=Inventory(1);self.assertTrue(i.add("a",2));self.assertTrue(i.add("a",3));self.assertEqual(i.count("a"),5)
 def test_slots(self):
  i=Inventory(1);i.add("a",1);self.assertFalse(i.add("b",1))
 def test_remove(self):
  i=Inventory(1);i.add("a",2);self.assertFalse(i.remove("a",3));self.assertTrue(i.remove("a",2));self.assertEqual(i.stacks,{})
 def test_atomic_transfer(self):
  a=Inventory(2);b=Inventory(1);a.add("a",2);b.add("b",1)
  self.assertFalse(a.transfer(b,"a",1));self.assertEqual(a.count("a"),2)
  b.remove("b",1);self.assertTrue(a.transfer(b,"a",1));self.assertEqual(b.count("a"),1)
 def test_snapshot(self):
  i=Inventory(2);i.add("a",3);self.assertEqual(Inventory.restore(i.snapshot()).snapshot(),i.snapshot())
 def test_invalid(self):
  for fn in [lambda:Inventory(0),lambda:Inventory(1,{"a":0}),lambda:Inventory(1).add("a",-1)]:
   with self.assertRaises(ValueError):fn()
if __name__=="__main__":unittest.main()
