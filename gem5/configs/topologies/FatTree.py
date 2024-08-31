# Copyright (c) 2010 Advanced Micro Devices, Inc.
#               2016 Georgia Institute of Technology
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from m5.params import *
from m5.objects import *

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology

# Creates FatTree Topology.
# Uses FatTreeAdaptive routing.


class FatTree(SimpleTopology):
    description = "FatTree"

    def __init__(self, controllers):
        self.nodes = controllers

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        # Router is the class of router, here it is GarnetRouter
        nodes = self.nodes

        num_cpus = options.num_cpus
        num_degree = options.num_pods # k
        half_degree = (num_degree // 2) # k / 2

        # Structure of the FatTree:
        # - Edge layer having k ^ 2 / 2 nodes
        # - Aggregation layer having k ^ 2 / 2 nodes
        # - Core layer having k ^ 2 / 4 nodes 
        # - k pods, each pod containing k / 2 edge switches and k / 2 aggregation switches
        num_edge_layer = half_degree * num_degree 
        num_agg_layer = half_degree * num_degree 
        num_core_layer = half_degree ** 2 
        num_routers = num_edge_layer + num_agg_layer + num_core_layer
        # print(f"num_routers: {num_routers}")
        assert num_routers == num_cpus

        # Default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_edge_layer)

        # Create the routers in the mesh
        routers = [
            Router(router_id=i, latency=router_latency)
            for i in range(num_routers) # edge / agg / core
        ]
        network.routers = routers

        # link counter to set unique link ids
        link_count = 0

        # Add all but the remainder nodes to the list of nodes to be uniformly
        # distributed across the network.
        network_nodes = []
        remainder_nodes = []
        for node_index in range(len(nodes)):
            if node_index < (len(nodes) - remainder):
                network_nodes.append(nodes[node_index])
            else:
                remainder_nodes.append(nodes[node_index])

        # Connect each node to the appropriate router (only to edge routers)
        ext_links = []
        for (i, n) in enumerate(network_nodes):
            cntrl_level, router_id = divmod(i, num_edge_layer)
            assert cntrl_level < cntrls_per_router
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=n,
                    int_node=routers[router_id],
                    latency=link_latency,
                )
            )
            link_count += 1

        # Connect the remainding nodes to router 0.  These should only be
        # DMA nodes.
        for (i, node) in enumerate(remainder_nodes):
            # assert node.type == "DMA_Controller"
            assert i < remainder
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=node,
                    int_node=routers[0],
                    latency=link_latency,
                )
            )
            link_count += 1

        network.ext_links = ext_links

        # Create the internal links.
        int_links = []

        # Router indexing: edge -> agg -> core
        # (Edge, Agg) links (weight = 1)
        for pod_id in range(num_degree):
            for edge_router_id in range(half_degree):
                for agg_router_id in range(half_degree):
                    edge_out = (0) + edge_router_id + (pod_id * half_degree)
                    agg_in = (num_edge_layer) + agg_router_id + (pod_id * half_degree)
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[edge_out],
                            dst_node=routers[agg_in],
                            src_outport=f"Agg{agg_router_id}",
                            dst_inport=f"Edge{edge_router_id}",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

                    edge_in = (0) + edge_router_id + (pod_id * half_degree)
                    agg_out = (num_edge_layer) + agg_router_id + (pod_id * half_degree)
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[agg_out],
                            dst_node=routers[edge_in],
                            src_outport=f"Edge{edge_router_id}",
                            dst_inport=f"Agg{agg_router_id}",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1


        # (Agg, Core) links (weight = 1)
        for core_type in range(half_degree):
            for core_router_id in range(half_degree):
                for pod_id in range(num_degree):
                    agg_router_id = core_type
                    agg_out = (num_edge_layer) + agg_router_id + (pod_id * half_degree)
                    core_in = (num_edge_layer + num_agg_layer) + core_router_id + (core_type * half_degree)
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[agg_out],
                            dst_node=routers[core_in],
                            src_outport=f"Core{core_router_id}",
                            dst_inport=f"Agg{pod_id}",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

                    agg_in = (num_edge_layer) + agg_router_id + (pod_id * half_degree)
                    core_out = (num_edge_layer + num_agg_layer) + core_router_id + (core_type * half_degree)
                    int_links.append(
                        IntLink(
                            link_id=link_count,
                            src_node=routers[core_out],
                            dst_node=routers[agg_in],
                            src_outport=f"Agg{pod_id}",
                            dst_inport=f"Core{core_router_id}",
                            latency=link_latency,
                            weight=1,
                        )
                    )
                    link_count += 1

        network.int_links = int_links

    # Register nodes with filesystem
    def registerTopology(self, options):
        for i in range(options.num_cpus):
            FileSystemConfig.register_node(
                [i], MemorySize(options.mem_size) // options.num_cpus, i
            )
