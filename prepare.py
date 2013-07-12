import os
from time import sleep
import keystoneclient.v2_0
from quantumclient.v2_0 import client as q_client
import glanceclient
import subprocess
import argparse

CIRROS_IMAGE = 'https://launchpad.net/cirros/trunk/0.3.0/+download/cirros-0.3.0-x86_64-disk.img'
here = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)
REPOSITORY_ROOT = here('..')
root = lambda *x: os.path.join(os.path.abspath(REPOSITORY_ROOT), *x)

template_folsom = """
[identity]
# This section contains configuration options that a variety of Tempest
# test clients use when authenticating with different user/tenant
# combinations

# Set to True if your test environment's Keystone authentication service should
# be accessed over HTTPS
use_ssl = %(IDENTITY_USE_SSL)s
# This is the main host address of the authentication service API
host = %(IDENTITY_HOST)s
# Port that the authentication service API is running on
port = %(IDENTITY_PORT)s
# Version of the authentication service API (a string)
api_version = %(IDENTITY_API_VERSION)s
# Path to the authentication service tokens resource (do not modify unless you
# have a custom authentication API and are not using Keystone)
path = %(IDENTITY_PATH)s
# Should typically be left as keystone unless you have a non-Keystone
# authentication API service
strategy = %(IDENTITY_STRATEGY)s

[compute]
# This section contains configuration options used when executing tests
# against the OpenStack Compute API.

# Allows test cases to create/destroy tenants and users. This option
# enables isolated test cases and better parallel execution,
# but also requires that OpenStack Identity API admin credentials
# are known.
allow_tenant_isolation = %(COMPUTE_ALLOW_TENANT_ISOLATION)s

# Allows test cases to create/destroy tenants and users. This option
# enables isolated test cases and better parallel execution,
# but also requires that OpenStack Identity API admin credentials
# are known.
allow_tenant_reuse = %(COMPUTE_ALLOW_TENANT_REUSE)s

# This should be the username of a user WITHOUT administrative privileges
username = %(USERNAME)s
# The above non-administrative user's password
password = %(PASSWORD)s
# The above non-administrative user's tenant name
tenant_name = %(TENANT_NAME)s

# This should be the username of an alternate user WITHOUT
# administrative privileges
alt_username = %(ALT_USERNAME)s
# The above non-administrative user's password
alt_password = %(ALT_PASSWORD)s
# The above non-administrative user's tenant name
alt_tenant_name = %(ALT_TENANT_NAME)s

# Reference data for tests. The ref and ref_alt should be
# distinct images/flavors.
image_ref = %(IMAGE_ID)s
image_ref_alt = %(IMAGE_ID_ALT)s
flavor_ref = %(FLAVOR_REF)s
flavor_ref_alt = %(FLAVOR_REF_ALT)s

# Number of seconds to wait while looping to check the status of an
# instance that is building.
build_interval = %(COMPUTE_BUILD_INTERVAL)s

# Number of seconds to time out on waiting for an instance
# to build or reach an expected status
build_timeout = %(COMPUTE_BUILD_TIMEOUT)s

# Run additional tests that use SSH for instance validation?
# This requires the instances be routable from the host
#  executing the tests
run_ssh = %(RUN_SSH)s
network_for_ssh = %(NETWORK_FOR_SSH)s

# The type of endpoint for a Compute API service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "compute"
catalog_type = %(COMPUTE_CATALOG_TYPE)s

# Does the Compute API support creation of images?
create_image_enabled = %(COMPUTE_CREATE_IMAGE_ENABLED)s

# For resize to work with libvirt/kvm, one of the following must be true:
# Single node: allow_resize_to_same_host=True must be set in nova.conf
# Cluster: the 'nova' user must have scp access between cluster nodes
resize_available = %(COMPUTE_RESIZE_AVAILABLE)s

# Does the compute API support changing the admin password?
change_password_available = %(COMPUTE_CHANGE_PASSWORD_AVAILABLE)s

# Level to log Compute API request/response details.
log_level = %(COMPUTE_LOG_LEVEL)s

# Whitebox options for compute. Whitebox options enable the
# whitebox test cases, which look at internal Nova database state,
# SSH into VMs to check instance state, etc.

# Should we run whitebox tests for Compute?
whitebox_enabled = %(COMPUTE_WHITEBOX_ENABLED)s

# Path of nova source directory
source_dir = %(COMPUTE_SOURCE_DIR)s

# Path of nova configuration file
config_path = %(COMPUTE_CONFIG_PATH)s

# Directory containing nova binaries such as nova-manage
bin_dir = %(COMPUTE_BIN_DIR)s

# Path to a private key file for SSH access to remote hosts
path_to_private_key = %(COMPUTE_PATH_TO_PRIVATE_KEY)s

# Connection string to the database of Compute service
db_uri = %(COMPUTE_DB_URI)s

[image]
# This section contains configuration options used when executing tests
# against the OpenStack Images API

# The type of endpoint for an Image API service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "image"
catalog_type = %(IMAGE_CATALOG_TYPE)s

# The version of the OpenStack Images API to use
api_version = %(IMAGE_API_VERSION)s

# This is the main host address of the Image API
host = %(IMAGE_HOST)s

# Port that the Image API is running on
port = %(IMAGE_PORT)s

# This should be the username of a user WITHOUT administrative privileges
username = %(IMAGE_USERNAME)s
# The above non-administrative user's password
password = %(IMAGE_PASSWORD)s
# The above non-administrative user's tenant name
tenant_name = %(IMAGE_TENANT_NAME)s

[compute-admin]
# This section contains configuration options for an administrative
# user of the Compute API. These options are used in tests that stress
# the admin-only parts of the Compute API

# This should be the username of a user WITH administrative privileges
username = %(COMPUTE_ADMIN_USERNAME)s
# The above administrative user's password
password = %(COMPUTE_ADMIN_PASSWORD)s
# The above administrative user's tenant name
tenant_name = %(COMPUTE_ADMIN_TENANT_NAME)s

[identity-admin]
# This section contains configuration options for an administrative
# user of the Compute API. These options are used in tests that stress
# the admin-only parts of the Compute API

# This should be the username of a user WITH administrative privileges
username = %(IDENTITY_ADMIN_USERNAME)s
# The above administrative user's password
password = %(IDENTITY_ADMIN_PASSWORD)s
# The above administrative user's tenant name
tenant_name = %(IDENTITY_ADMIN_TENANT_NAME)s

[volume]
# This section contains the configuration options used when executing tests
# against the OpenStack Block Storage API service

# The type of endpoint for a Cinder or Block Storage API service.
# Unless you have a custom Keystone service catalog implementation, you
# probably want to leave this value as "volume"
catalog_type = %(VOLUME_CATALOG_TYPE)s
# Number of seconds to wait while looping to check the status of a
# volume that is being made available
build_interval = %(VOLUME_BUILD_INTERVAL)s
# Number of seconds to time out on waiting for a volume
# to be available or reach an expected status
build_timeout = %(VOLUME_BUILD_TIMEOUT)s

[network]
catalog_type = %(NETWORK_CATALOG_TYPE)s
api_version = %(NETWORK_API_VERSION)s
"""

