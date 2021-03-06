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

from tempest import config
from tempest import exceptions
from tempest.services.boto.clients import APIClientEC2
from tempest.services.boto.clients import ObjectClientS3
from tempest.services.compute.json.extensions_client import \
    ExtensionsClientJSON
from tempest.services.compute.json.flavors_client import FlavorsClientJSON
from tempest.services.compute.json.floating_ips_client import \
    FloatingIPsClientJSON
from tempest.services.compute.json.images_client import ImagesClientJSON
from tempest.services.compute.json.limits_client import LimitsClientJSON
from tempest.services.compute.json.servers_client import ServersClientJSON
from tempest.services.compute.json.security_groups_client import \
    SecurityGroupsClientJSON
from tempest.services.compute.json.keypairs_client import KeyPairsClientJSON
from tempest.services.compute.json.quotas_client import QuotasClient
from tempest.services.compute.json.volumes_extensions_client import \
    VolumesExtensionsClientJSON
from tempest.services.compute.json.console_output_client import \
    ConsoleOutputsClientJSON
from tempest.services.compute.xml.extensions_client import ExtensionsClientXML
from tempest.services.compute.xml.flavors_client import FlavorsClientXML
from tempest.services.compute.xml.floating_ips_client import \
    FloatingIPsClientXML
from tempest.services.compute.xml.images_client import ImagesClientXML
from tempest.services.compute.xml.keypairs_client import KeyPairsClientXML
from tempest.services.compute.xml.limits_client import LimitsClientXML
from tempest.services.compute.xml.security_groups_client \
    import SecurityGroupsClientXML
from tempest.services.compute.xml.servers_client import ServersClientXML
from tempest.services.compute.xml.volumes_extensions_client import \
    VolumesExtensionsClientXML
from tempest.services.compute.xml.console_output_client import \
    ConsoleOutputsClientXML
from tempest.services.identity.json.admin_client import AdminClientJSON
from tempest.services.identity.json.admin_client import TokenClientJSON
from tempest.services.identity.xml.admin_client import AdminClientXML
from tempest.services.identity.xml.admin_client import TokenClientXML
from tempest.services.image import service as image_service
from tempest.services.network.json.network_client import NetworkClient
from tempest.services.object_storage.account_client import AccountClient
from tempest.services.object_storage.container_client import ContainerClient
from tempest.services.object_storage.object_client import ObjectClient
from tempest.services.volume.json.volumes_client import VolumesClientJSON
from tempest.services.volume.xml.volumes_client import VolumesClientXML
from tempest.services.object_storage.object_client import \
    ObjectClientCustomizedHeader

LOG = logging.getLogger(__name__)

IMAGES_CLIENTS = {
    "json": ImagesClientJSON,
    "xml": ImagesClientXML,
}

KEYPAIRS_CLIENTS = {
    "json": KeyPairsClientJSON,
    "xml": KeyPairsClientXML,
}

SERVERS_CLIENTS = {
    "json": ServersClientJSON,
    "xml": ServersClientXML,
}

LIMITS_CLIENTS = {
    "json": LimitsClientJSON,
    "xml": LimitsClientXML,
}

FLAVORS_CLIENTS = {
    "json": FlavorsClientJSON,
    "xml": FlavorsClientXML
}

EXTENSIONS_CLIENTS = {
    "json": ExtensionsClientJSON,
    "xml": ExtensionsClientXML
}

VOLUMES_EXTENSIONS_CLIENTS = {
    "json": VolumesExtensionsClientJSON,
    "xml": VolumesExtensionsClientXML,
}

FLOAT_CLIENTS = {
    "json": FloatingIPsClientJSON,
    "xml": FloatingIPsClientXML,
}

VOLUMES_CLIENTS = {
    "json": VolumesClientJSON,
    "xml": VolumesClientXML,
}

ADMIN_CLIENT = {
    "json": AdminClientJSON,
    "xml": AdminClientXML,
}

TOKEN_CLIENT = {
    "json": TokenClientJSON,
    "xml": TokenClientXML,
}

