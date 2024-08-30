/*
 * Copyright (c) 2008 Princeton University
 * Copyright (c) 2016 Georgia Institute of Technology
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */


#include "mem/ruby/network/garnet/RoutingUnit.hh"

#include "base/cast.hh"
#include "base/compiler.hh"
#include "debug/RubyNetwork.hh"
#include "mem/ruby/network/garnet/InputUnit.hh"
#include "mem/ruby/network/garnet/Router.hh"
#include "mem/ruby/slicc_interface/Message.hh"

namespace gem5
{

namespace ruby
{

namespace garnet
{

RoutingUnit::RoutingUnit(Router *router)
{
    m_router = router;
    m_routing_table.clear();
    m_weight_table.clear();
}

void
RoutingUnit::addRoute(std::vector<NetDest>& routing_table_entry)
{
    if (routing_table_entry.size() > m_routing_table.size()) {
        m_routing_table.resize(routing_table_entry.size());
    }
    for (int v = 0; v < routing_table_entry.size(); v++) {
        m_routing_table[v].push_back(routing_table_entry[v]);
    }
}

void
RoutingUnit::addWeight(int link_weight)
{
    m_weight_table.push_back(link_weight);
}

bool
RoutingUnit::supportsVnet(int vnet, std::vector<int> sVnets)
{
    // If all vnets are supported, return true
    if (sVnets.size() == 0) {
        return true;
    }

    // Find the vnet in the vector, return true
    if (std::find(sVnets.begin(), sVnets.end(), vnet) != sVnets.end()) {
        return true;
    }

    // Not supported vnet
    return false;
}

/*
 * This is the default routing algorithm in garnet.
 * The routing table is populated during topology creation.
 * Routes can be biased via weight assignments in the topology file.
 * Correct weight assignments are critical to provide deadlock avoidance.
 */
int
RoutingUnit::lookupRoutingTable(int vnet, NetDest msg_destination)
{
    // First find all possible output link candidates
    // For ordered vnet, just choose the first
    // (to make sure different packets don't choose different routes)
    // For unordered vnet, randomly choose any of the links
    // To have a strict ordering between links, they should be given
    // different weights in the topology file

    int output_link = -1;
    int min_weight = INFINITE_;
    std::vector<int> output_link_candidates;
    int num_candidates = 0;

    // Identify the minimum weight among the candidate output links
    for (int link = 0; link < m_routing_table[vnet].size(); link++) {
        if (msg_destination.intersectionIsNotEmpty(
            m_routing_table[vnet][link])) {

        if (m_weight_table[link] <= min_weight)
            min_weight = m_weight_table[link];
        }
    }

    // Collect all candidate output links with this minimum weight
    for (int link = 0; link < m_routing_table[vnet].size(); link++) {
        if (msg_destination.intersectionIsNotEmpty(
            m_routing_table[vnet][link])) {

            if (m_weight_table[link] == min_weight) {
                num_candidates++;
                output_link_candidates.push_back(link);
            }
        }
    }

    if (output_link_candidates.size() == 0) {
        fatal("Fatal Error:: No Route exists from this Router.");
        exit(0);
    }

    // Randomly select any candidate output link
    int candidate = 0;
    if (!(m_router->get_net_ptr())->isVNetOrdered(vnet))
        candidate = rand() % num_candidates;

    output_link = output_link_candidates.at(candidate);
    return output_link;
}


void
RoutingUnit::addInDirection(PortDirection inport_dirn, int inport_idx)
{
    m_inports_dirn2idx[inport_dirn] = inport_idx;
    m_inports_idx2dirn[inport_idx]  = inport_dirn;
}

void
RoutingUnit::addOutDirection(PortDirection outport_dirn, int outport_idx)
{
    m_outports_dirn2idx[outport_dirn] = outport_idx;
    m_outports_idx2dirn[outport_idx]  = outport_dirn;
}

// outportCompute() is called by the InputUnit
// It calls the routing table by default.
// A template for adaptive topology-specific routing algorithm
// implementations using port directions rather than a static routing
// table is provided here.

int
RoutingUnit::outportCompute(RouteInfo route, int inport,
                            PortDirection inport_dirn)
{
    int outport = -1;

    if (route.dest_router == m_router->get_id()) {

        // Multiple NIs may be connected to this router,
        // all with output port direction = "Local"
        // Get exact outport id from table
        outport = lookupRoutingTable(route.vnet, route.net_dest);
        return outport;
    }

    // Routing Algorithm set in GarnetNetwork.py
    // Can be over-ridden from command line using --routing-algorithm = 1
    RoutingAlgorithm routing_algorithm =
        (RoutingAlgorithm) m_router->get_net_ptr()->getRoutingAlgorithm();

    switch (routing_algorithm) {
        case TABLE_:  outport =
            lookupRoutingTable(route.vnet, route.net_dest); break;
        case XY_:     outport =
            outportComputeXY(route, inport, inport_dirn); break;
        // any custom algorithm
        case CUSTOM_: outport =
            outportComputeCustom(route, inport, inport_dirn); break;
        /// lab4
        case FATTREE_: outport = 
            outportComputeFatTree(route, inport, inport_dirn); break;
        case FATTREE_ADAPTIVE_: outport =
            outportComputeFatTreeAdaptive(route, inport, inport_dirn); break;

        default: outport =
            lookupRoutingTable(route.vnet, route.net_dest); break;
    }

    assert(outport != -1);
    return outport;
}

// XY routing implemented using port directions
// Only for reference purpose in a Mesh
// By default Garnet uses the routing table
int
RoutingUnit::outportComputeXY(RouteInfo route,
                              int inport,
                              PortDirection inport_dirn)
{
    PortDirection outport_dirn = "Unknown";

    [[maybe_unused]] int num_rows = m_router->get_net_ptr()->getNumRows();
    int num_cols = m_router->get_net_ptr()->getNumCols();
    assert(num_rows > 0 && num_cols > 0);

    int my_id = m_router->get_id();
    int my_x = my_id % num_cols;
    int my_y = my_id / num_cols;

    int dest_id = route.dest_router;
    int dest_x = dest_id % num_cols;
    int dest_y = dest_id / num_cols;

    int x_hops = abs(dest_x - my_x);
    int y_hops = abs(dest_y - my_y);

    bool x_dirn = (dest_x >= my_x);
    bool y_dirn = (dest_y >= my_y);

    // already checked that in outportCompute() function
    assert(!(x_hops == 0 && y_hops == 0));

    if (x_hops > 0) {
        if (x_dirn) {
            assert(inport_dirn == "Local" || inport_dirn == "West");
            outport_dirn = "East";
        } else {
            assert(inport_dirn == "Local" || inport_dirn == "East");
            outport_dirn = "West";
        }
    } else if (y_hops > 0) {
        if (y_dirn) {
            // "Local" or "South" or "West" or "East"
            assert(inport_dirn != "North");
            outport_dirn = "North";
        } else {
            // "Local" or "North" or "West" or "East"
            assert(inport_dirn != "South");
            outport_dirn = "South";
        }
    } else {
        // x_hops == 0 and y_hops == 0
        // this is not possible
        // already checked that in outportCompute() function
        panic("x_hops == y_hops == 0");
    }

    return m_outports_dirn2idx[outport_dirn];
}

// Template for implementing custom routing algorithm
// using port directions. (Example adaptive)
int
RoutingUnit::outportComputeCustom(RouteInfo route,
                                 int inport,
                                 PortDirection inport_dirn)
{
    panic("%s placeholder executed", __FUNCTION__);
}

/// Base of lab4: FatTree Routing
int
RoutingUnit::outportComputeFatTree(RouteInfo route,
                                   int inport,
                                   PortDirection inport_dirn)
{
    PortDirection outport_dirn = "Unknown";
    int k = m_router->get_net_ptr()->getNumPods(); // tree degree, num_pods, k
    int half_k = k / 2;
    int num_edge_layer = half_k * k;
    int num_agg_layer = half_k * k;
    int num_core_layer = half_k * half_k;
    int my_id = m_router->get_id();

    // This function calculates the next direction if we want to go from 
    //   the current router to the desired route.dest_router, which must 
    //   be an edge router. 
    // Determine layer of current router

    int my_layer;
    if (my_id < num_edge_layer) {
        my_layer = 0; // EDGE
    } else if (my_id < num_edge_layer + num_agg_layer) {
        my_layer = 1; // AGGREGATION
    } else {
        my_layer = 2; // CORE
    }

    // srand((int)time(0));
    // std :: cout << "my_layer: " << my_layer << " dest_layer: " << dest_layer << std :: endl;
    // std :: cout << "k: " << k << "num_edge_layer: " << num_edge_layer << std::endl;
    // std :: cout << "my_id: " << my_id << "dest_id: " << dest_id << std :: endl; 
    // assert(dest_id < num_edge_layer);
    
    if (my_layer == 0) { // EDGE
        int my_pos = my_id % half_k;
        /// Upwards to my aggregation router; Can become adaptive later
        outport_dirn = "Agg" + std::to_string(my_pos);
    } else if (my_layer == 1) { // AGGREGATION
        int my_pod = (my_id - num_edge_layer) / half_k;
        int my_pos = my_id % half_k;
        int dest_id = route.dest_router;
        if (dest_id / half_k == my_pod) {
            // Destination is an edge router in the same pod
            outport_dirn = "Edge" + std::to_string(dest_id % half_k);
        } else {
            // Upwards to my core router; Can become adaptive later
            outport_dirn = "Core" + std::to_string(my_pos);
        }
    } else if (my_layer == 2) { // CORE
        // Downwards to the correct aggregation router in the destination pod
        int dest_id = route.dest_router;
        int dest_pod = dest_id / half_k;
        outport_dirn = "Agg" + std::to_string(dest_pod);
    } else {
        panic("Invalid router layer determined");
    }

    return m_outports_dirn2idx[outport_dirn];
}


/// lab4: FatTree Adaptive Routing
int
RoutingUnit::outportComputeFatTreeAdaptive(RouteInfo route,
                                           int inport,
                                           PortDirection inport_dirn)
{
    return outportComputeFatTree(route, inport, inport_dirn);
    // PortDirection outport_dirn = "Unknown";
    // int k = m_router->get_net_ptr()->getNumPods(); // tree degree, num_pods, k
    // int half_k = k / 2;

    // int num_edge_layer = half_k * k;
    // int num_agg_layer = half_k * k;
    // int num_core_layer = (half_k * half_k);

    // int my_id = m_router->get_id();

    // // Determine layer of current router
    // int my_layer;
    // if (my_id < num_edge_layer) {
    //     my_layer = 0; // EDGE
    // } else if (my_id < num_edge_layer + num_agg_layer) {
    //     my_layer = 1; // AGGREGATION
    // } else {
    //     my_layer = 2; // CORE
    // }

    // int dest_id = route.dest_router;

    // int my_pod = my_id / (k * half_k);
    // int my_pos_within_pod = my_id % half_k;

    // std::ostringstream ss;
    // if (my_layer == 0) { // EDGE
    //     if (my_pod == dest_id / (k * half_k)) {
    //         // Destination is within the same pod
    //         if (dest_id < num_edge_layer) {
    //             // Destination is an edge router in the same pod
    //             if (my_id == dest_id) {
    //                 outport_dirn = "Local";
    //             } else {
    //                 ss << "Agg" << my_pos_within_pod;
    //                 outport_dirn = chooseLeastCongested(ss.str(), half_k);
    //             }
    //         } else {
    //             // Destination is an aggregation router in the same pod
    //             outport_dirn = chooseLeastCongested(dest_id, half_k);
    //         }
    //     } else {
    //         // Destination is in a different pod, route to my aggregation router
    //         outport_dirn = chooseLeastCongested(my_pod, half_k);
    //     }
    // } else if (my_layer == 1) { // AGGREGATION
    //     if (my_pod == dest_id / (k * half_k)) {
    //         // Destination is an edge router in the same pod
    //         ss << "Edge" << (dest_id % half_k);
    //         outport_dirn = ss.str();
    //     } else {
    //         // Route to appropriate core based on the destination pod and position
    //         outport_dirn = chooseLeastCongestedCore(dest_id, half_k, num_core_layer);
    //     }
    // } else if (my_layer == 2) { // CORE
    //     // Route down to the correct aggregation router in the destination pod
    //     outport_dirn = chooseLeastCongestedAgg(dest_id, half_k, num_agg_layer);
    // } else {
    //     panic("Invalid router layer determined");
    // }
    

    // return m_outports_dirn2idx[outport_dirn];
}

// Example helper function to choose the least congested link
std::string RoutingUnit::chooseLeastCongested(std::string basePort, int half_k) {
    int min_congestion = INT_MAX;
    std::string least_congested_port = basePort;
    for (int i = 0; i < half_k; i++) {
        std::ostringstream ss;
        ss << basePort << i;
        int congestion = getCongestionLevel(ss.str());
        if (congestion < min_congestion) {
            min_congestion = congestion;
            least_congested_port = ss.str();
        }
    }
    return least_congested_port;
}

int RoutingUnit::getCongestionLevel(std::string portName) {
    // Retrieve congestion level for the port
    // This function needs to be implemented based on how congestion data is collected and stored
    return 0; // Placeholder
}

} // namespace garnet
} // namespace ruby
} // namespace gem5
