import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("domain_cooldowns",Path(__file__).resolve().parents[1]/"factory/domains/cooldowns.py")
m=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=m
spec.loader.exec_module(m)


class CooldownDomainTests(unittest.TestCase):
    def test_individual(self):
        s=m.CooldownState()
        self.assertTrue(s.activate("spell",10,5))
        self.assertFalse(s.activate("spell",11,5))
        self.assertEqual(s.remaining("spell",13),2)
        self.assertTrue(s.ready("spell",15))
    def test_group(self):
        s=m.CooldownState()
        self.assertTrue(s.activate("a",10,2,group="global",group_duration=5))
        self.assertFalse(s.activate("b",12,1,group="global"))
        self.assertTrue(s.activate("b",15,1,group="global"))
    def test_charges(self):
        s=m.CooldownState();s.configure_charges("a",2)
        self.assertTrue(s.spend_charge("a",0,10))
        self.assertTrue(s.spend_charge("a",0,10))
        self.assertFalse(s.spend_charge("a",0,10))
        self.assertEqual(s.available_charges("a",10),2)
    def test_grouped_charges(self):
        s=m.CooldownState();s.configure_charges("a",2)
        self.assertTrue(s.spend_charge("a",0,5,group="g",group_duration=2))
        self.assertFalse(s.spend_charge("a",1,5,group="g"))
        self.assertTrue(s.spend_charge("a",2,5,group="g"))
    def test_reduce(self):
        s=m.CooldownState();s.activate("a",0,10)
        s.configure_charges("b",1);s.spend_charge("b",0,10)
        s.reduce("a",7,1);s.reduce("b",7,1)
        self.assertEqual(s.remaining("a",1),2)
        self.assertEqual(s.available_charges("b",3),1)
    def test_purge(self):
        s=m.CooldownState();s.activate("a",0,2)
        s.configure_charges("b",1);s.spend_charge("b",0,2)
        self.assertEqual(s.purge(2),2)
    def test_roundtrip(self):
        s=m.CooldownState();s.activate("a",1,5,group="g",group_duration=3)
        s.configure_charges("b",2);s.spend_charge("b",1,10)
        self.assertEqual(m.CooldownState.restore(s.snapshot()).snapshot(),s.snapshot())
    def test_invalid_snapshot(self):
        with self.assertRaises(ValueError):
            m.CooldownState.restore('{"schema":1}')
    def test_invalid_arguments(self):
        s=m.CooldownState()
        for call in [lambda:s.activate("a",0,-1),lambda:s.activate("",0,1),
                     lambda:s.configure_charges("a",0),lambda:s.remaining("a",-1),
                     lambda:s.activate("a",0,1,group_duration=2)]:
            with self.assertRaises(ValueError):call()
    def test_capacity_change(self):
        s=m.CooldownState();s.configure_charges("a",2)
        s.spend_charge("a",0,10);s.spend_charge("a",0,10)
        with self.assertRaises(ValueError):s.configure_charges("a",1)
if __name__=="__main__":unittest.main()