SECURITY_GROUPS_CLIENT = {
    "json": SecurityGroupsClientJSON,
    "xml": SecurityGroupsClientXML,
}

CONSOLE_OUTPUT_CLIENT = {
    "json": ConsoleOutputsClientJSON,
    "xml": ConsoleOutputsClientXML,
}


class Manager(object):

    """
    Top level manager for OpenStack Compute clients
    """

    def __init__(self, username=None, password=None, tenant_name=None,
                 interface='json'):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name is used.

        :param username: Override of the username
        :param password: Override of the password
        :param tenant_name: Override of the tenant name
        """
        self.config = config.TempestConfig()

        # If no creds are provided, we fall back on the defaults
        # in the config file for the Compute API.
        self.username = username or self.config.compute.username
        self.password = password or self.config.compute.password
        self.tenant_name = tenant_name or self.config.compute.tenant_name

        if None in (self.username, self.password, self.tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        self.auth_url = self.config.identity.auth_url

        if self.config.identity.strategy == 'keystone':
            client_args = (self.config, self.username, self.password,
                           self.auth_url, self.tenant_name)
        else:
            client_args = (self.config, self.username, self.password,
                           self.auth_url)

        try:
            self.servers_client = SERVERS_CLIENTS[interface](*client_args)
            self.limits_client = LIMITS_CLIENTS[interface](*client_args)
            self.images_client = IMAGES_CLIENTS[interface](*client_args)
            self.keypairs_client = KEYPAIRS_CLIENTS[interface](*client_args)
            self.flavors_client = FLAVORS_CLIENTS[interface](*client_args)
            ext_cli = EXTENSIONS_CLIENTS[interface](*client_args)
            self.extensions_client = ext_cli
            vol_ext_cli = VOLUMES_EXTENSIONS_CLIENTS[interface](*client_args)
            self.volumes_extensions_client = vol_ext_cli
            self.floating_ips_client = FLOAT_CLIENTS[interface](*client_args)
            self.volumes_client = VOLUMES_CLIENTS[interface](*client_args)
            self.admin_client = ADMIN_CLIENT[interface](*client_args)
            self.token_client = TOKEN_CLIENT[interface](self.config)
            self.security_groups_client = \
                SECURITY_GROUPS_CLIENT[interface](*client_args)
            self.console_outputs_client = \
                CONSOLE_OUTPUT_CLIENT[interface](*client_args)
        except KeyError:
            msg = "Unsupported interface type `%s'" % interface
            raise exceptions.InvalidConfiguration(msg)
        self.quotas_client = QuotasClient(*client_args)
        self.network_client = NetworkClient(*client_args)
        self.account_client = AccountClient(*client_args)
        self.container_client = ContainerClient(*client_args)
        self.object_client = ObjectClient(*client_args)
        self.ec2api_client = APIClientEC2(*client_args)
        self.s3_client = ObjectClientS3(*client_args)
        self.custom_object_client = ObjectClientCustomizedHeader(*client_args)


class AltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = config.TempestConfig()
        super(AltManager, self).__init__(conf.compute.alt_username,
                                         conf.compute.alt_password,
                                         conf.compute.alt_tenant_name)


class AdminManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        conf = config.TempestConfig()
        super(AdminManager, self).__init__(conf.compute_admin.username,
                                           conf.compute_admin.password,
                                           conf.compute_admin.tenant_name,
                                           interface=interface)


class ServiceManager(object):

    """
    Top-level object housing clients for OpenStack APIs
    """

    def __init__(self):
        self.config = config.TempestConfig()
        self.services = {}
        self.services['image'] = image_service.Service(self.config)
        self.images = self.services['image']


class IdentityManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        conf = config.TempestConfig()
        super(IdentityManager, self).__init__(conf.identity_admin.username,
                                              conf.identity_admin.password,
                                              conf.identity_admin.tenant_name,
                                              interface)


class IdentityNaManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        conf = config.TempestConfig()
        super(IdentityNaManager, self).__init__(conf.compute.username,
                                                conf.compute.password,
                                                conf.compute.tenant_name,
                                                interface)
