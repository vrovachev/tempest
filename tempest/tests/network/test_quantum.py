import unittest2 as unittest
from quantumclient.common import exceptions
from tempest.test import DefaultClientTest

class TestQuantum(DefaultClientTest):

    @property
    def client(self):
        """
        :rtype : quantumclient.v2_0.client.Client
        """
        return self.manager._get_network_client()

    @property
    def admin_client(self):
        """
        :rtype : quantumclient.v2_0.client.Client
        """
        return self.manager._get_network_client_admin()

    def _tenant_id(self):
        tenants =  filter(lambda x: x.name == self.manager.config.compute.tenant_name,
            self.manager._get_identity_client(
            ).tenants.list())
        if len(tenants) == 0: raise Exception('Tenant %s not found' % tenants[0])
        return tenants[0].id

    def test_list_extensions(self):
        self.client.list_extensions()

    def test_list_networks(self):
        self.client.list_networks()

    def test_list_floatingips(self):
        self.client.list_floatingips()

    def test_list_networks(self):
        self.client.list_networks()

    def test_list_ports(self):
        self.client.list_ports()

    def test_list_subnets(self):
        self.client.list_subnets()

    def test_list_routers(self):
        self.client.list_routers()

    def test_(self):
        pass
#        self.client.create_floatingip(body='')
#        self.client.create_port()
        #self.client.create_router()
#        self.client.create_subnet()

    def _body(self, entity, **kwargs):
        return { entity : dict(**kwargs) }

    def setUp(self):
        for network in self.client.list_networks()["networks"]:
            if network["name"].startswith("sample"):
                self.client.delete_network(network["id"])
        for router in self.client.list_routers()["routers"]:
            if router["name"].startswith("sample"):
                self.client.delete_router(router["id"])
        for subnet in self.client.list_subnets()["subnets"]:
            if subnet["name"].startswith("sample"):
                self.client.delete_subnet(subnet["id"])

    def validateNetwork(self, network, name, admin_state_up):
        self.assertEquals(admin_state_up, network["admin_state_up"])
        self.assertEquals(name, network["name"])
        self.assertEquals("ACTIVE", network["status"])
        self.assertEquals([], network["subnets"])
        self.assertEquals(False, network["shared"])
        self.assertEquals(self._tenant_id(), network["tenant_id"])
        self.assertTrue(network["id"])
        self.assertIsNotNone(network["router:external"])

    def test_create_network_admin_state_down(self):
        body = self._body("network", name="sample_network", admin_state_up=False)
        network = self.client.create_network(body)["network"]
        self.validateNetwork(network, "sample_network", admin_state_up=False)

    def test_create_network_admin_state_up(self):
        body = self._body("network", name="sample_network", admin_state_up=True)
        network = self.client.create_network(body)["network"]
        self.validateNetwork(network, "sample_network", admin_state_up=True)

    def test_create_network_bulk(self):
        body = {
            "networks": [
                {
                    "name": "sample_network_1",
                    "admin_state_up": False,
                },
                {
                    "name": "sample_network_2",
                    "admin_state_up": True,
                }]
        }
        networks = self.client.create_network(body)["networks"]
        self.validateNetwork(filter(lambda network: network["name"]=="sample_network_1", networks)[0], "sample_network_1", False)
        self.validateNetwork(filter(lambda network: network["name"]=="sample_network_2", networks)[0], "sample_network_2", True)

    def test_update_network_admin_state_down(self):
        network_id = self.client.create_network(self._body("network", name="sample_network", admin_state_up=False))["network"]["id"]
        network = self.client.update_network(network_id, self._body("network", name="sample_network2", admin_state_up=True))["network"]
        self.validateNetwork(network, "sample_network2", admin_state_up=True)


    def test_show_network_admin_state_down(self):
        network_id = self.client.create_network(self._body("network", name="sample_network", admin_state_up=False))["network"]["id"]
        network = self.client.show_network(network_id)["network"]
        self.validateNetwork(network, "sample_network", admin_state_up=False)

    def test_show_network_admin_state_up(self):
        network_id = self.client.create_network(self._body("network", name="sample_network", admin_state_up=True))["network"]["id"]
        network = self.client.show_network(network_id)["network"]
        self.validateNetwork(network, "sample_network", admin_state_up=True)

    def test_delete_network_admin_state_down(self):
        body = self._body("network", name="sample_network", admin_state_up=False)
        network = self.client.create_network(body)["network"]
        self.client.delete_network(network["id"])

    def test_delete_network_admin_state_up(self):
        body = self._body("network", name="sample_network", admin_state_up=True)
        network = self.client.create_network(body)["network"]
        self.client.delete_network(network["id"])

    def test_delete_network_twice(self):
        body = self._body("network", name="sample_network", admin_state_up=True)
        network = self.client.create_network(body)["network"]
        self.client.delete_network(network["id"])
        self.assertRaisesRegexp(exceptions.QuantumException, "Network .* could not be found", self.client.delete_network, network["id"])


    def validateRouter(self, router, name, admin_state_up, external_gateway_info):
        self.assertEquals(admin_state_up, router["admin_state_up"])
        self.assertEquals(name, router["name"])
        self.assertEquals("ACTIVE", router["status"])
        self.assertEquals(external_gateway_info, router["external_gateway_info"])
        self.assertEquals(self._tenant_id(), router["tenant_id"])
        self.assertTrue(router["id"])

    def test_create_router_admin_state_down(self):
        body = self._body("router", name='sample_router', admin_state_up=False)
        router = self.client.create_router(body)["router"]
        self.validateRouter(router, 'sample_router', admin_state_up=False, external_gateway_info=None)

    def test_create_router_admin_state_up(self):
        body = self._body("router", name='sample_router', admin_state_up=True)
        router = self.client.create_router(body)["router"]
        self.validateRouter(router, 'sample_router', admin_state_up=True, external_gateway_info=None)

    @unittest.skip("quantum")
    def test_create_router_external_gateway(self):
        network_id = filter(lambda network: network["router:external"]==True, self.client.list_networks()["networks"])[0]["id"]
        body = self._body("router", name='sample_router', admin_state_up=True, external_gateway_info={'network_id': network_id})
        router = self.admin_client.create_router(body)["router"]
        self.validateRouter(router, 'sample_router', admin_state_up=True, external_gateway_info={'network_id': network_id})

    def validateSubnet(self, subnet, name, network_id, cidr, enable_dhcp, ip_version, allocation_pools, gateway_ip):
        self.assertEquals(name, subnet["name"])
        self.assertEquals(self._tenant_id(), subnet["tenant_id"])
        self.assertEquals(network_id, subnet["network_id"])
        self.assertEquals(cidr, subnet["cidr"])
        self.assertEquals(enable_dhcp, subnet["enable_dhcp"])
        self.assertEquals(ip_version, subnet["ip_version"])
        self.assertEquals(allocation_pools, subnet["allocation_pools"])
        self.assertEquals(gateway_ip, subnet["gateway_ip"])
        self.assertTrue(subnet["id"])

