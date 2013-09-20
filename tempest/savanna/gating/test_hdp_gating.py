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
import tempest.savanna.map_reduce as map_reduce
import tempest.savanna.scaling as scaling


node_group_template_id_list = []


class HDPGatingTest(map_reduce.MapReduceTest, scaling.ScalingTest):

    SKIP_MAP_REDUCE_TEST = cfg().savanna_hdp.SKIP_MAP_REDUCE_TEST
    SKIP_SCALING_TEST = cfg().savanna_hdp.SKIP_SCALING_TEST

    @attrib.attr(tags='hdp')
    @unittest2.skipIf(cfg().savanna_hdp.SKIP_ALL_TESTS_FOR_PLUGIN,
                      'All tests for HDP plugin were skipped')
    def test_hdp_plugin_gating(self):

        node_group_template_id_list = []

#-------------------------------CLUSTER CREATION-------------------------------

#---------------------"jt-nn" node group template creation---------------------

        try:

            node_group_template_jt_nn_id = self.create_node_group_template(
                'jt-nn',
                self.HDP,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['JOBTRACKER', 'NAMENODE', 'SECONDARY_NAMENODE',
                                'GANGLIA_SERVER', 'GANGLIA_MONITOR',
                                'NAGIOS_SERVER', 'AMBARI_SERVER',
                                'AMBARI_AGENT'],
                node_configs={}
            )
            node_group_template_id_list.append(node_group_template_jt_nn_id)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                print(
                    'Failure while \'jt-nn\' node group template creation: '
                    + str(e)
                )

#-----------------------"tt-dn" node group template creation-------------------

        try:

            node_group_template_tt_dn_id = self.create_node_group_template(
                'tt-dn',
                self.HDP,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['TASKTRACKER', 'DATANODE', 'GANGLIA_MONITOR',
                                'HDFS_CLIENT', 'MAPREDUCE_CLIENT',
                                'AMBARI_AGENT'],
                node_configs={}
            )
            node_group_template_id_list.append(node_group_template_tt_dn_id)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    node_group_template_id_list=node_group_template_id_list
                )
                print(
                    'Failure while \'tt-dn\' node group template creation: '
                    + str(e)
                )

#---------------------------Cluster template creation--------------------------

        try:

            cluster_template_id = self.create_cluster_template(
                'test-cluster-template',
                self.HDP,
                description='test cluster template',
                cluster_configs={},
                node_groups=[
                    dict(
                        name='master-node',
                        node_group_template_id=node_group_template_jt_nn_id,
                        count=1),
                    dict(
                        name='worker-node',
                        node_group_template_id=node_group_template_tt_dn_id,
                        count=3)
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
                self.HDP,
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

#------------------------------MAP REDUCE TESTING------------------------------

        try:

            self._map_reduce_testing(cluster_info)

        except Exception as e:

            with excutils.save_and_reraise_exception():

                self.delete_objects(
                    cluster_info['cluster_id'], cluster_template_id,
                    node_group_template_id_list
                )
                print('Failure while Map Reduce testing: ' + str(e))

#--------------------------------CLUSTER SCALING-------------------------------

        change_list = [
            {
                'operation': 'resize',
                'info': ['worker-node', 4]
            },
            {
                'operation': 'add',
                'info': [
                    'new-worker-node-tt-dn', 1, '%s'
                                                % node_group_template_tt_dn_id
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

        if not self.HDP.SKIP_SCALING_TEST:

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

#----------------------------DELETE CREATED OBJECTS----------------------------

        self.delete_objects(
            cluster_info['cluster_id'], cluster_template_id,
            node_group_template_id_list
        )
