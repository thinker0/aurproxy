# Copyright 2015 TellApart, Inc.
import boto3
from collections import namedtuple
from tellapart.aurproxy.register.aws import AwsRegisterer
from tellapart.aurproxy.register.base import RegistrationAction, RegistrationActionReason
from tellapart.aurproxy.util import get_logger
logger = get_logger(__name__)

Route53Record = namedtuple('Route53Record', ('domain', 'hostname', 'ttl'))

class BaseRoute53Registerer(AwsRegisterer):
  def __init__(self, domain, hosted_zone_id, region, ttl, access_key=None, secret_key=None):
    super(BaseRoute53Registerer, self).__init__(region, access_key, secret_key)
    self._domain = domain.rstrip('.') + '.'
    self._hosted_zone_id = hosted_zone_id
    self._ttl = int(ttl)

  def _get_records(self):
    resp = self.conn.route53.list_resource_record_sets(HostedZoneId=self._hosted_zone_id, StartRecordName=self._domain, StartRecordType='CNAME')
    return [r for r in resp.get('ResourceRecordSets', []) if r['Name'] == self._domain and r['Type'] == 'CNAME']

  def _update(self, action, hostname, ttl):
    self.conn.route53.change_resource_record_sets(
      HostedZoneId=self._hosted_zone_id,
      ChangeBatch={'Changes': [{'Action': action, 'ResourceRecordSet': {
        'Name': self._domain, 'Type': 'CNAME', 'TTL': ttl, 'SetIdentifier': hostname, 'Weight': 1,
        'ResourceRecords': [{'Value': hostname}]
      }}]}
    )

  def _register(self, hostname):
    records = self._get_records()
    if hostname not in [r.get('SetIdentifier') for r in records]:
      ttl = records[0]['TTL'] if records else self._ttl
      self._update('CREATE', hostname, ttl)
      return True
    return False

  def _unregister(self, hostname):
    records = [r for r in self._get_records() if r.get('SetIdentifier') == hostname]
    if records:
      self._update('DELETE', hostname, records[0]['TTL'])
      return True
    return False

class Route53SelfRegisterer(BaseRoute53Registerer):
  def add(self):
    host = self.get_public_hostname()
    if self._register(host): self.record(self._domain, host, RegistrationAction.REGISTER)
  def remove(self):
    host = self.get_public_hostname()
    if self._unregister(host): self.record(self._domain, host, RegistrationAction.REMOVE)

class Route53JobRegisterer(BaseRoute53Registerer):
  def __init__(self, source, domain, hosted_zone_id, region, ttl, remove_other_instances, **kwargs):
    self._source = source
    self._remove_other_instances = self.is_truish(remove_other_instances)
    super(Route53JobRegisterer, self).__init__(domain, hosted_zone_id, region, ttl, **kwargs)
  def synchronize(self, write):
    announced = self.get_job_hosts(self._source)
    registered = [r.get('SetIdentifier') for r in self._get_records()]
    for h in (set(announced) - set(registered)):
      self.record(self._domain, h, RegistrationAction.REGISTER)
      if write: self._register(h)
    if self._remove_other_instances:
      for h in (set(registered) - set(announced)):
        self.record(self._domain, h, RegistrationAction.REMOVE)
        if write: self._unregister(h)
