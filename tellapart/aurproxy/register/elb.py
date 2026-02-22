# Copyright 2015 TellApart, Inc.
from tellapart.aurproxy.register.aws import AwsRegisterer
from tellapart.aurproxy.register.base import RegistrationAction, RegistrationActionReason
from tellapart.aurproxy.util import get_logger
logger = get_logger(__name__)

class BaseElbRegisterer(AwsRegisterer):
  def __init__(self, elb_names, region, access_key=None, secret_key=None):
    super(BaseElbRegisterer, self).__init__(region, access_key, secret_key)
    self._elb_names = elb_names.split(',')

  def _get_elb_instance_ids(self, elb_name):
    resp = self.conn.elb.describe_load_balancers(LoadBalancerNames=[elb_name])
    instances = resp['LoadBalancerDescriptions'][0].get('Instances', [])
    return [i['InstanceId'] for i in instances]

class ElbSelfRegisterer(BaseElbRegisterer):
  def add(self):
    instance_id = self.get_current_instance_id()
    for name in self._elb_names:
      if instance_id not in self._get_elb_instance_ids(name):
        self.record(name, instance_id, RegistrationAction.REGISTER, [RegistrationActionReason.NOT_YET_REGISTERED])
        self.conn.elb.register_instances_with_load_balancer(LoadBalancerName=name, Instances=[{'InstanceId': instance_id}])
      else:
        self.record(name, instance_id, RegistrationAction.NONE, [RegistrationActionReason.ALREADY_REGISTERED])
  def remove(self):
    instance_id = self.get_current_instance_id()
    for name in self._elb_names:
      if instance_id in self._get_elb_instance_ids(name):
        self.record(name, instance_id, RegistrationAction.REMOVE)
        self.conn.elb.deregister_instances_from_load_balancer(LoadBalancerName=name, Instances=[{'InstanceId': instance_id}])
      else:
        self.record(name, instance_id, RegistrationAction.NONE, [RegistrationActionReason.NOT_ALREADY_REGISTERED])

class ElbJobRegisterer(BaseElbRegisterer):
  def __init__(self, source, elb_names, region, remove_other_instances, access_key=None, secret_key=None, **kwargs):
    self._remove_other_instances = self.is_truish(remove_other_instances)
    self._source = source
    super(ElbJobRegisterer, self).__init__(elb_names, region, access_key, secret_key)
  def synchronize(self, write):
    hosts = self.get_job_hosts(self._source)
    instance_ids = self.get_instance_ids(hosts)
    for name in self._elb_names:
      elb_insts = self._get_elb_instance_ids(name)
      not_yet = set(instance_ids) - set(elb_insts)
      for inst in not_yet:
        self.record(name, inst, RegistrationAction.REGISTER, [RegistrationActionReason.NOT_YET_REGISTERED])
        if write: self.conn.elb.register_instances_with_load_balancer(LoadBalancerName=name, Instances=[{'InstanceId': inst}])
      if self._remove_other_instances:
        others = set(elb_insts) - set(instance_ids)
        for inst in others:
          self.record(name, inst, RegistrationAction.REMOVE, [RegistrationActionReason.NO_CORRESPONDING_TASK])
          if write: self.conn.elb.deregister_instances_from_load_balancer(LoadBalancerName=name, Instances=[{'InstanceId': inst}])
