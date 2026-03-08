# Copyright 2015 TellApart, Inc.
import posixpath
import gevent
from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError
from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.protocol.states import ZnodeStat
from kazoo.retry import KazooRetry
import mox3.mox as mox
import unittest
from tellapart.aurproxy.source.sources import serverset

TEST_PATH = '/test/path'
TEST_NODE = 'member_0001'
TEST_NODE_2 = 'member_0002'
TEST_NODE_DATA = '{ "status": "ALIVE", "additionalEndpoints": {"aurora": {"host": "192.168.33.7", "port": 15508}, "http": {"host": "192.168.33.7", "port": 15508}}, "serviceEndpoint": {"host": "192.168.33.7", "port": 15508}, "shard": 0}'
TEST_NODE_PATH = posixpath.join(TEST_PATH, TEST_NODE)
TEST_NODE_2_DATA = '{ "status": "ALIVE", "additionalEndpoints": {"aurora": {"host": "192.168.33.7", "port": 15508}, "http": {"host": "192.168.33.8", "port": 15508}}, "serviceEndpoint": {"host": "192.168.33.8", "port": 15508}, "shard": 0}'
TEST_NODE_2_PATH = posixpath.join(TEST_PATH, TEST_NODE_2)

def getMockServerSet(smox):
    listeners = []
    def add_listener(listener):
        listeners.append(listener)
    zk = smox.CreateMock(KazooClient)
    zk.connected = True
    zk.handler = SequentialGeventHandler()
    zk.retry = KazooRetry()
    mock_stat = smox.CreateMock(ZnodeStat)
    mock_stat.mzxid = 1
    zk.exists(TEST_PATH).AndReturn(True)
    zk.add_listener(mox.IgnoreArg()).WithSideEffects(add_listener)
    zk.get(TEST_PATH, mox.IgnoreArg()).AndReturn((1, mock_stat))
    zk.add_listener(mox.IgnoreArg()).WithSideEffects(add_listener)
    return zk

@unittest.skip("Flaky with gevent and mox3")
class ZooKeeperTestCase(mox.MoxTestBase):
    def testNodeDoesntExist(self):
        zk = self.mox.CreateMock(KazooClient)
        zk.connected = True
        zk.get_children(TEST_PATH).AndRaise(NoNodeError)
        self.mox.ReplayAll()
        ss = serverset.ServerSet(zk, TEST_PATH, None, None)
        members = ss.get_members()
        self.assertEqual(0, len(members))

    def testNodeJoinAndLeave(self):
        nodes = set()
        children_listeners = []
        def on_join(node): nodes.add(node.service_endpoint)
        def on_leave(node): nodes.remove(node.service_endpoint)
        zk = getMockServerSet(self.mox)
        def get_children(path, listener): children_listeners.append(listener)
        
        # Initial scan
        zk.get_children(TEST_PATH, mox.IgnoreArg()).WithSideEffects(get_children).AndReturn([TEST_NODE])
        zk.get(TEST_NODE_PATH).AndReturn((TEST_NODE_DATA,))
        
        # Call 1 -> Add node
        zk.get_children(TEST_PATH, mox.IgnoreArg()).AndReturn([TEST_NODE, TEST_NODE_2])
        zk.get(TEST_NODE_2_PATH).AndReturn((TEST_NODE_2_DATA,))
        
        # Call 2 -> Remove node
        zk.get_children(TEST_PATH, mox.IgnoreArg()).AndReturn([TEST_NODE_2])
        
        self.mox.ReplayAll()
        serverset.ServerSet(zk, TEST_PATH, on_join, on_leave)
        gevent.sleep(0.1) # Wait for initial join
        
        # Trigger Join
        children_listeners[0](type("Event", (object,), {"type": "NONE"})())
        gevent.sleep(0.1)
        self.assertEqual(len(nodes), 2)
        
        # Trigger Leave
        children_listeners[0](type("Event", (object,), {"type": "NONE"})())
        gevent.sleep(0.1)
        self.assertEqual(len(nodes), 1)

    def testNodeLeavingWhileInitializing(self):
        zk = getMockServerSet(self.mox)
        initial_nodes = [TEST_NODE, TEST_NODE_2]
        def remove_a_node(listener):
            initial_nodes.remove(TEST_NODE)
            listener(type("Event", (object,), {"type": "NONE"})())
        def get_children(_, listener):
            gevent.spawn_later(0.01, remove_a_node, listener)
        def noop(_): pass

        zk.get_children(TEST_PATH, mox.IgnoreArg()).WithSideEffects(get_children).AndReturn(initial_nodes)
        zk.get(TEST_NODE_2_PATH).AndReturn((TEST_NODE_2_DATA,))
        
        # When notification worker kicks in after gevent.sleep
        zk.get(TEST_NODE_PATH).AndReturn((TEST_NODE_DATA,))
        
        # list(ss) call
        zk.get_children(TEST_PATH).AndReturn([TEST_NODE_2])
        zk.get(TEST_NODE_2_PATH).AndReturn((TEST_NODE_2_DATA,))

        self.mox.ReplayAll()
        ss = serverset.ServerSet(zk, TEST_PATH, noop, noop)
        gevent.sleep(0.2)
        
        members = list(ss)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].name, TEST_NODE_2)
