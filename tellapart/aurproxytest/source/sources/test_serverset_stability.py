import unittest
from unittest.mock import MagicMock, patch
from kazoo.client import KazooClient
from tellapart.aurproxy.source.sources.serverset import ServerSet

class TestServerSetStability(unittest.TestCase):
    def setUp(self):
        self.zk = MagicMock(spec=KazooClient)
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

from tellapart.aurproxy.source.sources.aurora import AuroraProxySource

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
            print(f'\nVerified ZK Path: {source._zk_path}')
