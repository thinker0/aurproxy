# Copyright 2015 TellApart, Inc.
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from tellapart.aurproxy.mirror import (
  MirrorUpdater,
  load_mirror_updater)
from tellapart.aurproxy.source import StaticProxySource

class MirrorUpdaterTests(unittest.TestCase):
  def setUp(self):
    self.template_path = os.path.join(
      os.path.dirname(__file__),
      '../../templates/gor/mirror.sh.template')
    self.source = StaticProxySource(signal_update_fn=lambda: None,
                                    share_adjuster_factories=[],
                                    name='base',
                                    host='127.0.0.1',
                                    port=80)
    self.updater = MirrorUpdater(source=self.source,
                                 ports=[8080],
                                 max_qps=100,
                                 max_update_frequency=15,
                                 command_template_path=self.template_path,
                                 pid_path='/tmp/gor-mirror.pid',
                                 command_path='/tmp/aurproxy-mirror-test.sh')

  def test_load_mirror_updater(self):
    source_config = json.dumps({
      'source_class': 'tellapart.aurproxy.source.StaticProxySource',
      'host': '127.0.0.1',
      'name': 'base',
      'port': 80
    })
    updater = load_mirror_updater(source=source_config,
                                  ports='8080,8081',
                                  max_qps=100,
                                  max_update_frequency=15,
                                  command_template_path=self.template_path,
                                  pid_path='/tmp/gor-mirror.pid')
    self.assertIsInstance(updater, MirrorUpdater)

  def test_load_mirror_updater_accepts_zero_max_qps(self):
    source_config = json.dumps({
      'source_class': 'tellapart.aurproxy.source.StaticProxySource',
      'host': '127.0.0.1',
      'name': 'base',
      'port': 80
    })
    updater = load_mirror_updater(source=source_config,
                                  ports='8080,8081',
                                  max_qps=0,
                                  max_update_frequency=15,
                                  command_template_path=self.template_path,
                                  pid_path='/tmp/gor-mirror.pid')
    self.assertIsInstance(updater, MirrorUpdater)

  def test_update_returns_success_when_kill_running_is_false(self):
    with patch.object(self.updater, '_update_command', return_value=True):
      self.assertTrue(self.updater._update('echo ok',
                                           '/tmp/aurproxy-mirror-test.sh',
                                           kill_running=False))

  def test_set_up_does_not_schedule_periodic_update(self):
    with patch('tellapart.aurproxy.mirror.spawn_later') as mock_spawn:
      with patch.object(self.updater, '_update_command', return_value=True):
        self.updater.set_up()
    mock_spawn.assert_not_called()

  def test_update_schedules_next_run_when_enabled(self):
    with patch('tellapart.aurproxy.mirror.spawn_later') as mock_spawn:
      with patch.object(self.updater, '_update', return_value=True):
        self.updater.update(kill_running=False, schedule_next=True)
    mock_spawn.assert_called_once()

  def test_update_records_skipped_metric_when_no_update_needed(self):
    self.updater._needs_update = False
    with patch('tellapart.aurproxy.mirror.METRIC_MIRROR_UPDATE_SKIPPED.inc') as skipped_inc:
      with patch('tellapart.aurproxy.mirror.spawn_later'):
        self.updater.update(kill_running=False, schedule_next=True)
    skipped_inc.assert_called_once()

  def test_generate_command_records_fallback_metric_without_endpoints(self):
    with patch('tellapart.aurproxy.mirror.METRIC_MIRROR_FALLBACK_COMMAND_USED.inc') as fallback_inc:
      self.updater._generate_command()
    fallback_inc.assert_called_once()

  def test_kill_running_process_marks_success(self):
    self.updater._get_pid = MagicMock(return_value=1234)
    proc = MagicMock()
    proc.cmdline.return_value = ['/opt/go/bin/gor', '--input-raw', ':8080']
    with patch('tellapart.aurproxy.mirror.psutil.Process', return_value=proc):
      self.assertTrue(self.updater._kill_running())
    proc.kill.assert_called_once()
