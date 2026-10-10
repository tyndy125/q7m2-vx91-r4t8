import unittest
from asset_manifest import validate_manifest


class ManifestTests(unittest.TestCase):
    def test_deterministic_order(self):
        self.assertEqual(validate_manifest({"z": "z.png", "a": "a.png"}),
                         (("a", "a.png"), ("z", "z.png")))

    def test_no_mutation(self):
        source = {"z": "z.png"}
        validate_manifest(source)
        self.assertEqual(source, {"z": "z.png"})

    def test_invalid_entries(self):
        for item in ({"": "x"}, {"x": ""}, {"x": None}):
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    validate_manifest(item)

    def test_reject_non_mapping(self):
        with self.assertRaises(TypeError):
            validate_manifest([])


if __name__ == "__main__":
    unittest.main()
