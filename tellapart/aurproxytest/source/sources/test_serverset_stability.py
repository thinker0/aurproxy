import unittest
from unittest.mock import MagicMock, patch

try:
  from kazoo.client import KazooClient
  _KAZOO_SPEC = KazooClient
except ImportError:
  _KAZOO_SPEC = None

from tellapart.aurproxy.source.sources.aurora import AuroraProxySource
from tellapart.aurproxy.source.sources.serverset import (
  Endpoint,
  Member,
  ServerSet,
  ServerSetSource)


class TestServerSetStability(unittest.TestCase):

  def setUp(self):
    self.zk = MagicMock(spec=_KAZOO_SPEC)
    self.zk.connected = True
    self.path = '/test/path'
    with patch('tellapart.aurproxy.source.sources.serverset.DataWatch'):
      with patch('tellapart.aurproxy.source.sources.serverset.gevent.spawn'):
        self.ss = ServerSet(self.zk, self.path)

  def test_data_changed_restarts_watch(self):
    self.ss._watching = True
    self.ss._data_changed(None, None)
    assert self.ss._watching is False
    with patch.object(self.ss, '_begin_watch') as mock_begin:
      self.ss._data_changed('data', MagicMock())
      mock_begin.assert_called_once()

  def test_begin_watch_idempotency(self):
    with patch('tellapart.aurproxy.source.sources.serverset.ChildrenWatch') as mock_cw:
      self.ss._watching = False
      self.ss._begin_watch()
      assert self.ss._watching is True
      assert mock_cw.call_count == 1
      self.ss._begin_watch()
      assert mock_cw.call_count == 1

  def test_integration_flow(self):
    with patch('tellapart.aurproxy.source.sources.serverset.ChildrenWatch') as mock_cw:
      self.ss._watching = False
      self.ss._data_changed('data', MagicMock())
      assert self.ss._watching is True
      assert mock_cw.call_count == 1
      self.ss._data_changed(None, None)
      assert self.ss._watching is False
      self.ss._data_changed('data', MagicMock())
      assert self.ss._watching is True
      assert mock_cw.call_count == 2

  def test_safe_zk_node_to_member_records_parse_error(self):
    self.ss._member_factory = MagicMock(side_effect=ValueError('bad node'))
    self.ss._get_info = MagicMock(return_value='{}')
    with patch('tellapart.aurproxy.source.sources.serverset.METRIC_SERVERSET_MEMBER_PARSE_ERROR.inc') as metric_inc:
      member = self.ss._safe_zk_node_to_member('member-1')
    self.assertIsNone(member)
    metric_inc.assert_called_once()


class TestServerSetSourceMetrics(unittest.TestCase):
  def test_join_and_leave_record_metrics(self):
    source = ServerSetSource(path='/test/path',
                             zk_servers='127.0.0.1:2181',
                             signal_update_fn=lambda: None,
                             share_adjuster_factories=[])
    member = Member(member='m1',
                    service_endpoint=Endpoint('127.0.0.1', 8080),
                    additional_endpoints={},
                    shard=0,
                    status='ALIVE')
    join_cb = source._on_join('/test/path')
    leave_cb = source._on_leave('/test/path')

    with patch('tellapart.aurproxy.source.sources.serverset.METRIC_SOURCE_DISCOVERY_JOINED.labels') as joined_labels:
      join_cb(member)
      joined_labels.assert_called_with(source_type='serversetsource')

    with patch('tellapart.aurproxy.source.sources.serverset.METRIC_SOURCE_DISCOVERY_LEFT.labels') as left_labels:
      leave_cb(member)
      left_labels.assert_called_with(source_type='serversetsource')


class TestAuroraSourcePath(unittest.TestCase):

  def test_path_construction_with_custom_announcer(self):
    """Verify that the ZK path is constructed correctly when announcer_serverset_path is 'aurora'."""
    config = {
      'role': 'www',
      'environment': 'devel',
      'job': 'heron-tracker',
      'zk_servers': 'localhost:2181',
      'announcer_serverset_path': 'aurora'
    }
    # Mock KazooClient.start() to prevent actual ZK connection
    with patch('tellapart.aurproxy.source.sources.serverset.KazooClient'):
      source = AuroraProxySource(signal_update_fn=lambda: None, **config)
      # Expected path: /aurora/www/devel/heron-tracker
      expected_path = '/aurora/www/devel/heron-tracker'
      assert source._zk_path == expected_path
