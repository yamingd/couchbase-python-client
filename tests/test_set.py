#
# Copyright 2013, Couchbase, Inc.
# All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from time import sleep

from couchbase import FMT_JSON, FMT_PICKLE, FMT_BYTES, FMT_UTF8

from couchbase.exceptions import (KeyExistsError, ValueFormatError,
                                  ArgumentError, NotFoundError,
                                  NotStoredError)

from tests.base import CouchbaseTestCase


class ConnectionSetTest(CouchbaseTestCase):
    def setUp(self):
        super(ConnectionSetTest, self).setUp()
        self.cb = self.make_connection()

    def test_trivial_set(self):
        rv = self.cb.set(self.gen_key(), 'value1')
        self.assertTrue(rv)
        self.assertTrue(rv.cas > 0)
        rv = self.cb.set(self.gen_key(), 'value2')
        self.assertTrue(rv.cas > 0)

    def test_set_with_cas(self):
        key = self.gen_key('cas')
        rv1 = self.cb.set(key, 'value1')
        self.assertTrue(rv1.cas > 0)

        self.assertRaises(KeyExistsError, self.cb.set,
                          key, 'value2', cas=rv1.cas+1)

        rv2 = self.cb.set(key, 'value3', cas=rv1.cas)
        self.assertTrue(rv2.cas > 0)
        self.assertNotEqual(rv1.cas, rv2.cas)

        rv3 = self.cb.set(key, 'value4')
        self.assertTrue(rv3.cas > 0)
        self.assertNotEqual(rv3.cas, rv2.cas)
        self.assertNotEqual(rv3.cas, rv1.cas)

    def test_set_with_ttl(self):
        self.slowTest()
        key = self.gen_key('ttl')
        self.cb.set(key, 'value_ttl', ttl=2)
        rv = self.cb.get(key)
        self.assertEqual(rv.value, 'value_ttl')
        # Make sure the key expires
        sleep(3)
        self.assertRaises(NotFoundError, self.cb.get, key)

    def test_set_format(self):
        key = self.gen_key('set_format')
        rv1 = self.cb.set(key, {'some': 'value1'}, format=FMT_JSON)
        self.assertTrue(rv1.cas > 0)

        self.assertRaises(ValueFormatError, self.cb.set,
                          key, object(), format=FMT_JSON)

        rv3 = self.cb.set(key, {'some': 'value3'},
                           format=FMT_PICKLE)
        self.assertTrue(rv3.cas > 0)
        rv4 = self.cb.set(key, object(), format=FMT_PICKLE)
        self.assertTrue(rv4.cas > 0)

        self.assertRaises(ValueFormatError, self.cb.set,
                          key, {'some': 'value5'},
                          format=FMT_BYTES)
        self.assertRaises(ValueFormatError, self.cb.set,
                          key, { 'some' : 'value5.1'},
                          format=FMT_UTF8)

        rv6 = self.cb.set(key, b'some value6', format=FMT_BYTES)
        self.assertTrue(rv6.cas > 0)

        rv7 = self.cb.set(key, b"\x42".decode('utf-8'),
                          format=FMT_UTF8)
        self.assertTrue(rv7.success)


    def test_set_objects(self):
        key = self.gen_key('set_objects')
        for v in (None, False, True):
            for fmt in (FMT_JSON, FMT_PICKLE):
                rv = self.cb.set(key, v, format=fmt)
                self.assertTrue(rv.success)
                rv = self.cb.get(key)
                self.assertTrue(rv.success)
                self.assertEqual(rv.value, v)

    def test_multi_set(self):
        kv = self.gen_kv_dict(prefix='set_multi')
        rvs = self.cb.set_multi(kv)
        self.assertTrue(rvs.all_ok)
        for k, v in rvs.items():
            self.assertTrue(v.success)
            self.assertTrue(v.cas > 0)

        for k, v in rvs.items():
            self.assertTrue(k in rvs)
            self.assertTrue(rvs[k].success)

        self.assertRaises((ArgumentError,TypeError), self.cb.set_multi, kv,
                          cas = 123)

    def test_add(self):
        key = self.gen_key('add')
        self.cb.delete(key, quiet=True)
        rv = self.cb.add(key, "value")
        self.assertTrue(rv.cas)

        self.assertRaises(KeyExistsError,
                          self.cb.add, key, "value")

    def test_replace(self):
        key = self.gen_key('replace')
        rv = self.cb.set(key, "value")
        self.assertTrue(rv.success)

        rv = self.cb.replace(key, "value")
        self.assertTrue(rv.cas)

        rv = self.cb.replace(key, "value", cas=rv.cas)
        self.assertTrue(rv.cas)

        self.assertRaises(KeyExistsError,
                          self.cb.replace, key, "value", cas=0xdeadbeef)

        self.cb.delete(key, quiet=True)
        self.assertRaises(NotFoundError,
                          self.cb.replace, key, "value")


if __name__ == '__main__':
    unittest.main()
