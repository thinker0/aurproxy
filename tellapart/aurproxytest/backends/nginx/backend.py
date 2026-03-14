# Copyright 2015 TellApart, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

import os
import signal
import tempfile
import unittest
from unittest.mock import patch

from tellapart.aurproxy.backends import NginxProxyBackend
from tellapart.aurproxytest.backends.backend import (
  build_proxy_configuration,
  ProxyBackendTstBase)


class NginxRestartTests(unittest.TestCase):

  def _make_backend(self, pid_path):
    config, scope = build_proxy_configuration(
      include_route_server=True,
      include_stream_server=False,
      include_route_share_adjusters=False,
      include_stream_share_adjusters=False)
    config['nginx_pid_path'] = pid_path
    return NginxProxyBackend(configuration=config,
                             signal_update_fn=scope.signal_update_fn)

  def test_restart_sends_sighup_to_pid_from_file(self):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pid', delete=False) as f:
      f.write('12345\n')
      pid_path = f.name
    try:
      backend = self._make_backend(pid_path)
      with patch('os.kill') as mock_kill:
        backend.restart()
        mock_kill.assert_called_once_with(12345, signal.SIGHUP)
    finally:
      os.unlink(pid_path)

  def test_restart_missing_pid_file_raises(self):
    backend = self._make_backend('/nonexistent/nginx.pid')
    with self.assertRaises(FileNotFoundError):
      backend.restart()

  def test_restart_invalid_pid_content_raises(self):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pid', delete=False) as f:
      f.write('not-a-pid\n')
      pid_path = f.name
    try:
      backend = self._make_backend(pid_path)
      with self.assertRaises(ValueError):
        backend.restart()
    finally:
      os.unlink(pid_path)

  def test_restart_process_not_found_raises(self):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pid', delete=False) as f:
      f.write('99999999\n')
      pid_path = f.name
    try:
      backend = self._make_backend(pid_path)
      with patch('os.kill', side_effect=ProcessLookupError):
        with self.assertRaises(ProcessLookupError):
          backend.restart()
    finally:
      os.unlink(pid_path)


class NginxProxyBackendTests(ProxyBackendTstBase):

  def test_nginx_proxy_backend(self):
    config, scope = build_proxy_configuration(include_route_server=True,
                                              include_stream_server=False,
                                              include_route_share_adjusters=True,
                                              include_stream_share_adjusters=False)

    backend = NginxProxyBackend(configuration=config,
                                signal_update_fn=scope.signal_update_fn)
    self.tst_proxy_backend(backend, scope)

if __name__ == '__main__':
    unittest.main()