template_grizzly = """
[identity]
# This section contains configuration options that a variety of Tempest
# test clients use when authenticating with different user/tenant
# combinations

# The type of endpoint for a Identity service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "identity"
catalog_type = %(IDENTITY_CATALOG_TYPE)s
# Ignore SSL certificate validation failures? Use when in testing
# environments that have self-signed SSL certs.
disable_ssl_certificate_validation = %(IDENTITY_DISABLE_SSL_CHECK)s
# URL for where to find the OpenStack Identity API endpoint (Keystone)
uri = %(IDENTITY_URI)s
# Should typically be left as keystone unless you have a non-Keystone
# authentication API service

# Set to True if your test environment's Keystone authentication service should
# be accessed over HTTPS
use_ssl = %(IDENTITY_USE_SSL)s
# This is the main host address of the authentication service API
host = %(IDENTITY_HOST)s
# Port that the authentication service API is running on
port = %(IDENTITY_PORT)s
# Version of the authentication service API (a string)
api_version = %(IDENTITY_API_VERSION)s
# Path to the authentication service tokens resource (do not modify unless you
# have a custom authentication API and are not using Keystone)
path = %(IDENTITY_PATH)s
# Should typically be left as keystone unless you have a non-Keystone
# authentication API service
strategy = %(IDENTITY_STRATEGY)s
# The identity region
region = %(IDENTITY_REGION)s
# This should be the username of a user WITHOUT administrative privileges
username = %(USERNAME)s
# The above non-administrative user's password
password = %(PASSWORD)s
# The above non-administrative user's tenant name
tenant_name = %(TENANT_NAME)s
# This should be the username of an alternate user WITHOUT
# administrative privileges
alt_username = %(ALT_USERNAME)s
# The above non-administrative user's password
alt_password = %(ALT_PASSWORD)s
# The above non-administrative user's tenant name
alt_tenant_name = %(ALT_TENANT_NAME)s

# This should be the username of a user WITH administrative privileges
admin_username = %(ADMIN_USER_NAME)s
# The above non-administrative user's password
admin_password = %(ADMIN_PASSWORD)s
# The above non-administrative user's tenant name
admin_tenant_name = %(ADMIN_TENANT_NAME)s

[compute]
# This section contains configuration options used when executing tests
# against the OpenStack Compute API.

# Allows test cases to create/destroy tenants and users. This option
# enables isolated test cases and better parallel execution,
# but also requires that OpenStack Identity API admin credentials
# are known.
allow_tenant_isolation = %(COMPUTE_ALLOW_TENANT_ISOLATION)s

# Allows test cases to create/destroy tenants and users. This option
# enables isolated test cases and better parallel execution,
# but also requires that OpenStack Identity API admin credentials
# are known.
allow_tenant_reuse = %(COMPUTE_ALLOW_TENANT_REUSE)s

# This should be the username of a user WITHOUT administrative privileges
username = %(USERNAME)s
# The above non-administrative user's password
password = %(PASSWORD)s
# The above non-administrative user's tenant name
tenant_name = %(TENANT_NAME)s

# This should be the username of an alternate user WITHOUT
# administrative privileges
alt_username = %(ALT_USERNAME)s
# The above non-administrative user's password
alt_password = %(ALT_PASSWORD)s
# The above non-administrative user's tenant name
alt_tenant_name = %(ALT_TENANT_NAME)s

# Reference data for tests. The ref and ref_alt should be
# distinct images/flavors.
image_ref = %(IMAGE_ID)s
image_ref_alt = %(IMAGE_ID_ALT)s
flavor_ref = %(FLAVOR_REF)s
flavor_ref_alt = %(FLAVOR_REF_ALT)s

# Number of seconds to wait while looping to check the status of an
# instance that is building.
build_interval = %(COMPUTE_BUILD_INTERVAL)s

# Number of seconds to time out on waiting for an instance
# to build or reach an expected status
build_timeout = %(COMPUTE_BUILD_TIMEOUT)s

# Run additional tests that use SSH for instance validation?
# This requires the instances be routable from the host
#  executing the tests
run_ssh = %(RUN_SSH)s
network_for_ssh = %(NETWORK_FOR_SSH)s
ssh_user = %(SSH_USER)s

# IP version of the address used for SSH
ip_version_for_ssh = 4

# Number of seconds to wait to authenticate to an instance
ssh_timeout = 300

# Number of seconds to wait for output from ssh channel
ssh_channel_timeout = 60

# The type of endpoint for a Compute API service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "compute"
catalog_type = %(COMPUTE_CATALOG_TYPE)s

# Does the Compute API support creation of images?
create_image_enabled = %(COMPUTE_CREATE_IMAGE_ENABLED)s

# For resize to work with libvirt/kvm, one of the following must be true:
# Single node: allow_resize_to_same_host=True must be set in nova.conf
# Cluster: the 'nova' user must have scp access between cluster nodes
resize_available = %(COMPUTE_RESIZE_AVAILABLE)s

# Does the compute API support changing the admin password?
change_password_available = %(COMPUTE_CHANGE_PASSWORD_AVAILABLE)s

# Level to log Compute API request/response details.
log_level = %(COMPUTE_LOG_LEVEL)s

# Run live migration tests (requires 2 hosts)
live_migration_available = %(LIVE_MIGRATION)s

# Use block live migration (Otherwise, non-block migration will be
# performed, which requires XenServer pools in case of using XS)
use_block_migration_for_live_migration = %(USE_BLOCKMIG_FOR_LIVEMIG)s

# By default, rely on the status of the diskConfig extension to
# decide if to execute disk config tests. When set to false, tests
# are forced to skip, regardless of the extension status
disk_config_enabled_override = true


[whitebox]
# Whitebox options for compute. Whitebox options enable the
# whitebox test cases, which look at internal Nova database state,
# SSH into VMs to check instance state, etc.

# Should we run whitebox tests for Compute?
whitebox_enabled = %(COMPUTE_WHITEBOX_ENABLED)s

# Path of nova source directory
source_dir = %(COMPUTE_SOURCE_DIR)s

# Path of nova configuration file
config_path = %(COMPUTE_CONFIG_PATH)s

# Directory containing nova binaries such as nova-manage
bin_dir = %(COMPUTE_BIN_DIR)s

# Path to a private key file for SSH access to remote hosts
path_to_private_key = %(COMPUTE_PATH_TO_PRIVATE_KEY)s

# Connection string to the database of Compute service
db_uri = %(COMPUTE_DB_URI)s

[image]
# This section contains configuration options used when executing tests
# against the OpenStack Images API

# The type of endpoint for an Image API service. Unless you have a
# custom Keystone service catalog implementation, you probably want to leave
# this value as "image"
catalog_type = %(IMAGE_CATALOG_TYPE)s

# The version of the OpenStack Images API to use
api_version = %(IMAGE_API_VERSION)s

# This is the main host address of the Image API
host = %(IMAGE_HOST)s

# Port that the Image API is running on
port = %(IMAGE_PORT)s

# This should be the username of a user WITHOUT administrative privileges
username = %(IMAGE_USERNAME)s
# The above non-administrative user's password
password = %(IMAGE_PASSWORD)s
# The above non-administrative user's tenant name
tenant_name = %(IMAGE_TENANT_NAME)s

[compute-admin]
# This section contains configuration options for an administrative
# user of the Compute API. These options are used in tests that stress
# the admin-only parts of the Compute API

# This should be the username of a user WITH administrative privileges
username = %(COMPUTE_ADMIN_USERNAME)s
# The above administrative user's password
password = %(COMPUTE_ADMIN_PASSWORD)s
# The above administrative user's tenant name
tenant_name = %(COMPUTE_ADMIN_TENANT_NAME)s

[identity-admin]
# This section contains configuration options for an administrative
# user of the Compute API. These options are used in tests that stress
# the admin-only parts of the Compute API

# This should be the username of a user WITH administrative privileges
username = %(IDENTITY_ADMIN_USERNAME)s
# The above administrative user's password
password = %(IDENTITY_ADMIN_PASSWORD)s
# The above administrative user's tenant name
tenant_name = %(IDENTITY_ADMIN_TENANT_NAME)s

[volume]
# This section contains the configuration options used when executing tests
# against the OpenStack Block Storage API service

# The type of endpoint for a Cinder or Block Storage API service.
# Unless you have a custom Keystone service catalog implementation, you
# probably want to leave this value as "volume"
catalog_type = %(VOLUME_CATALOG_TYPE)s
# Number of seconds to wait while looping to check the status of a
# volume that is being made available
build_interval = %(VOLUME_BUILD_INTERVAL)s
# Number of seconds to time out on waiting for a volume
# to be available or reach an expected status
build_timeout = %(VOLUME_BUILD_TIMEOUT)s

[network]
catalog_type = %(NETWORK_CATALOG_TYPE)s
api_version = %(NETWORK_API_VERSION)s
# A large private cidr block from which to allocate smaller blocks for
# tenant networks.
tenant_network_cidr = %(TENANT_NETWORK_CIDR)s

# The mask bits used to partition the tenant block.
tenant_network_mask_bits = %(TENANT_NETWORK_MASK_BITS)s

# If tenant networks are reachable, connectivity checks will be
# performed directly against addresses on those networks.
tenant_networks_reachable = %(TENANT_NETS_REACHABLE)s

# Id of the public network that provides external connectivity.
public_network_id = %(PUBLIC_NETWORK_ID)s

# Id of a shared public router that provides external connectivity.
# A shared public router would commonly be used where IP namespaces
# were disabled.  If namespaces are enabled, it would be preferable
# for each tenant to have their own router.
public_router_id = %(PUBLIC_ROUTER_ID)s

# Whether or not quantum is expected to be available
quantum_available = %(QUANTUM)s
"""


