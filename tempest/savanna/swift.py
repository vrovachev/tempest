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


from tempest.openstack.common import excutils
from tempest.savanna import base


class SwiftTest(base.ITestCase):

    @base.skip_test(
        'SKIP_SWIFT_TEST',
        message='Test for check of Swift availability was skipped.')
    def _check_swift_availability(self, cluster_info):

        plugin = cluster_info['plugin']

        extra_script_parameters = {
            'OS_URL': self.COMMON.OS_AUTH_URL,
            'OS_TENANT_NAME': self.COMMON.OS_TENANT_NAME,
            'OS_USERNAME': self.COMMON.OS_USERNAME,
            'OS_PASSWORD': self.COMMON.OS_PASSWORD,
            'HADOOP_USER': plugin.HADOOP_USER,
        }

        namenode_ip = cluster_info['node_info']['namenode_ip']

        self.open_ssh_connection(namenode_ip, plugin.NODE_USERNAME)

        try:

            self.transfer_helper_script_to_node('swift_test_script.sh',
                                                extra_script_parameters)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                print(str(e))

        self.execute_command('./script.sh')

        self.close_ssh_connection()
