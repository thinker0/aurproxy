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

"""Basic Flask HTTP modules for composing larger applications.
"""

__copyright__ = 'Copyright (C) 2015 TellApart, Inc. All Rights Reserved.'

import os
import socket

from flask import (
  Blueprint,
  Response)
import flask_restful
from prometheus_client.registry import REGISTRY
from prometheus_client.utils import floatToGoString

from tellapart.aurproxy.app import lifecycle
from tellapart.aurproxy.metrics.store import root_metric_store

# Define a standard blueprint for lifecycle management endpoints
lifecycle_blueprint = Blueprint('lifecycle', __name__)
_bp = flask_restful.Api(lifecycle_blueprint)

hostname = socket.gethostname()
environ = os.environ.get('AURPROXY_ENVIRON', 'devel')
domain = os.environ.get('AURPROXY_DOMAIN', 'localhost')


@_bp.resource('/quitquitquit')
class QuitQuitQuit(flask_restful.Resource):
  def post(self):
    lifecycle.execute_shutdown_handlers()
    return 'OK', 200


@_bp.resource('/abortabortabort')
class AbortAbortAbort(flask_restful.Resource):
  def post(self):
    lifecycle.execute_shutdown_handlers()
    return 'OK', 200


@_bp.resource('/health')
class Health(flask_restful.Resource):
  def get(self):
    status, message = lifecycle.check_health()
    if not status:
      # Still respond with 200, otherwise Aurora UI doesn't show failure text.
      return Response(response='Health checks failed: %s' % message)

    return Response(response='OK')


@_bp.resource('/metrics.json')
class MetricsJson(flask_restful.Resource):
  def get(self):
    metrics = root_metric_store().get_metrics()
    ordered_metrics = sorted(metrics, key=lambda metric: metric.name)

    return dict((m.name, m.value()) for m in ordered_metrics)


@_bp.resource('/metrics')
class Metrics(flask_restful.Resource):
  def get(self):
    """Returns the metrics from the registry in latest text format as a string."""

    def sample_line(prefix, line):
      line.labels['host'] = hostname
      line.labels['env'] = environ
      line.labels['domain'] = domain
      labelstr = '{{{0}}}'.format(','.join(
        ['{0}="{1}"'.format(
          k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
          for k, v in sorted(line.labels.items())]))
      timestamp = ''
      if line.timestamp is not None:
        # Convert to milliseconds.
        timestamp = ' {0:d}'.format(int(float(line.timestamp) * 1000))
      if line.value != 0:
        return '{0}{1}{2} {3}{4}\n'.format(
          prefix, line.name, labelstr, floatToGoString(line.value), timestamp)
      else:
        return ''

    prefix = 'aurproxy_'
    output = []
    for metric in REGISTRY.collect():
      try:
        mname = prefix + metric.name
        mtype = metric.type
        # Munging from OpenMetrics into Prometheus format.
        if mtype == 'counter':
          mname = mname + '_total'
        elif mtype == 'info':
          mname = mname + '_info'
          mtype = 'gauge'
        elif mtype == 'stateset':
          mtype = 'gauge'
        elif mtype == 'gaugehistogram':
          # A gauge histogram is really a gauge,
          # but this captures the strucutre better.
          mtype = 'histogram'
        elif mtype == 'unknown':
          mtype = 'untyped'

        output.append('# HELP {0} {1}\n'.format(
          mname, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
        output.append('# TYPE {0} {1}\n'.format(mname, mtype))

        om_samples = {}
        for s in metric.samples:
          for suffix in ['_created', '_gsum', '_gcount']:
            if s.name == metric.name + suffix:
              # OpenMetrics specific sample, put in a gauge at the end.
              om_samples.setdefault(suffix, []).append(sample_line(prefix, s))
              break
          else:
            output.append(sample_line(prefix, s))
      except Exception as exception:
        exception.args = (exception.args or ('',)) + (metric,)
        raise

      for suffix, lines in sorted(om_samples.items()):
        output.append('# TYPE {0}{1} gauge\n'.format(metric.name, suffix))
        output.extend(lines)
    msg = ''.join(output).encode('utf-8')
    return Response(msg, mimetype='text/plain; version=0.0.4; charset=utf-8')
