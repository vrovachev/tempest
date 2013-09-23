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


import nose.plugins.attrib as attrib
import unittest2

from tempest.openstack.common import excutils
from tempest.config import TempestConfig as cfg
import tempest.savanna.cluster_configs as cluster_configs
import tempest.savanna.map_reduce as map_reduce
import tempest.savanna.scaling as scaling
import tempest.savanna.swift as swift


class VanillaGatingTest(cluster_configs.ClusterConfigTest,
                        map_reduce.MapReduceTest, swift.SwiftTest,
                        scaling.ScalingTest):

    SKIP_CLUSTER_CONFIG_TEST = cfg().savanna_vanilla.SKIP_CLUSTER_CONFIG_TEST
    SKIP_MAP_REDUCE_TEST = cfg().savanna_vanilla.SKIP_MAP_REDUCE_TEST
    SKIP_SWIFT_TEST = cfg().savanna_vanilla.SKIP_SWIFT_TEST
    SKIP_SCALING_TEST = cfg().savanna_vanilla.SKIP_SCALING_TEST

    @attrib.attr(tags='vanilla')
    @unittest2.skipIf(cfg().savanna_vanilla.SKIP_ALL_TESTS_FOR_PLUGIN,
                      'All tests for Vanilla plugin were skipped')
    def test_vanilla_plugin_gating(self):

        node_group_template_id_list = []

#-------------------------------CLUSTER CREATION-------------------------------

#---------------------"tt-dn" node group template creation---------------------

        try:

            node_group_template_tt_dn_id = self.create_node_group_template(
                'tt-dn',
                self.VANILLA,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['tasktracker', 'datanode'],
                node_configs={
                    'HDFS': cluster_configs.DN_CONFIG,
                    'MapReduce': cluster_configs.TT_CONFIG
                }
            )
            node_group_template_id_list.append(node_group_template_tt_dn_id)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                print(
                    'Failure while \'tt-dn\' node group template creation: '
                    + str(e)
                )

#-----------------------"tt" node group template creation----------------------

        try:

            node_group_template_tt_id = self.create_node_group_template(
                'tt',
                self.VANILLA,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['tasktracker'],
                node_configs={
                    'MapReduce': cluster_configs.TT_CONFIG
                }
            )
            node_group_template_id_list.append(node_group_template_tt_id)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    node_group_template_id_list=node_group_template_id_list
                )
                print(
                    'Failure while \'tt\' node group template creation: '
                    + str(e)
                )

#----------------------"dn" node group template creation-----------------------

        try:

            node_group_template_dn_id = self.create_node_group_template(
                'dn',
                self.VANILLA,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['datanode'],
                node_configs={
                    'HDFS': cluster_configs.DN_CONFIG
                }
            )
            node_group_template_id_list.append(node_group_template_dn_id)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    node_group_template_id_list=node_group_template_id_list
                )
                print(
                    'Failure while \'dn\' node group template creation: '
                    + str(e)
                )

#---------------------------Cluster template creation--------------------------

        try:

            cluster_template_id = self.create_cluster_template(
                'test-cluster-template',
                self.VANILLA,
                description='test cluster template',
                cluster_configs={
                    'HDFS': cluster_configs.CLUSTER_HDFS_CONFIG,
                    'MapReduce': cluster_configs.CLUSTER_MR_CONFIG,
                    'general': cluster_configs.CLUSTER_GENERAL_CONFIG
                },
                node_groups=[
                    dict(
                        name='master-node-jt-nn',
                        flavor_id=self.COMMON.FLAVOR_ID,
                        node_processes=['namenode', 'jobtracker'],
                        node_configs={
                            'HDFS': cluster_configs.NN_CONFIG,
                            'MapReduce': cluster_configs.JT_CONFIG
                        },
                        count=1),
                    dict(
                        name='master-node-sec-nn',
                        flavor_id=self.COMMON.FLAVOR_ID,
                        node_processes=['secondarynamenode'],
                        node_configs={
                            'HDFS': cluster_configs.SNN_CONFIG
                        },
                        count=1),
                    dict(
                        name='worker-node-tt-dn',
                        node_group_template_id=node_group_template_tt_dn_id,
                        count=3),
                    dict(
                        name='worker-node-dn',
                        node_group_template_id=node_group_template_dn_id,
                        count=1),
                    dict(
                        name='worker-node-tt',
                        node_group_template_id=node_group_template_tt_id,
                        count=1)
                ],
                anti_affinity=[]
            )

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    node_group_template_id_list=node_group_template_id_list
                )
                print(
                    'Failure while cluster template creation: ' + str(e)
                )

