import unittest
from unittest.mock import patch, MagicMock
from tellapart.aurproxy.backends.nginx.metrics import NginxProxyMetricsPublisher

class NginxProxyMetricsResourceTests(unittest.TestCase):
  @patch('tellapart.aurproxy.backends.nginx.metrics.urllib.request.urlopen')
  def test_metrics_urlopen_closed_on_success(self, mock_urlopen):
    # Mock response
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.readlines.return_value = [
      b"Active connections: 10",
      b"server accepts handled requests",
      b" 100 100 100",
      b"Reading: 0 Writing: 1 Waiting: 9"
    ]
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    publisher = NginxProxyMetricsPublisher(port=80)
    publisher.publish()

    # Verify context manager exited
    mock_response.__exit__.assert_called_once()
