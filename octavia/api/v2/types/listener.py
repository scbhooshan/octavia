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

from wsme import types as wtypes

from octavia.api.common import types
from octavia.api.v2.types import l7policy
from octavia.api.v2.types import pool
from octavia.common import constants


class BaseListenerType(types.BaseType):
    _type_to_model_map = {'admin_state_up': 'enabled',
                          'default_tls_container_ref': 'tls_certificate_id'}


class MinimalLoadBalancer(types.BaseType):
    id = wtypes.wsattr(wtypes.UuidType())


class MinimalL7Policy(types.BaseType):
    id = wtypes.wsattr(wtypes.UuidType())


class ListenerResponse(BaseListenerType):
    """Defines which attributes are to be shown on any response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    description = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    admin_state_up = wtypes.wsattr(bool)
    protocol = wtypes.wsattr(wtypes.text)
    protocol_port = wtypes.wsattr(wtypes.IntegerType())
    connection_limit = wtypes.wsattr(wtypes.IntegerType())
    default_tls_container_ref = wtypes.wsattr(wtypes.StringType())
    sni_container_refs = [wtypes.StringType()]
    # TODO(johnsom) Remove after deprecation (R series)
    project_id = wtypes.wsattr(wtypes.StringType())
    # TODO(johnsom) Remove after deprecation (R series)
    tenant_id = wtypes.wsattr(wtypes.StringType())
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    l7policies = wtypes.wsattr([MinimalL7Policy])
    insert_headers = wtypes.wsattr(wtypes.DictType(str, str))
    created_at = wtypes.wsattr(wtypes.datetime.datetime)
    updated_at = wtypes.wsattr(wtypes.datetime.datetime)
    loadbalancers = wtypes.wsattr([MinimalLoadBalancer])

    @classmethod
    def from_data_model(cls, data_model, children=False):
        listener = super(ListenerResponse, cls).from_data_model(
            data_model, children=children)
        listener.tenant_id = data_model.project_id

        listener.sni_container_refs = [
            sni_c.tls_container_id for sni_c in data_model.sni_containers]
        listener.loadbalancers = [
            MinimalLoadBalancer.from_data_model(data_model.load_balancer)]
        listener.l7policies = [
            MinimalL7Policy.from_data_model(i) for i in data_model.l7policies]

        if not listener.description:
            listener.description = ""
        if not listener.name:
            listener.name = ""

        return listener


class ListenerRootResponse(types.BaseType):
    listener = wtypes.wsattr(ListenerResponse)


class ListenersRootResponse(types.BaseType):
    listeners = wtypes.wsattr([ListenerResponse])


class ListenerPOST(BaseListenerType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    protocol = wtypes.wsattr(wtypes.Enum(str, *constants.SUPPORTED_PROTOCOLS),
                             mandatory=True)
    protocol_port = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_PORT_NUMBER,
                           maximum=constants.MAX_PORT_NUMBER), mandatory=True)
    connection_limit = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_CONNECTION_LIMIT), default=-1)
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    sni_container_refs = [wtypes.StringType(max_length=255)]
    # TODO(johnsom) Remove after deprecation (R series)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    # TODO(johnsom) Remove after deprecation (R series)
    tenant_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    default_pool = wtypes.wsattr(pool.PoolPOST)
    l7policies = wtypes.wsattr([l7policy.L7PolicyPOST], default=[])
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))
    loadbalancer_id = wtypes.wsattr(wtypes.UuidType(), mandatory=True)


class ListenerRootPOST(types.BaseType):
    listener = wtypes.wsattr(ListenerPOST)


class ListenerPUT(BaseListenerType):
    """Defines attributes that are acceptable of a PUT request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool)
    connection_limit = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_CONNECTION_LIMIT))
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    sni_container_refs = [wtypes.StringType(max_length=255)]
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))


class ListenerRootPUT(types.BaseType):
    listener = wtypes.wsattr(ListenerPUT)
