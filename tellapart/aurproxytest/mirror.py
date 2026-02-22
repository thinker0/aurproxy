# Copyright 2015 TellApart, Inc.
import json
import os
import unittest
from tellapart.aurproxy.mirror import _FALLBACK_MSG, load_mirror_updater, MirrorUpdater
from tellapart.aurproxy.config import SourceEndpoint

def dummy_update(self, kill_running=True):
    self._needs_update = False

class MirrorUpdaterTests(unittest.TestCase):
    def test_mirror_updater(self):
        static_source_config = json.dumps({
            "source_class": "tellapart.aurproxy.source.StaticProxySource",
            "host": "127.0.0.1", "name": "base", "port": 80
        })
        # Use absolute path to avoid confusion
        template_path = os.path.join(os.path.join(os.path.dirname(__file__), '../../'), 'templates/gor/mirror.sh.template')
        mirror_updater = load_mirror_updater(source=static_source_config, ports='8080,8081', max_qps=100, max_update_frequency=15, command_template_path=template_path, pid_path='/tmp/gor-mirror.pid')
        
        mirror_updater.update = dummy_update.__get__(mirror_updater, MirrorUpdater)
        mirror_updater._template_path = template_path

        self.assertTrue(mirror_updater._should_update())
        mirror_updater.set_up()
        self.assertTrue('127.0.0.1:80' in mirror_updater._generate_command())
        mirror_updater._source.add(SourceEndpoint('127.0.0.1', 81))
        self.assertTrue(mirror_updater._should_update())
        mirror_updater.update()
        self.assertTrue('127.0.0.1:81' in mirror_updater._generate_command())
