# Copyright 2015 TellApart, Inc.

import os
import unittest

from tellapart.aurproxy import command
from tellapart.aurproxy.backends.nginx.backend import _DEFAULT_TEMPLATE_LOC


class CommandPathTests(unittest.TestCase):
  def test_default_mirror_template_path_exists(self):
    self.assertTrue(os.path.isfile(command._MIRROR_COMMAND_TEMPLATE_PATH))

  def test_default_replay_template_path_exists(self):
    self.assertTrue(os.path.isfile(command._REPLAY_COMMAND_TEMPLATE_PATH))

  def test_default_nginx_template_path_exists(self):
    self.assertTrue(os.path.isfile(_DEFAULT_TEMPLATE_LOC))


if __name__ == '__main__':
  unittest.main()
