# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.api.savanna import base
from tempest.openstack.common import excutils


class SwiftTest(base.BaseSavannaTest):

    @base.skip_test(
        'SKIP_SWIFT_TEST',
        message='Test for check of Swift availability was skipped.')
    def _check_swift_availability(self, cluster_info):

        plugin_config = cluster_info['plugin_config']

        extra_script_parameters = {
            'OS_TENANT_NAME': self.config.identity.tenant_name,
            'OS_USERNAME': self.config.identity.username,
            'OS_PASSWORD': self.config.identity.password,
            'HADOOP_USER': plugin_config.hadoop_user,
            'CONTAINER_NAME': self.container_name
        }

        namenode_ip = cluster_info['node_info']['namenode_ip']

        self.open_ssh_connection(namenode_ip, plugin_config.image_user)

        try:

            self.container_client.create_container(self.container_name)

            self.transfer_helper_script_to_node(
                'swift_test_script.sh', parameter_list=extra_script_parameters
            )

        except Exception as e:

            with excutils.save_and_reraise_exception():

                print(str(e))

        try:

            self.execute_command('./script.sh')

        except Exception as e:

            with excutils.save_and_reraise_exception():

                print(str(e))

        finally:

            self.close_ssh_connection()

            self.delete_swift_container(self.container_name)
