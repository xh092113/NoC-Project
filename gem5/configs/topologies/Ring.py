from m5.params import *
from m5.objects import *

from common import FileSystemConfig
from topologies.BaseTopology import SimpleTopology

# Creates a generic Ring topology
# Ring routing will be handled by the 'ring_topology' routing algorithm.

class RingTopology(SimpleTopology):
    description = "RingTopology"

    def __init__(self, controllers, ring_length):
        self.nodes = controllers

    # Makes a generic ring topology
    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        num_routers = options.num_cpus
        link_latency = options.link_latency
        router_latency = options.router_latency

        # Ensure there are as many nodes as routers or fewer
        assert len(nodes) <= num_routers

        # Create the routers in the ring
        routers = [
            Router(router_id=i, latency=router_latency)
            for i in range(num_routers)
        ]
        network.routers = routers

        # Link counter to set unique link IDs
        link_count = 0

        # Connect each node to the appropriate router
        ext_links = []
        for (i, node) in enumerate(nodes):
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=node,
                    int_node=routers[i],
                    latency=link_latency,
                )
            )
            link_count += 1

        network.ext_links = ext_links

        # Create the ring links (wrap-around)
        int_links = []

        # Connect each router to the next in the ring
        for i in range(num_routers):
            next_router = (i + 1) % num_routers  # Wrap around to create the ring
            int_links.append(
                IntLink(
                    link_id=link_count,
                    src_node=routers[i],
                    dst_node=routers[next_router],
                    src_outport="East",
                    dst_inport="West",
                    latency=link_latency,
                    weight=1,
                )
            )
            link_count += 1

        for i in range(num_routers):
            next_router = (i - 1 + num_routers) % num_routers  # Wrap around
            int_links.append(
                IntLink(
                    link_id=link_count,
                    src_node=routers[i],
                    dst_node=routers[next_router],
                    src_outport="West",
                    dst_inport="East",
                    latency=link_latency,
                    weight=1,
                )
            )
            link_count += 1

        network.int_links = int_links

    # Register nodes with the filesystem
    def registerTopology(self, options):
        for i in range(len(self.nodes)):
            FileSystemConfig.register_node(
                [i], MemorySize(options.mem_size) // len(self.nodes), i
            )