#-------------------------------Cluster creation-------------------------------

        try:

            cluster_info = self.create_cluster_and_get_info(
                self.VANILLA,
                cluster_template_id,
                description='test cluster',
                cluster_configs={},
                node_groups=None,
                anti_affinity=[]
            )

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    self.cluster_id, cluster_template_id,
                    node_group_template_id_list
                )
                print('Failure while cluster creation: ' + str(e))

#----------------------------CLUSTER CONFIG TESTING----------------------------

        try:
            self._cluster_config_testing(cluster_info)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    cluster_info['cluster_id'], cluster_template_id,
                    node_group_template_id_list
                )
                print(
                    'Failure while cluster config testing: ' + str(e)
                )

#------------------------------MAP REDUCE TESTING------------------------------

        try:

            self._map_reduce_testing(cluster_info)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                # self.delete_objects(
                #     cluster_info['cluster_id'], cluster_template_id,
                #     node_group_template_id_list
                # )
                print('Failure while Map Reduce testing: ' + str(e))

#---------------------------CHECK SWIFT AVAILABILITY---------------------------

        try:

            self._check_swift_availability(cluster_info)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    cluster_info['cluster_id'], cluster_template_id,
                    node_group_template_id_list
                )
                print(
                    'Failure during check of Swift availability: ' + str(e)
                )

#--------------------------------CLUSTER SCALING-------------------------------

        change_list = [
            {
                'operation': 'resize',
                'info': ['worker-node-tt-dn', 4]
            },
            {
                'operation': 'resize',
                'info': ['worker-node-dn', 0]
            },
            {
                'operation': 'resize',
                'info': ['worker-node-tt', 0]
            },
            {
                'operation': 'add',
                'info': [
                    'new-worker-node-tt', 1, '%s' % node_group_template_tt_id
                ]
            },
            {
                'operation': 'add',
                'info': [
                    'new-worker-node-dn', 1, '%s' % node_group_template_dn_id
                ]
            }
        ]

        try:

            new_cluster_info = self._cluster_scaling(cluster_info, change_list)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    cluster_info['cluster_id'], cluster_template_id,
                    node_group_template_id_list
                )
                print('Failure while cluster scaling: ' + str(e))

        if not self.VANILLA.SKIP_SCALING_TEST:

#---------------------CLUSTER CONFIG TESTING AFTER SCALING---------------------

            try:

                self._cluster_config_testing(new_cluster_info)

            except Exception as e:

                with excutils.save_and_reraise_exception():

                    self.delete_objects(
                        new_cluster_info['cluster_id'], cluster_template_id,
                        node_group_template_id_list
                    )
                    print(
                        'Failure while cluster config testing after '
                        'cluster scaling: ' + str(e)
                    )

#-----------------------MAP REDUCE TESTING AFTER SCALING-----------------------

            try:

                self._map_reduce_testing(new_cluster_info)

            except Exception as e:

                with excutils.save_and_reraise_exception():

                    self.delete_objects(
                        new_cluster_info['cluster_id'], cluster_template_id,
                        node_group_template_id_list
                    )
                    print(
                        'Failure while Map Reduce testing after '
                        'cluster scaling: ' + str(e)
                    )

#--------------------CHECK SWIFT AVAILABILITY AFTER SCALING--------------------

            try:

                self._check_swift_availability(new_cluster_info)

            except Exception as e:

                with excutils.save_and_reraise_exception():

                    self.delete_objects(
                        new_cluster_info['cluster_id'], cluster_template_id,
                        node_group_template_id_list
                    )
                    print(
                        'Failure during check of Swift availability after '
                        'cluster scaling: ' + str(e)
                    )

#----------------------------DELETE CREATED OBJECTS----------------------------

        self.delete_objects(
            cluster_info['cluster_id'], cluster_template_id,
            node_group_template_id_list
        )
