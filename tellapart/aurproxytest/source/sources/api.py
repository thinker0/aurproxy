# Copyright 2015 TellApart, Inc.

import unittest
from datetime import (
  datetime,
  timedelta)

from flask import Flask

from tellapart.aurproxy.source.sources.api import ApiSource


class ApiSourceTests(unittest.TestCase):
  def setUp(self):
    self.source = ApiSource(name='test_api')
    self.app = Flask(__name__)
    self.app.register_blueprint(self.source.blueprint)
    self.client = self.app.test_client()

  def test_get_source_without_expiration(self):
    source_name = 'static_a'
    source_config = {
      'source_class': 'tellapart.aurproxy.source.StaticProxySource',
      'name': 's1',
      'host': '127.0.0.1',
      'port': 8080
    }
    put_resp = self.client.put('/api/source/test_api/source/{0}/'.format(source_name),
                               json={'source': source_config})
    self.assertIn(put_resp.status_code, [200, 201])

    get_resp = self.client.get('/api/source/test_api/source/{0}/'.format(source_name))
    self.assertEqual(get_resp.status_code, 200)
    payload = get_resp.get_json()
    self.assertEqual(payload['source'], source_config)
    self.assertIsNone(payload['expiration'])

  def test_get_source_with_expiration(self):
    source_name = 'static_b'
    source_config = {
      'source_class': 'tellapart.aurproxy.source.StaticProxySource',
      'name': 's2',
      'host': '127.0.0.1',
      'port': 8081
    }
    expiration = (datetime.now() + timedelta(minutes=2)).isoformat()
    put_resp = self.client.put('/api/source/test_api/source/{0}/'.format(source_name),
                               json={'source': source_config, 'expiration': expiration})
    self.assertIn(put_resp.status_code, [200, 201])

    get_resp = self.client.get('/api/source/test_api/source/{0}/'.format(source_name))
    self.assertEqual(get_resp.status_code, 200)
    payload = get_resp.get_json()
    self.assertEqual(payload['source'], source_config)
    self.assertTrue(isinstance(payload['expiration'], str))


if __name__ == '__main__':
  unittest.main()
