import unittest
from unittest.mock import patch, MagicMock
from urllib import error
from tellapart.aurproxy.share.adjusters.health import HttpHealthCheckShareAdjuster
from tellapart.aurproxy.config import SourceEndpoint

class HttpHealthCheckResourceTests(unittest.TestCase):
  def setUp(self):
    self.endpoint = MagicMock(spec=SourceEndpoint)
    self.endpoint.host = '127.0.0.1'
    self.endpoint.port = '8080'
    self.endpoint.context = {}
    self.signal_update_fn = MagicMock()

  @patch('tellapart.aurproxy.share.adjusters.health.request.urlopen')
  def test_urlopen_closed_on_success(self, mock_urlopen):
    # Mock response context manager
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    adjuster = HttpHealthCheckShareAdjuster(
      self.endpoint,
      self.signal_update_fn,
      interval=1000
    )
    adjuster._check()

    # Verify context manager exited
    mock_response.__exit__.assert_called_once()

  @patch('tellapart.aurproxy.share.adjusters.health.request.urlopen')
  def test_urlopen_closed_on_http_error(self, mock_urlopen):
    # Mock HTTPError
    http_error = error.HTTPError('http://127.0.0.1/health', 500, 'Internal Server Error', {}, None)
    http_error.close = MagicMock()
    mock_urlopen.side_effect = http_error

    adjuster = HttpHealthCheckShareAdjuster(
      self.endpoint,
      self.signal_update_fn,
      interval=1000
    )
    adjuster._check()

    # Verify HTTPError response was closed
    http_error.close.assert_called_once()
