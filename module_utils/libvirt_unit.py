import unittest

import roles.libvirt.module_utils.libvirt_utils as util


class TestUtilMethods(unittest.TestCase):

    def test_to_bytes(self):
        self.assertEqual(util.to_bytes(1, 'b'), 1)
        self.assertEqual(util.to_bytes(1, 'byte'), 1)
        self.assertEqual(util.to_bytes(1, 'bytes'), 1)
        self.assertEqual(util.to_bytes(1, 'kb'), 1000)
        self.assertEqual(util.to_bytes(1, 'kib'), 1024)
        self.assertEqual(util.to_bytes(1, 'mb'), 1000 ** 2)
        self.assertEqual(util.to_bytes(1, 'mib'), 1024 ** 2)
        self.assertEqual(util.to_bytes(1, 'gb'), 1000 ** 3)
        self.assertEqual(util.to_bytes(1, 'gib'), 1024 ** 3)
        self.assertEqual(util.to_bytes(1, 'tb'), 1000 ** 4)
        self.assertEqual(util.to_bytes(1, 'tib'), 1024 ** 4)
        self.assertEqual(util.to_bytes(1, 'pb'), 1000 ** 5)
        self.assertEqual(util.to_bytes(1, 'pib'), 1024 ** 5)
        self.assertEqual(util.to_bytes(1, 'eb'), 1000 ** 6)
        self.assertEqual(util.to_bytes(1, 'eib'), 1024 ** 6)

        self.assertRaises(ValueError, util.to_bytes, 1, 'x')
        self.assertRaises(ValueError, util.to_bytes, 1, 'KxB')
        self.assertRaises(ValueError, util.to_bytes, 1, 'KiX')
        self.assertRaises(ValueError, util.to_bytes, 1, 'by')

    def test_compare(self):
        self.assertTrue(util.compare(None, None, 'domain')[0])
        self.assertTrue(util.compare(False, False, 'domain')[0])
        self.assertTrue(util.compare(True, True, 'domain')[0])
        self.assertTrue(util.compare(0, 0, 'domain')[0])
        self.assertTrue(util.compare(1, 1, 'domain')[0])
        self.assertTrue(util.compare('a', 'a', 'domain')[0])
        self.assertTrue(util.compare({}, {}, 'domain')[0])
        self.assertTrue(util.compare([], [], 'domain')[0])
        self.assertTrue(util.compare([None], [None], 'domain')[0])
        self.assertTrue(util.compare([False], [False], 'domain')[0])
        self.assertTrue(util.compare([True], [True], 'domain')[0])
        self.assertTrue(util.compare([0], [0], 'domain')[0])
        self.assertTrue(util.compare(['a'], ['a'], 'domain')[0])
        self.assertTrue(util.compare([{}], [{}], 'domain')[0])
        self.assertTrue(util.compare([[]], [[]], 'domain')[0])

        self.assertTrue(util.compare({'a': None}, {'a': None}, 'domain')[0])
        self.assertTrue(util.compare({'a': False}, {'a': False}, 'domain')[0])
        self.assertTrue(util.compare({'a': True}, {'a': True}, 'domain')[0])
        self.assertTrue(util.compare({'a': {}}, {'a': {}}, 'domain')[0])
        self.assertTrue(util.compare({'a': []}, {'a': []}, 'domain')[0])
        self.assertTrue(util.compare({'a': ['a', 'b', 'c']}, {'a': ['a', 'b', 'c']}, 'domain')[0])
        self.assertTrue(util.compare({'a': [{'a': 1}]}, {'a': [{'a': 1}]}, 'domain')[0])
        self.assertTrue(util.compare({'a': {'a': 1, 'b': 2, 'c': 3}}, {'a': {'c': 3, 'a': 1, 'b': 2}}, 'domain')[0])
        self.assertTrue(util.compare({'a': {'a': 1, 'b': ['c', 'd']}}, {'a': {'a': 1, 'b': ['c', 'd']}}, 'domain')[0])

        self.assertTrue(util.compare({'a': {'_unit': 'KB', '__value': 1}}, {'a': {'_unit': 'b', '__value': 1000}}, 'domain')[0])
        self.assertTrue(util.compare({'a': {'_unit': 'KiB', '__value': 1}}, {'a': {'_unit': 'b', '__value': 1024}}, 'domain')[0])
        self.assertTrue(util.compare({'a': {'_unit': 'KiB', '__value': 1024}}, {'a': {'_unit': 'MiB', '__value': 1}}, 'domain')[0])

    def test_validate(self):
        xml = '''
        <domain type='kvm'>
          <name>test</name>
          <memory unit='GiB'>1</memory>
          <os>
            <type arch='x86_64' machine='pc-i440fx-bionic'>hvm</type>
          </os>
        </domain>
        '''
        self.assertTrue(util.validate(xml))


if __name__ == '__main__':
    unittest.main()
