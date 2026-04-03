# Copyright 2015 TellApart, Inc.

import json
import unittest

from tellapart.aurproxy.source import CuratorServiceDiscoverySource
from tellapart.aurproxy.source.sources.curator import Instance


class CuratorServiceDiscoverySourceTests(unittest.TestCase):
  def test_slug_is_stable_and_does_not_raise(self):
    source = CuratorServiceDiscoverySource(path='/services/test',
                                           zk_servers='127.0.0.1:2181',
                                           signal_update_fn=lambda: None,
                                           share_adjuster_factories=[])
    slug = source.slug
    self.assertTrue(isinstance(slug, str))
    self.assertTrue(len(slug) > 0)

  def test_instance_from_node_requires_port(self):
    with self.assertRaises(ValueError):
      Instance.from_node(member='member-1',
                         data=json.dumps({'address': '127.0.0.1'}))


if __name__ == '__main__':
  unittest.main()