class PrepareTempest():
    def __init__(self, username, password, tenant, public_ip, internal_ip,
                 release, simple):
        self.username = username
        self.password = password
        self.tenant = tenant
        self.public_ip = public_ip
        self.internal_ip = internal_ip
        self.release = release
        self.simple = simple

    def prepare(self):
        if self.release == "grizzly":
            self.prepare_tempest_grizzly(template_grizzly)
        else:
            self.prepare_tempest_folsom(template_folsom)

    def get_auth_url(self):
        print "auth_url", 'http://%s:5000/v2.0/' % self.public_ip
        return 'http://%s:5000/v2.0/' % self.public_ip

    def get_keystone(self):
        keystone = retry(10, keystoneclient.v2_0.client.Client,
                         username=self.username,
                         password=self.password,
                         tenant_name=self.tenant,
                         auth_url=self.get_auth_url())

        return keystone

    def get_quantum(self):
        quantum = retry(10, q_client.Client,
                        username=self.username,
                        password=self.password,
                        tenant_name=self.tenant,
                        auth_url=self.get_auth_url())
        return quantum

    def get_glance(self):
        keystone = self.get_keystone()
        endpoint = keystone.service_catalog.url_for(service_type='image',
                                                    endpoint_type='publicURL')
        return glanceclient.Client('1', endpoint=endpoint,
                                   token=keystone.auth_token)

    def prepare_tempest_folsom(self, template_folsom):
        image_ref, image_ref_alt, net_id, router_id = self.make_tempest_objects()
        self._tempest_write_config(
            self._tempest_config_folsom(
                template=template_folsom,
                image_ref=image_ref,
                image_ref_alt=image_ref_alt,
                path_to_private_key=root('fuel_test',
                                         'config',
                                         'ssh_keys',
                                         'openstack'),
                compute_db_uri='mysql://nova:nova@%s/nova' % self.internal_ip
            )
        )

    def prepare_tempest_grizzly(self, template_grizzly):
        image_ref, image_ref_alt, net_id, router_id = self.make_tempest_objects()
        self._tempest_write_config(
            self._tempest_config_grizzly(
                template=template_grizzly,
                image_ref=image_ref,
                image_ref_alt=image_ref_alt,
                public_network_id=net_id,
                public_router_id=router_id,
                path_to_private_key=root(
                    'fuel_test',
                    'config',
                    'ssh_keys',
                    'openstack'
                ),
                compute_db_uri='mysql://nova:nova@%s/nova' % self.internal_ip
            )
        )

    def make_tempest_objects(self):
        keystone = self.get_keystone()
        tenant1 = retry(10, keystone.tenants.create, tenant_name='tenant1')
        tenant2 = retry(10, keystone.tenants.create, tenant_name='tenant2')
        retry(10, keystone.users.create, name='tempest1', password='secret',
              email='tempest1@example.com', tenant_id=tenant1.id)
        retry(10, keystone.users.create, name='tempest2', password='secret',
              email='tempest2@example.com', tenant_id=tenant2.id)
        image_ref, image_ref_alt = self._tempest_add_images()
        #net_id, router_id = self._tempest_get_netid_routerid()
        return image_ref, image_ref_alt, "net_id", "router_id"

    def _upload(self, glance, name, path):
        image = glance.images.create(name=name, is_public=True,
                                     container_format='bare',
                                     disk_format='qcow2')
        image.update(data=open(path, 'rb'))
        return image.id

    def _tempest_add_images(self):
        if not os.path.isfile('cirros.img'):
            subprocess.check_call(['wget', CIRROS_IMAGE, '-O', 'cirros.img'])
        glance = self.get_glance()
        return self._upload(glance, 'cirros.img', 'cirros.img'), self._upload(
            glance, 'cirros.img', 'cirros.img')

    def _tempest_get_netid_routerid(self):
        networking = self.get_quantum()
        params = {'router:external': True}
        network = networking.list_networks(**params)['networks'][0]['id']
        router = networking.list_routers()['routers'][0]['id']
        return network, router

    def _tempest_write_config(self, config):
        with open(root('..', 'tempest.conf'), 'w') as f:
            f.write(config)

    def _tempest_config_folsom(
            self, template, image_ref, image_ref_alt,
            path_to_private_key,
            compute_db_uri='mysql://user:pass@localhost/nova'):
        sample = load(template)
        config = sample % {
            'IDENTITY_USE_SSL': 'false',
            'IDENTITY_HOST': self.public_ip,
            'IDENTITY_PORT': '5000',
            'IDENTITY_API_VERSION': 'v2.0',
            'IDENTITY_PATH': 'tokens',
            'IDENTITY_STRATEGY': 'keystone',
            'COMPUTE_ALLOW_TENANT_ISOLATION': 'true',
            'COMPUTE_ALLOW_TENANT_REUSE': 'true',
            'USERNAME': 'tempest1',
            'PASSWORD': 'secret',
            'TENANT_NAME': 'tenant1',
            'ALT_USERNAME': 'tempest2',
            'ALT_PASSWORD': 'secret',
            'ALT_TENANT_NAME': 'tenant2',
            'IMAGE_ID': image_ref,
            'IMAGE_ID_ALT': image_ref_alt,
            'FLAVOR_REF': '1',
            'FLAVOR_REF_ALT': '2',
            'COMPUTE_BUILD_INTERVAL': '10',
            'COMPUTE_BUILD_TIMEOUT': '600',
            'RUN_SSH': 'false',
            'NETWORK_FOR_SSH': 'novanetwork',
            'COMPUTE_CATALOG_TYPE': 'compute',
            'COMPUTE_CREATE_IMAGE_ENABLED': 'true',
            'COMPUTE_RESIZE_AVAILABLE': 'true',
            'COMPUTE_CHANGE_PASSWORD_AVAILABLE': 'false',
            'COMPUTE_LOG_LEVEL': 'DEBUG',
            'COMPUTE_WHITEBOX_ENABLED': 'true',
            'COMPUTE_SOURCE_DIR': '/opt/stack/nova',
            'COMPUTE_CONFIG_PATH': '/etc/nova/nova.conf',
            'COMPUTE_BIN_DIR': '/usr/local/bin',
            'COMPUTE_PATH_TO_PRIVATE_KEY': path_to_private_key,
            'COMPUTE_DB_URI': compute_db_uri,
            'IMAGE_CATALOG_TYPE': 'image',
            'IMAGE_API_VERSION': '1',
            'IMAGE_HOST': self.public_ip,
            'IMAGE_PORT': '9292',
            'IMAGE_USERNAME': 'tempest1',
            'IMAGE_PASSWORD': 'secret',
            'IMAGE_TENANT_NAME': 'tenant1',
            'COMPUTE_ADMIN_USERNAME': self.username,
            'COMPUTE_ADMIN_PASSWORD': self.password,
            'COMPUTE_ADMIN_TENANT_NAME': self.tenant,
            'IDENTITY_ADMIN_USERNAME': self.username,
            'IDENTITY_ADMIN_PASSWORD': self.password,
            'IDENTITY_ADMIN_TENANT_NAME': self.tenant,
            'VOLUME_CATALOG_TYPE': 'volume',
            'VOLUME_BUILD_INTERVAL': '10',
            'VOLUME_BUILD_TIMEOUT': '300',
            'NETWORK_CATALOG_TYPE': 'network',
            'NETWORK_API_VERSION': 'v2.0',
        }

        return config

    def _tempest_config_grizzly(
            self, template, image_ref, image_ref_alt,
            public_network_id, public_router_id,
            path_to_private_key,
            compute_db_uri='mysql://nova:secret@localhost/nova'):
        config = template % {
            'IDENTITY_CATALOG_TYPE': 'identity',
            'IDENTITY_DISABLE_SSL_CHECK': 'true',
            'IDENTITY_USE_SSL': 'false',
            'IDENTITY_URI': 'http://%s:5000/v2.0/' % self.public_ip,
            'IDENTITY_STRATEGY': 'keystone',
            'IDENTITY_REGION': 'RegionOne',
            'USERNAME': 'tempest1',
            'PASSWORD': 'secret',
            'TENANT_NAME': 'tenant1',
            'ALT_USERNAME': 'tempest2',
            'ALT_PASSWORD': 'secret',
            'ALT_TENANT_NAME': 'tenant2',
            'ADMIN_USER_NAME': self.username,
            'ADMIN_PASSWORD': self.password,
            'ADMIN_TENANT_NAME': self.tenant,
            'COMPUTE_ALLOW_TENANT_ISOLATION': 'false',
            'COMPUTE_ALLOW_TENANT_REUSE': 'true',
            'IMAGE_ID': image_ref,
            'IMAGE_ID_ALT': image_ref_alt,
            'FLAVOR_REF': '1',
            'FLAVOR_REF_ALT': '1',
            'COMPUTE_BUILD_INTERVAL': '10',
            'COMPUTE_BUILD_TIMEOUT': '600',
            'RUN_SSH': 'false',
            'SSH_USER': 'cirros',
            'NETWORK_FOR_SSH': 'net04',
            'COMPUTE_CATALOG_TYPE': 'compute',
            'COMPUTE_CREATE_IMAGE_ENABLED': 'true',
            'COMPUTE_RESIZE_AVAILABLE': 'true',
            'COMPUTE_CHANGE_PASSWORD_AVAILABLE': 'true',
            'LIVE_MIGRATION': 'true',
            'USE_BLOCKMIG_FOR_LIVEMIG': 'true',
            'COMPUTE_WHITEBOX_ENABLED': 'true',
            'COMPUTE_SOURCE_DIR': '/opt/stack/nova',
            'COMPUTE_CONFIG_PATH': '/etc/nova/nova.conf',
            'COMPUTE_BIN_DIR': '/usr/local/bin',
            'COMPUTE_DB_URI': compute_db_uri,
            'COMPUTE_PATH_TO_PRIVATE_KEY': path_to_private_key,
            'COMPUTE_ADMIN_USERNAME': self.username,
            'COMPUTE_ADMIN_PASSWORD': self.password,
            'COMPUTE_ADMIN_TENANT_NAME': self.tenant,
            'IMAGE_CATALOG_TYPE': 'image',
            'IMAGE_API_VERSION': '1',
            'NETWORK_API_VERSION': 'v1.1',
            'NETWORK_CATALOG_TYPE': 'network',
            'TENANT_NETWORK_CIDR': '192.168.112.0/24',
            'TENANT_NETWORK_MASK_BITS': '28',
            'TENANT_NETS_REACHABLE': 'false',
            'PUBLIC_NETWORK_ID': public_network_id,
            'PUBLIC_ROUTER_ID': public_router_id,
            'QUANTUM': 'false',
            'VOLUME_CATALOG_TYPE': 'volume',
            'VOLUME_BUILD_INTERVAL': '15',
            'VOLUME_BUILD_TIMEOUT': '400',
            'IDENTITY_USE_SSL': 'false',
            'IDENTITY_HOST': self.public_ip,
            'IDENTITY_PORT': '5000',
            'IDENTITY_API_VERSION': 'v2.0',
            'IDENTITY_PATH': 'tokens',
            'COMPUTE_LOG_LEVEL': 'DEBUG',
            'IMAGE_HOST': self.public_ip,
            'IMAGE_PORT': '9292',
            'IMAGE_USERNAME': 'tempest1',
            'IMAGE_PASSWORD': 'secret',
            'IMAGE_TENANT_NAME': 'tenant1',
            'IDENTITY_ADMIN_USERNAME': self.username,
            'IDENTITY_ADMIN_PASSWORD': self.password,
            'IDENTITY_ADMIN_TENANT_NAME': self.tenant,
        }

        return config


def retry(count, func, **kwargs):
    i = 0
    while True:
        # noinspection PyBroadException
        try:
            return func(**kwargs)
        except:
            if i >= count:
                raise
            i += 1
            sleep(1)


def load(path):
    with open(path) as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", help="openstack release under test",
                        default="grizzly")
    parser.add_argument("--username", help="administrator name",
                        default="admin")
    parser.add_argument("--password", help="administrator password",
                        default="nova")
    parser.add_argument("--tenant", help="default tenant name",
                        default="admin")
    parser.add_argument("public_ip",
                        help="public or virtual ip of controller")
    parser.add_argument("internal_ip",
                        help="internal or virtual ip of controller")
    parser.add_argument("-c", "--ci", default=True)
    parser.add_argument("--simple", default=False)
    args = vars(parser.parse_args())

    prepare = PrepareTempest(
        username=args['username'],
        password=args['password'],
        tenant=args['tenant'],
        public_ip=args['public_ip'],
        internal_ip=args['internal_ip'],
        simple=args['simple'],
        release=args['release']
    )

    prepare.prepare()


if __name__ == '__main__':
    main()