#    {
#        "subnet": {
#            "name": "",
#            "network_id": "ed2e3c10-2e43-4297-9006-2863a2d1abbc",
#            "tenant_id": "c1210485b2424d48804aad5d39c61b8f",
#            "allocation_pools": [{"start": "10.0.3.20", "end": "10.0.3.150"}],
#            "gateway_ip": "10.0.3.1",
#            "ip_version": 4,
#            "cidr": "10.0.3.0/24",
#            "id": "9436e561-47bf-436a-b1f1-fe23a926e031",
#            "enable_dhcp": true}
#    }

    def test_create_subnet(self):
        network_id = self.client.create_network(self._body("network", name="sample_network", admin_state_up=False))["network"]["id"]
        subnet = self.client.create_subnet(
            self._body("subnet",
                network_id=network_id,
                cidr="10.0.3.0/24",
                ip_version=4,
                allocation_pools = [{"start": "10.0.3.20", "end": "10.0.3.150"}])
            )["subnet"]
        self.validateSubnet(subnet, network_id=network_id, cidr="10.0.3.0/24", enable_dhcp=True, ip_version=4, allocation_pools=[{"start": "10.0.3.20", "end": "10.0.3.150"}],gateway_ip="10.0.3.1", name="")

    def test_create_subnet2(self):
        network_id = self.client.create_network(self._body("network", name="sample_network", admin_state_up=False))["network"]["id"]
        subnet = self.client.create_subnet(
            self._body("subnet",
                name = "sample_subnet",
                network_id=network_id,
                cidr="::10.0.3.0/24",
                enable_dhcp=False,
                ip_version=6,
                gateway_ip="::10.0.2.1",
                allocation_pools = [{"start": "::10.0.3.20", "end": "::10.0.3.150"}])
        )["subnet"]
        self.validateSubnet(subnet, network_id=network_id, cidr="::10.0.3.0/24", enable_dhcp=False, ip_version=6, allocation_pools=[{"start": "::10.0.3.20", "end": "::10.0.3.150"}],gateway_ip="::10.0.2.1", name="sample_subnet")






















