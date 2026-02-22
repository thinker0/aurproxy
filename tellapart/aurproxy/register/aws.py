# Copyright 2015 TellApart, Inc.
import boto3
import requests
from tellapart.aurproxy.register.base import BaseRegisterer

_CONN_MGR = None
_AWS_METADATA_URI = 'http://169.254.169.254/latest/meta-data/{0}'

class AwsRegisterer(BaseRegisterer):
  def __init__(self, region, access_key=None, secret_key=None):
    self._region = region
    self._access_key = access_key
    self._secret_key = secret_key

  @property
  def conn(self):
    global _CONN_MGR
    if not _CONN_MGR:
      _CONN_MGR = Boto3ConnectionManager(self._region, self._access_key, self._secret_key)
    return _CONN_MGR

  def get_current_instance_id(self):
    return self._get_instance_metadata('instance-id')

  def get_public_hostname(self):
    return self._get_instance_metadata('public-hostname')

  def _get_instance_metadata(self, identifier):
    url = _AWS_METADATA_URI.format(identifier)
    try:
      resp = requests.get(url, timeout=2)
      return resp.text if resp.status_code == 200 else None
    except:
      return None

  def get_instance_ids(self, hosts):
    return [self.get_instance_id(host) for host in hosts]

  def get_instance_id(self, hostname):
    response = self.conn.ec2.describe_instances(
        Filters=[{'Name': 'dns-name', 'Values': [hostname]}]
    )
    for res in response.get('Reservations', []):
      for inst in res.get('Instances', []):
        return inst['InstanceId']
    return None

class Boto3ConnectionManager(object):
  def __init__(self, region, access_key=None, secret_key=None):
    self._session = boto3.Session(region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
  @property
  def ec2(self):
    if not hasattr(self, '_ec2'): self._ec2 = self._session.client('ec2')
    return self._ec2
  @property
  def elb(self):
    if not hasattr(self, '_elb'): self._elb = self._session.client('elb')
    return self._elb
  @property
  def elbv2(self):
    if not hasattr(self, '_elbv2'): self._elbv2 = self._session.client('elbv2')
    return self._elbv2
  @property
  def route53(self):
    if not hasattr(self, '_route53'): self._route53 = self._session.client('route53')
    return self._route53
