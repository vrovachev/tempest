# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
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

import logging
import time
import nose

import unittest2 as unittest
from common.isolated_creds import get_isolated_creds_common

from tempest import config
from tempest import openstack
from tempest.common.utils.data_utils import rand_name

__all__ = ['BaseComputeTest', 'BaseComputeTestJSON', 'BaseComputeTestXML',
           'BaseComputeAdminTestJSON', 'BaseComputeAdminTestXML']

LOG = logging.getLogger(__name__)


class BaseCompTest(unittest.TestCase):

    """Base test case class for all Compute API tests"""

    @classmethod
    def setUpClass(cls):
        cls.config = config.TempestConfig()
        cls.isolated_creds = []

        if cls.config.compute.allow_tenant_isolation:
            creds = cls._get_isolated_creds()
            username, tenant_name, password = creds
            os = openstack.Manager(username=username,
                                   password=password,
                                   tenant_name=tenant_name,
                                   interface=cls._interface)
        else:
            os = openstack.Manager(interface=cls._interface)

        cls.os = os
        cls.servers_client = os.servers_client
        cls.flavors_client = os.flavors_client
        cls.images_client = os.images_client
        cls.extensions_client = os.extensions_client
        cls.floating_ips_client = os.floating_ips_client
        cls.keypairs_client = os.keypairs_client
        cls.security_groups_client = os.security_groups_client
        cls.console_outputs_client = os.console_outputs_client
        cls.limits_client = os.limits_client
        cls.volumes_extensions_client = os.volumes_extensions_client
        cls.volumes_client = os.volumes_client
        cls.build_interval = cls.config.compute.build_interval
        cls.build_timeout = cls.config.compute.build_timeout
        cls.ssh_user = cls.config.compute.ssh_user
        cls.image_ref = cls.config.compute.image_ref
        cls.image_ref_alt = cls.config.compute.image_ref_alt
        cls.flavor_ref = cls.config.compute.flavor_ref
        cls.flavor_ref_alt = cls.config.compute.flavor_ref_alt
        cls.servers = []

    @classmethod
    def _get_identity_admin_client(cls):
        """
        Returns an instance of the Identity Admin API client
        """
        os = openstack.IdentityManager(interface=cls._interface)
        admin_client = os.admin_client
        return admin_client

    @classmethod
    def _get_isolated_creds(cls):
        """
        Creates a new set of user/tenant/password credentials for a
        **regular** user of the Compute API so that a test case can
        operate in an isolated tenant container.
        """
        return get_isolated_creds_common(cls, LOG)

    @classmethod
    def clear_isolated_creds(cls):
        if not cls.isolated_creds:
            pass
        admin_client = cls._get_identity_admin_client()

        for user, tenant in cls.isolated_creds:
            admin_client.delete_user(user['id'])
            admin_client.delete_tenant(tenant['id'])

    @classmethod
    def clear_servers(cls):
        for server in cls.servers:
            try:
                cls.servers_client.delete_server(server['id'])
            except Exception:
                pass

        for server in cls.servers:
            try:
                cls.servers_client.wait_for_server_termination(server['id'])
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        cls.clear_servers()
        cls.clear_isolated_creds()

    @classmethod
    def create_server(cls, image_id=None):
        """Wrapper utility that returns a test server"""
        server_name = rand_name(cls.__name__ + "-instance")
        flavor = cls.flavor_ref
        if not image_id:
            image_id = cls.image_ref

        resp, server = cls.servers_client.create_server(
                                                server_name, image_id, flavor)
        cls.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        cls.servers.append(server)
        return server

    def wait_for(self, condition):
        """Repeatedly calls condition() until a timeout"""
        start_time = int(time.time())
        while True:
            try:
                condition()
            except:
                pass
            else:
                return
            if int(time.time()) - start_time >= self.build_timeout:
                condition()
                return
            time.sleep(self.build_interval)


class BaseComputeTestJSON(BaseCompTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(BaseComputeTestJSON, cls).setUpClass()

# NOTE(danms): For transition, keep the old name active as JSON
BaseComputeTest = BaseComputeTestJSON


class BaseComputeTestXML(BaseCompTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(BaseComputeTestXML, cls).setUpClass()


class BaseComputeAdminTest(unittest.TestCase):

    """Base test case class for all Compute Admin API tests"""

    @classmethod
    def setUpClass(cls):
        cls.config = config.TempestConfig()
        cls.admin_username = cls.config.compute_admin.username
        cls.admin_password = cls.config.compute_admin.password
        cls.admin_tenant = cls.config.compute_admin.tenant_name

        if not cls.admin_username and cls.admin_password and cls.admin_tenant:
            msg = ("Missing Compute Admin API credentials "
                   "in configuration.")
            raise nose.SkipTest(msg)

        cls.os = openstack.AdminManager(interface=cls._interface)


class BaseComputeAdminTestJSON(BaseComputeAdminTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(BaseComputeAdminTestJSON, cls).setUpClass()


class BaseComputeAdminTestXML(BaseComputeAdminTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(BaseComputeAdminTestXML, cls).setUpClass()
