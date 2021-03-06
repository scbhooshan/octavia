#    Copyright 2014 Rackspace
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from oslo_utils import uuidutils

from octavia.common import constants
import octavia.common.context
from octavia.tests.functional.api.v2 import base

import testtools


class TestPool(base.BaseAPITest):

    root_tag = 'pool'
    root_tag_list = 'pools'
    root_tag_links = 'pools_links'

    def setUp(self):
        super(TestPool, self).setUp()

        self.lb = self.create_load_balancer(
            uuidutils.generate_uuid()).get('loadbalancer')
        self.lb_id = self.lb.get('id')

        self.set_lb_status(self.lb_id)

        self.listener = self.create_listener(
            constants.PROTOCOL_HTTP, 80,
            self.lb_id).get('listener')
        self.listener_id = self.listener.get('id')

        self.set_lb_status(self.lb_id)

    def test_get(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        # Set status to ACTIVE/ONLINE because set_lb_status did it in the db
        api_pool['provisioning_status'] = constants.ACTIVE
        api_pool['operating_status'] = constants.ONLINE
        api_pool.pop('updated_at')
        self.set_lb_status(lb_id=self.lb_id)
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        response.pop('updated_at')
        self.assertEqual(api_pool, response)

    def test_bad_get(self):
        self.get(self.POOL_PATH.format(pool_id=uuidutils.generate_uuid()),
                 status=404)

    def test_get_all(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        pools = self.get(self.POOLS_PATH).json.get(self.root_tag_list)
        self.assertIsInstance(pools, list)
        self.assertEqual(1, len(pools))
        self.assertEqual(api_pool.get('id'), pools[0].get('id'))

    def test_get_all_admin(self):
        project_id = uuidutils.generate_uuid()
        lb1 = self.create_load_balancer(uuidutils.generate_uuid(), name='lb1',
                                        project_id=project_id)
        lb1_id = lb1.get('loadbalancer').get('id')
        self.set_lb_status(lb1_id)
        pool1 = self.create_pool(
            lb1_id, constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb1_id)
        pool2 = self.create_pool(
            lb1_id, constants.PROTOCOL_HTTPS,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb1_id)
        pool3 = self.create_pool(
            lb1_id, constants.PROTOCOL_TCP,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb1_id)
        pools = self.get(self.POOLS_PATH).json.get(self.root_tag_list)
        self.assertEqual(3, len(pools))
        pool_id_protocols = [(p.get('id'), p.get('protocol')) for p in pools]
        self.assertIn((pool1.get('id'), pool1.get('protocol')),
                      pool_id_protocols)
        self.assertIn((pool2.get('id'), pool2.get('protocol')),
                      pool_id_protocols)
        self.assertIn((pool3.get('id'), pool3.get('protocol')),
                      pool_id_protocols)

    def test_get_all_non_admin(self):
        project_id = uuidutils.generate_uuid()
        lb1 = self.create_load_balancer(uuidutils.generate_uuid(), name='lb1',
                                        project_id=project_id)
        lb1_id = lb1.get('loadbalancer').get('id')
        self.set_lb_status(lb1_id)
        self.create_pool(
            lb1_id, constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb1_id)
        self.create_pool(
            lb1_id, constants.PROTOCOL_HTTPS,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb1_id)
        pool3 = self.create_pool(
            self.lb_id, constants.PROTOCOL_TCP,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(self.lb_id)

        auth_strategy = self.conf.conf.get('auth_strategy')
        self.conf.config(auth_strategy=constants.KEYSTONE)
        with mock.patch.object(octavia.common.context.Context, 'project_id',
                               pool3['project_id']):
            pools = self.get(self.POOLS_PATH).json.get(self.root_tag_list)
        self.conf.config(auth_strategy=auth_strategy)

        self.assertEqual(1, len(pools))
        pool_id_protocols = [(p.get('id'), p.get('protocol')) for p in pools]
        self.assertIn((pool3.get('id'), pool3.get('protocol')),
                      pool_id_protocols)

    def test_get_by_project_id(self):
        project1_id = uuidutils.generate_uuid()
        project2_id = uuidutils.generate_uuid()
        lb1 = self.create_load_balancer(uuidutils.generate_uuid(), name='lb1',
                                        project_id=project1_id)
        lb1_id = lb1.get('loadbalancer').get('id')
        self.set_lb_status(lb1_id)
        lb2 = self.create_load_balancer(uuidutils.generate_uuid(), name='lb2',
                                        project_id=project2_id)
        lb2_id = lb2.get('loadbalancer').get('id')
        self.set_lb_status(lb2_id)
        pool1 = self.create_pool(
            lb1_id, constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb1_id)
        pool2 = self.create_pool(
            lb1_id, constants.PROTOCOL_HTTPS,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb1_id)
        pool3 = self.create_pool(
            lb2_id, constants.PROTOCOL_TCP,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.set_lb_status(lb2_id)
        pools = self.get(
            self.POOLS_PATH,
            params={'project_id': project1_id}).json.get(self.root_tag_list)

        self.assertEqual(2, len(pools))
        pool_id_protocols = [(p.get('id'), p.get('protocol')) for p in pools]
        self.assertIn((pool1.get('id'), pool1.get('protocol')),
                      pool_id_protocols)
        self.assertIn((pool2.get('id'), pool2.get('protocol')),
                      pool_id_protocols)
        pools = self.get(
            self.POOLS_PATH,
            params={'project_id': project2_id}).json.get(self.root_tag_list)
        self.assertEqual(1, len(pools))
        pool_id_protocols = [(p.get('id'), p.get('protocol')) for p in pools]
        self.assertIn((pool3.get('id'), pool3.get('protocol')),
                      pool_id_protocols)

    def test_get_all_with_listener(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        response = self.get(self.POOLS_PATH).json.get(self.root_tag_list)
        self.assertIsInstance(response, list)
        self.assertEqual(1, len(response))
        self.assertEqual(api_pool.get('id'), response[0].get('id'))

    def test_empty_get_all(self):
        response = self.get(self.POOLS_PATH).json.get(self.root_tag_list)
        self.assertIsInstance(response, list)
        self.assertEqual(0, len(response))

    def test_create(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_CREATE,
            pool_op_status=constants.OFFLINE)
        self.set_lb_status(self.lb_id)
        self.assertEqual(constants.PROTOCOL_HTTP, api_pool.get('protocol'))
        self.assertEqual(constants.LB_ALGORITHM_ROUND_ROBIN,
                         api_pool.get('lb_algorithm'))
        self.assertIsNotNone(api_pool.get('created_at'))
        self.assertIsNone(api_pool.get('updated_at'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'))

    def test_create_with_proxy_protocol(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_PROXY,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_CREATE,
            pool_op_status=constants.OFFLINE)
        self.set_lb_status(self.lb_id)
        self.assertEqual(constants.PROTOCOL_PROXY, api_pool.get('protocol'))
        self.assertEqual(constants.LB_ALGORITHM_ROUND_ROBIN,
                         api_pool.get('lb_algorithm'))
        self.assertIsNotNone(api_pool.get('created_at'))
        self.assertIsNone(api_pool.get('updated_at'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'))

    def test_create_sans_listener(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN).get(self.root_tag)
        self.assertEqual(constants.PROTOCOL_HTTP, api_pool.get('protocol'))
        self.assertEqual(constants.LB_ALGORITHM_ROUND_ROBIN,
                         api_pool.get('lb_algorithm'))
        # Make sure listener status is unchanged, but LB status is changed.
        # LB should still be locked even with pool and subordinate object
        # updates.
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.ACTIVE,
            pool_prov_status=constants.PENDING_CREATE,
            pool_op_status=constants.OFFLINE)

    def test_create_sans_loadbalancer_id(self):
        api_pool = self.create_pool(
            None,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.assertEqual(constants.PROTOCOL_HTTP, api_pool.get('protocol'))
        self.assertEqual(constants.LB_ALGORITHM_ROUND_ROBIN,
                         api_pool.get('lb_algorithm'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_CREATE,
            pool_op_status=constants.OFFLINE)

    def test_create_with_listener_id_in_pool_dict(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_CREATE,
            pool_op_status=constants.OFFLINE)
        self.set_lb_status(self.lb_id)
        self.assertEqual(constants.PROTOCOL_HTTP, api_pool.get('protocol'))
        self.assertEqual(constants.LB_ALGORITHM_ROUND_ROBIN,
                         api_pool.get('lb_algorithm'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'))

    def test_create_with_project_id(self):
        optionals = {
            'listener_id': self.listener_id,
            'project_id': self.project_id}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            **optionals).get(self.root_tag)
        self.assertEqual(self.project_id, api_pool.get('tenant_id'))

    def test_bad_create(self):
        pool = {'name': 'test1'}
        self.post(self.POOLS_PATH, self._build_body(pool), status=400)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id)

    def test_create_with_listener_with_default_pool_id_set(self):
        self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id)
        self.set_lb_status(self.lb_id)
        lb_pool = {
            'loadbalancer_id': self.lb_id,
            'listener_id': self.listener_id,
            'protocol': constants.PROTOCOL_HTTP,
            'lb_algorithm': constants.LB_ALGORITHM_ROUND_ROBIN,
            'project_id': self.project_id}
        self.post(self.POOLS_PATH, self._build_body(lb_pool), status=409)

    def test_create_bad_protocol(self):
        lb_pool = {
            'loadbalancer_id': self.lb_id,
            'protocol': 'STUPID_PROTOCOL',
            'lb_algorithm': constants.LB_ALGORITHM_ROUND_ROBIN}
        self.post(self.POOLS_PATH, self._build_body(lb_pool), status=400)

    def test_create_with_bad_handler(self):
        self.handler_mock().pool.create.side_effect = Exception()
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.ACTIVE,
            listener_prov_status=constants.ACTIVE,
            pool_prov_status=constants.ERROR,
            pool_op_status=constants.OFFLINE)

    def test_create_over_quota(self):
        self.check_quota_met_true_mock.start()
        self.addCleanup(self.check_quota_met_true_mock.stop)
        lb_pool = {
            'loadbalancer_id': self.lb_id,
            'protocol': constants.PROTOCOL_HTTP,
            'lb_algorithm': constants.LB_ALGORITHM_ROUND_ROBIN,
            'project_id': self.project_id}
        self.post(self.POOLS_PATH, self._build_body(lb_pool), status=403)

    def test_update(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        new_pool = {'name': 'new_name'}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_UPDATE)
        self.set_lb_status(self.lb_id)
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        self.assertNotEqual('new_name', response.get('name'))
        self.assertIsNotNone(response.get('created_at'))
        self.assertIsNotNone(response.get('updated_at'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=response.get('id'))

    def test_bad_update(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        new_pool = {'enabled': 'one'}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool), status=400)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'))

    def test_update_with_bad_handler(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        new_pool = {'name': 'new_name'}
        self.handler_mock().pool.update.side_effect = Exception()
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            pool_prov_status=constants.ERROR)

    def test_delete(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        # Set status to ACTIVE/ONLINE because set_lb_status did it in the db
        api_pool['provisioning_status'] = constants.ACTIVE
        api_pool['operating_status'] = constants.ONLINE
        api_pool.pop('updated_at')

        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        response.pop('updated_at')
        self.assertEqual(api_pool, response)

        self.delete(self.POOL_PATH.format(pool_id=api_pool.get('id')))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_DELETE)

    def test_bad_delete(self):
        self.delete(self.POOL_PATH.format(
            pool_id=uuidutils.generate_uuid()), status=404)

    def test_delete_with_l7policy(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.create_l7policy(
            self.listener_id,
            constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            redirect_pool_id=api_pool.get('id'))
        self.set_lb_status(self.lb_id)
        self.delete(self.POOL_PATH.format(
            pool_id=api_pool.get('id')), status=409)

    def test_delete_with_bad_handler(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        # Set status to ACTIVE/ONLINE because set_lb_status did it in the db
        api_pool['provisioning_status'] = constants.ACTIVE
        api_pool['operating_status'] = constants.ONLINE
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)

        self.assertIsNone(api_pool.pop('updated_at'))
        self.assertIsNotNone(response.pop('updated_at'))
        self.assertEqual(api_pool, response)
        self.handler_mock().pool.delete.side_effect = Exception()
        self.delete(self.POOL_PATH.format(pool_id=api_pool.get('id')))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            pool_prov_status=constants.ERROR)

    def test_create_with_session_persistence(self):
        sp = {"type": constants.SESSION_PERSISTENCE_HTTP_COOKIE,
              "cookie_name": "test_cookie_name"}
        optionals = {"listener_id": self.listener_id,
                     "session_persistence": sp}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            **optionals).get(self.root_tag)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_CREATE,
            pool_op_status=constants.OFFLINE)
        self.set_lb_status(self.lb_id)
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        sess_p = response.get('session_persistence')
        self.assertIsNotNone(sess_p)
        self.assertEqual(constants.SESSION_PERSISTENCE_HTTP_COOKIE,
                         sess_p.get('type'))
        self.assertEqual('test_cookie_name', sess_p.get('cookie_name'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'))

    def test_create_with_bad_session_persistence(self):
        sp = {"type": "persistence_type",
              "cookie_name": "test_cookie_name"}
        lb_pool = {
            'loadbalancer_id': self.lb_id,
            'listener_id': self.listener_id,
            'protocol': constants.PROTOCOL_HTTP,
            'lb_algorithm': constants.LB_ALGORITHM_ROUND_ROBIN,
            'session_persistence': sp}
        self.post(self.POOLS_PATH, self._build_body(lb_pool), status=400)

    def test_add_session_persistence(self):
        sp = {"type": constants.SESSION_PERSISTENCE_HTTP_COOKIE,
              "cookie_name": "test_cookie_name"}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        new_pool = {'session_persistence': sp}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool))
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        self.assertNotEqual(sp, response.get('session_persistence'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_UPDATE)

    def test_update_session_persistence(self):
        sp = {"type": constants.SESSION_PERSISTENCE_HTTP_COOKIE,
              "cookie_name": "test_cookie_name"}
        optionals = {"listener_id": self.listener_id,
                     "session_persistence": sp}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            **optionals).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        sess_p = response.get('session_persistence')
        sess_p['cookie_name'] = None
        sess_p['type'] = constants.SESSION_PERSISTENCE_SOURCE_IP
        new_pool = {'session_persistence': sess_p}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool))
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        self.assertNotEqual(sess_p, response.get('session_persistence'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_UPDATE)

    def test_update_preserve_session_persistence(self):
        sp = {"type": constants.SESSION_PERSISTENCE_HTTP_COOKIE,
              "cookie_name": "test_cookie_name"}
        optionals = {"listener_id": self.listener_id,
                     "name": "name", "session_persistence": sp}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            **optionals).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        new_pool = {'name': 'update_name'}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool))
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        self.assertEqual(sp, response.get('session_persistence'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_UPDATE)

    @testtools.skip('This test should pass with a validation layer')
    def test_update_bad_session_persistence(self):
        sp = {"type": constants.SESSION_PERSISTENCE_HTTP_COOKIE,
              "cookie_name": "test_cookie_name"}
        optionals = {"listener_id": self.listener_id,
                     "session_persistence": sp}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            **optionals).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        response = self.get(self.POOL_PATH.format(
            pool_id=api_pool.get('id'))).json.get(self.root_tag)
        sess_p = response.get('session_persistence')
        sess_p['type'] = 'persistence_type'
        new_pool = {'session_persistence': sess_p}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool), status=400)

    def test_delete_with_session_persistence(self):
        sp = {"type": constants.SESSION_PERSISTENCE_HTTP_COOKIE,
              "cookie_name": "test_cookie_name"}
        optionals = {"listener_id": self.listener_id,
                     "session_persistence": sp}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            **optionals).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        self.delete(self.POOL_PATH.format(pool_id=api_pool.get('id')))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_DELETE)

    def test_delete_session_persistence(self):
        sp = {"type": constants.SESSION_PERSISTENCE_HTTP_COOKIE,
              "cookie_name": "test_cookie_name"}
        optionals = {"listener_id": self.listener_id,
                     "session_persistence": sp}
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            **optionals).get(self.root_tag)
        self.set_lb_status(lb_id=self.lb_id)
        new_sp = {"pool": {"session_persistence": None}}
        response = self.put(self.POOL_PATH.format(
            pool_id=api_pool.get('id')), new_sp).json.get(self.root_tag)
        self.assertIsNotNone(response.get('session_persistence'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            pool_id=api_pool.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            pool_prov_status=constants.PENDING_UPDATE)

    def test_create_when_lb_pending_update(self):
        self.put(self.LB_PATH.format(lb_id=self.lb_id),
                 {'loadbalancer': {'name': 'test_name_change'}})
        lb_pool = {
            'loadbalancer_id': self.lb_id,
            'listener_id': self.listener_id,
            'protocol': constants.PROTOCOL_HTTP,
            'lb_algorithm': constants.LB_ALGORITHM_ROUND_ROBIN,
            'project_id': self.project_id}
        self.post(self.POOLS_PATH, self._build_body(lb_pool), status=409)

    def test_update_when_lb_pending_update(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.put(self.LB_PATH.format(lb_id=self.lb_id),
                 {'loadbalancer': {'name': 'test_name_change'}})
        new_pool = {'admin_state_up': False}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool), status=409)

    def test_delete_when_lb_pending_update(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.put(self.LB_PATH.format(lb_id=self.lb_id),
                 {"loadbalancer": {'name': 'test_name_change'}})
        self.delete(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                    status=409)

    def test_create_when_lb_pending_delete(self):
        self.delete(self.LB_PATH.format(lb_id=self.lb_id))
        new_pool = {
            'loadbalancer_id': self.lb_id,
            'listener_id': self.listener_id,
            'protocol': constants.PROTOCOL_HTTP,
            'lb_algorithm': constants.LB_ALGORITHM_ROUND_ROBIN,
            'project_id': self.project_id}
        self.post(self.POOLS_PATH, self._build_body(new_pool), status=409)

    def test_update_when_lb_pending_delete(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.delete(self.LB_PATH.format(lb_id=self.lb_id))
        new_pool = {'admin_state_up': False}
        self.put(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                 self._build_body(new_pool), status=409)

    def test_delete_when_lb_pending_delete(self):
        api_pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN,
            listener_id=self.listener_id).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.delete(self.LB_PATH.format(lb_id=self.lb_id))
        self.delete(self.POOL_PATH.format(pool_id=api_pool.get('id')),
                    status=409)
