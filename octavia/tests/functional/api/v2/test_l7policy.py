#    Copyright 2016 Blue Box, an IBM Company
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


class TestL7Policy(base.BaseAPITest):

    root_tag = 'l7policy'
    root_tag_list = 'l7policies'
    root_tag_links = 'l7policies_links'

    def setUp(self):
        super(TestL7Policy, self).setUp()
        self.lb = self.create_load_balancer(uuidutils.generate_uuid())
        self.lb_id = self.lb.get('loadbalancer').get('id')
        self.set_lb_status(self.lb_id)
        self.listener = self.create_listener(
            constants.PROTOCOL_HTTP, 80, lb_id=self.lb_id)
        self.listener_id = self.listener.get('listener').get('id')
        self.set_lb_status(self.lb_id)
        self.pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN)
        self.pool_id = self.pool.get('pool').get('id')
        self.set_lb_status(self.lb_id)

    def test_get(self):
        api_l7policy = self.create_l7policy(
            self.listener_id,
            constants.L7POLICY_ACTION_REJECT).get(self.root_tag)
        response = self.get(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id'))).json.get(self.root_tag)
        self.assertEqual(api_l7policy, response)

    def test_bad_get(self):
        self.get(self.L7POLICY_PATH.format(
            l7policy_id=uuidutils.generate_uuid()), status=404)

    def test_get_all(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        policies = self.get(self.L7POLICIES_PATH).json.get(self.root_tag_list)
        self.assertIsInstance(policies, list)
        self.assertEqual(1, len(policies))
        self.assertEqual(api_l7policy.get('id'), policies[0].get('id'))

    def test_get_all_admin(self):
        project_id = uuidutils.generate_uuid()
        lb1 = self.create_load_balancer(uuidutils.generate_uuid(), name='lb1',
                                        project_id=project_id)
        lb1_id = lb1.get('loadbalancer').get('id')
        self.set_lb_status(lb1_id)
        listener1 = self.create_listener(constants.PROTOCOL_HTTP, 80,
                                         lb1_id)
        listener1_id = listener1.get('listener').get('id')
        self.set_lb_status(lb1_id)
        pool1 = self.create_pool(lb1_id, constants.PROTOCOL_HTTP,
                                 constants.LB_ALGORITHM_ROUND_ROBIN)
        pool1_id = pool1.get('pool').get('id')
        self.set_lb_status(lb1_id)
        api_l7p_a = self.create_l7policy(
            listener1_id,
            constants.L7POLICY_ACTION_REJECT).get(self.root_tag)
        self.set_lb_status(lb1_id)
        api_l7p_b = self.create_l7policy(
            listener1_id, constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            position=2, redirect_pool_id=pool1_id).get(self.root_tag)
        self.set_lb_status(lb1_id)
        api_l7p_c = self.create_l7policy(
            listener1_id, constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            position=3, redirect_url='http://localhost/').get(self.root_tag)
        self.set_lb_status(lb1_id)
        policies = self.get(self.L7POLICIES_PATH).json.get(self.root_tag_list)
        self.assertEqual(3, len(policies))
        policy_id_actions = [(p.get('id'), p.get('action')) for p in policies]
        self.assertIn((api_l7p_a.get('id'), api_l7p_a.get('action')),
                      policy_id_actions)
        self.assertIn((api_l7p_b.get('id'), api_l7p_b.get('action')),
                      policy_id_actions)
        self.assertIn((api_l7p_c.get('id'), api_l7p_c.get('action')),
                      policy_id_actions)

    def test_get_all_non_admin(self):
        project_id = uuidutils.generate_uuid()
        lb1 = self.create_load_balancer(uuidutils.generate_uuid(), name='lb1',
                                        project_id=project_id)
        lb1_id = lb1.get('loadbalancer').get('id')
        self.set_lb_status(lb1_id)
        listener1 = self.create_listener(constants.PROTOCOL_HTTP, 80,
                                         lb1_id)
        listener1_id = listener1.get('listener').get('id')
        self.set_lb_status(lb1_id)
        pool1 = self.create_pool(lb1_id, constants.PROTOCOL_HTTP,
                                 constants.LB_ALGORITHM_ROUND_ROBIN)
        pool1_id = pool1.get('pool').get('id')
        self.set_lb_status(lb1_id)
        self.create_l7policy(
            listener1_id,
            constants.L7POLICY_ACTION_REJECT).get(self.root_tag)
        self.set_lb_status(lb1_id)
        self.create_l7policy(
            listener1_id, constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            position=2, redirect_pool_id=pool1_id).get(self.root_tag)
        self.set_lb_status(lb1_id)
        api_l7p_c = self.create_l7policy(
            self.listener_id, constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            redirect_url='http://localhost/').get(self.root_tag)
        self.set_lb_status(lb1_id)

        auth_strategy = self.conf.conf.get('auth_strategy')
        self.conf.config(auth_strategy=constants.KEYSTONE)
        with mock.patch.object(octavia.common.context.Context, 'project_id',
                               api_l7p_c.get('project_id')):
            policies = self.get(
                self.L7POLICIES_PATH).json.get(self.root_tag_list)
        self.conf.config(auth_strategy=auth_strategy)

        self.assertEqual(1, len(policies))
        policy_id_actions = [(p.get('id'), p.get('action')) for p in policies]
        self.assertIn((api_l7p_c.get('id'), api_l7p_c.get('action')),
                      policy_id_actions)

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
        listener1 = self.create_listener(constants.PROTOCOL_HTTP, 80,
                                         lb1_id)
        listener1_id = listener1.get('listener').get('id')
        self.set_lb_status(lb1_id)
        listener2 = self.create_listener(constants.PROTOCOL_HTTP, 80,
                                         lb2_id)
        listener2_id = listener2.get('listener').get('id')
        self.set_lb_status(lb2_id)
        pool1 = self.create_pool(lb1_id, constants.PROTOCOL_HTTP,
                                 constants.LB_ALGORITHM_ROUND_ROBIN)
        pool1_id = pool1.get('pool').get('id')
        self.set_lb_status(lb1_id)
        api_l7p_a = self.create_l7policy(
            listener1_id,
            constants.L7POLICY_ACTION_REJECT).get(self.root_tag)
        self.set_lb_status(lb1_id)
        api_l7p_b = self.create_l7policy(
            listener1_id, constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            position=2, redirect_pool_id=pool1_id).get(self.root_tag)
        self.set_lb_status(lb1_id)
        api_l7p_c = self.create_l7policy(
            listener2_id, constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            redirect_url='http://localhost/').get(self.root_tag)
        self.set_lb_status(lb2_id)
        policies = self.get(
            self.L7POLICIES_PATH,
            params={'project_id': project1_id}).json.get(self.root_tag_list)

        self.assertEqual(2, len(policies))
        policy_id_actions = [(p.get('id'), p.get('action')) for p in policies]
        self.assertIn((api_l7p_a.get('id'), api_l7p_a.get('action')),
                      policy_id_actions)
        self.assertIn((api_l7p_b.get('id'), api_l7p_b.get('action')),
                      policy_id_actions)
        policies = self.get(
            self.L7POLICIES_PATH,
            params={'project_id': project2_id}).json.get(self.root_tag_list)
        self.assertEqual(1, len(policies))
        policy_id_actions = [(p.get('id'), p.get('action')) for p in policies]
        self.assertIn((api_l7p_c.get('id'), api_l7p_c.get('action')),
                      policy_id_actions)

    def test_empty_get_all(self):
        response = self.get(self.L7POLICIES_PATH).json.get(self.root_tag_list)
        self.assertIsInstance(response, list)
        self.assertEqual(0, len(response))

    def test_create_reject_policy(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.assertEqual(constants.L7POLICY_ACTION_REJECT,
                         api_l7policy['action'])
        self.assertEqual(1, api_l7policy['position'])
        self.assertIsNone(api_l7policy['redirect_pool_id'])
        self.assertIsNone(api_l7policy['redirect_url'])
        self.assertTrue(api_l7policy['admin_state_up'])
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            l7policy_prov_status=constants.PENDING_CREATE,
            l7policy_op_status=constants.OFFLINE)

    def test_create_redirect_to_pool(self):
        api_l7policy = self.create_l7policy(
            self.listener_id, constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            redirect_pool_id=self.pool_id).get(self.root_tag)
        self.assertEqual(constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
                         api_l7policy['action'])
        self.assertEqual(1, api_l7policy['position'])
        self.assertEqual(self.pool_id, api_l7policy['redirect_pool_id'])
        self.assertIsNone(api_l7policy['redirect_url'])
        self.assertTrue(api_l7policy['admin_state_up'])
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            l7policy_prov_status=constants.PENDING_CREATE,
            l7policy_op_status=constants.OFFLINE)

    def test_create_redirect_to_url(self):
        api_l7policy = self.create_l7policy(
            self.listener_id, constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            redirect_url='http://www.example.com').get(self.root_tag)
        self.assertEqual(constants.L7POLICY_ACTION_REDIRECT_TO_URL,
                         api_l7policy['action'])
        self.assertEqual(1, api_l7policy['position'])
        self.assertIsNone(api_l7policy.get('redirect_pool_id'))
        self.assertEqual('http://www.example.com',
                         api_l7policy['redirect_url'])
        self.assertTrue(api_l7policy['admin_state_up'])
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            l7policy_prov_status=constants.PENDING_CREATE,
            l7policy_op_status=constants.OFFLINE)

    def test_bad_create(self):
        l7policy = {'listener_id': self.listener_id,
                    'name': 'test1'}
        self.post(self.L7POLICIES_PATH, self._build_body(l7policy), status=400)

    def test_bad_create_redirect_to_pool(self):
        l7policy = {
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            'listener_id': self.listener_id,
            'redirect_pool_id': uuidutils.generate_uuid()}
        self.post(self.L7POLICIES_PATH, self._build_body(l7policy), status=404)

    def test_bad_create_redirect_to_url(self):
        l7policy = {'listener_id': self.listener_id,
                    'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
                    'redirect_url': 'bad url'}
        self.post(self.L7POLICIES_PATH, self._build_body(l7policy), status=400)

    def test_create_with_bad_handler(self):
        self.handler_mock().l7policy.create.side_effect = Exception()
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            l7policy_prov_status=constants.ERROR,
            l7policy_op_status=constants.OFFLINE)

    def test_create_over_quota(self):
        self.check_quota_met_true_mock.start()
        self.addCleanup(self.check_quota_met_true_mock.stop)
        l7policy = {'listener_id': self.listener_id,
                    'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
                    'redirect_url': 'http://a.com'}
        self.post(self.L7POLICIES_PATH, self._build_body(l7policy), status=403)

    def test_update(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        new_l7policy = {
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            'redirect_url': 'http://www.example.com'}
        response = self.put(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id')),
            self._build_body(new_l7policy)).json.get(self.root_tag)
        self.assertEqual(constants.L7POLICY_ACTION_REJECT,
                         response.get('action'))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            l7policy_prov_status=constants.PENDING_UPDATE)

    def test_bad_update(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        new_l7policy = {'listener_id': self.listener_id,
                        'action': 'bad action'}
        self.put(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id')),
            self._build_body(new_l7policy), status=400)

    def test_bad_update_redirect_to_pool(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        new_l7policy = {
            'listener_id': self.listener_id,
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            'redirect_pool_id': uuidutils.generate_uuid()}
        self.put(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id')),
            self._build_body(new_l7policy), status=400)

    def test_bad_update_redirect_to_url(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        new_l7policy = {
            'listener_id': self.listener_id,
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            'redirect_url': 'bad url'}
        self.put(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id')),
            self._build_body(new_l7policy), status=400)

    def test_update_with_bad_handler(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        new_l7policy = {
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            'redirect_url': 'http://www.example.com'}
        self.handler_mock().l7policy.update.side_effect = Exception()
        self.put(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id')),
            self._build_body(new_l7policy))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            l7policy_prov_status=constants.ERROR)

    def test_update_redirect_to_pool_bad_pool_id(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        new_l7policy = {'redirect_pool_id': uuidutils.generate_uuid()}
        self.put(self.L7POLICY_PATH.format(l7policy_id=api_l7policy.get('id')),
                 self._build_body(new_l7policy), status=404)

    def test_update_redirect_to_pool_minimal(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        new_l7policy = {'redirect_pool_id': self.pool_id}
        self.put(self.L7POLICY_PATH.format(l7policy_id=api_l7policy.get('id')),
                 self._build_body(new_l7policy))

    def test_update_redirect_to_url_bad_url(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        new_l7policy = {'listener_id': self.listener_id,
                        'redirect_url': 'bad-url'}
        self.put(self.L7POLICY_PATH.format(l7policy_id=api_l7policy.get('id')),
                 self._build_body(new_l7policy), status=400)

    def test_update_redirect_to_url_minimal(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        new_l7policy = {'redirect_url': 'http://www.example.com/'}
        self.put(self.L7POLICY_PATH.format(l7policy_id=api_l7policy.get('id')),
                 self._build_body(new_l7policy))

    def test_delete(self):
        api_l7policy = self.create_l7policy(
            self.listener_id,
            constants.L7POLICY_ACTION_REJECT).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        # Set status to ACTIVE/ONLINE because set_lb_status did it in the db
        api_l7policy['provisioning_status'] = constants.ACTIVE
        api_l7policy['operating_status'] = constants.ONLINE
        api_l7policy.pop('updated_at')

        response = self.get(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id'))).json.get(self.root_tag)
        response.pop('updated_at')
        self.assertEqual(api_l7policy, response)

        self.delete(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id')))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            lb_prov_status=constants.PENDING_UPDATE,
            listener_prov_status=constants.PENDING_UPDATE,
            l7policy_prov_status=constants.PENDING_DELETE)

    def test_bad_delete(self):
        self.delete(self.L7POLICY_PATH.format(
            l7policy_id=uuidutils.generate_uuid()), status=404)

    def test_delete_with_bad_handler(self):
        api_l7policy = self.create_l7policy(self.listener_id,
                                            constants.L7POLICY_ACTION_REJECT,
                                            ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        # Set status to ACTIVE/ONLINE because set_lb_status did it in the db
        api_l7policy['provisioning_status'] = constants.ACTIVE
        api_l7policy['operating_status'] = constants.ONLINE
        response = self.get(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id'))).json.get(self.root_tag)

        self.assertIsNone(api_l7policy.pop('updated_at'))
        self.assertIsNotNone(response.pop('updated_at'))
        self.assertEqual(api_l7policy, response)
        self.handler_mock().l7policy.delete.side_effect = Exception()
        self.delete(self.L7POLICY_PATH.format(
            l7policy_id=api_l7policy.get('id')))
        self.assert_correct_status(
            lb_id=self.lb_id, listener_id=self.listener_id,
            l7policy_id=api_l7policy.get('id'),
            l7policy_prov_status=constants.ERROR)

    def test_create_when_lb_pending_update(self):
        self.create_l7policy(self.listener_id,
                             constants.L7POLICY_ACTION_REJECT,
                             )
        self.set_lb_status(self.lb_id)
        self.put(self.LB_PATH.format(lb_id=self.lb_id),
                 body={'loadbalancer': {'name': 'test_name_change'}})
        new_l7policy = {
            'listener_id': self.listener_id,
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            'redirect_url': 'http://www.example.com'}
        self.post(self.L7POLICIES_PATH, body=self._build_body(new_l7policy),
                  status=409)

    def test_update_when_lb_pending_update(self):
        l7policy = self.create_l7policy(self.listener_id,
                                        constants.L7POLICY_ACTION_REJECT,
                                        ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.put(self.LB_PATH.format(lb_id=self.lb_id),
                 body={'loadbalancer': {'name': 'test_name_change'}})
        new_l7policy = {'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
                        'redirect_url': 'http://www.example.com'}
        self.put(self.L7POLICY_PATH.format(
                 l7policy_id=l7policy.get('id')),
                 body=self._build_body(new_l7policy), status=409)

    def test_delete_when_lb_pending_update(self):
        l7policy = self.create_l7policy(self.listener_id,
                                        constants.L7POLICY_ACTION_REJECT,
                                        ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.put(self.LB_PATH.format(lb_id=self.lb_id),
                 body={'loadbalancer': {'name': 'test_name_change'}})
        self.delete(self.L7POLICY_PATH.format(
                    l7policy_id=l7policy.get('id')),
                    status=409)

    def test_create_when_lb_pending_delete(self):
        self.delete(self.LB_PATH.format(lb_id=self.lb_id))
        new_l7policy = {
            'listener_id': self.listener_id,
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            'redirect_url': 'http://www.example.com'}
        self.post(self.L7POLICIES_PATH, body=self._build_body(new_l7policy),
                  status=409)

    def test_update_when_lb_pending_delete(self):
        l7policy = self.create_l7policy(self.listener_id,
                                        constants.L7POLICY_ACTION_REJECT,
                                        ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.delete(self.LB_PATH.format(lb_id=self.lb_id))
        new_l7policy = {
            'action': constants.L7POLICY_ACTION_REDIRECT_TO_URL,
            'redirect_url': 'http://www.example.com'}
        self.put(self.L7POLICY_PATH.format(
                 l7policy_id=l7policy.get('id')),
                 body=self._build_body(new_l7policy), status=409)

    def test_delete_when_lb_pending_delete(self):
        l7policy = self.create_l7policy(self.listener_id,
                                        constants.L7POLICY_ACTION_REJECT,
                                        ).get(self.root_tag)
        self.set_lb_status(self.lb_id)
        self.delete(self.LB_PATH.format(lb_id=self.lb_id))
        self.delete(self.L7POLICY_PATH.format(
                    l7policy_id=l7policy.get('id')),
                    status=409)
