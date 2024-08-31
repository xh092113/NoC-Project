### Code Structure

- src/mem/ruby/network/garnet
  - GarnetNetwork.cc
    - 
- configs
  - example
    - garnet_synth_traffic.py
  - network
    - Network.py
  - topologies



- 代码中GarnetSyntheticTraffic是白的，解决方案：
  - https://jianyue.tech/posts/gem5/

## Lab1

### Task 1

- Original result

```

packets_injected = 5                       (Unspecified)
packets_received = 2                       (Unspecified)
average_packet_queueing_latency = 1000                       (Unspecified)
average_packet_network_latency = 3000                       (Unspecified)
average_packet_latency = 4000                       (Unspecified)
average_hops = 1.500000                       (Unspecified)

```

- Result after changing GlobalFrequency to 2GHz

```

packets_injected = 3165                       (Unspecified)
packets_received = 3162                       (Unspecified)
average_packet_queueing_latency = 2                       (Unspecified)
average_packet_network_latency = 13.557559                       (Unspecified)
average_packet_latency = 15.557559                       (Unspecified)
average_hops = 5.269450                       (Unspecified)

```

### Task2

- Complete the units

  - In GarnetNetwork.cc, around line 520, add .unit(statistics::units::Count::get()) and .desc() to variables that are output in the stats.txt.
  - 所有的average latency都是Rate<Tick, Count>, 其他的都是Count
  - 注意要写成statistics::units::Rate<statistics::units::Tick, statistics::units::Count>::get()
  - 可以选的单位有cycle, tick, second, bit, byte, watt, joule, volt, degreecelsius, count, ratio, unspecified, rate<T1, T2>
  - 一个cycle是好几个tick
  - count是数量，ratio是数量除出来的东西

- ```
  ./build/NULL/gem5.opt \
  configs/example/garnet_synth_traffic.py \
  --network=garnet --num-cpus=64 --num-dirs=64 \
  --topology=Mesh_XY --mesh-rows=8 \
  --inj-vnet=0 --synthetic=uniform_random \
  --sim-cycles=10000 --injectionrate=0.01 
  
  echo > network_stats.txt
  grep "packets_injected::total" m5out/stats.txt | sed 's/system.ruby.network.packets_injected::total\s*/packets_injected = /' >> network_stats.txt
  grep "packets_received::total" m5out/stats.txt | sed 's/system.ruby.network.packets_received::total\s*/packets_received = /' >> network_stats.txt
  grep "average_packet_queueing_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_queueing_latency\s*/average_packet_queueing_latency = /' >> network_stats.txt
  grep "average_packet_network_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_network_latency\s*/average_packet_network_latency = /' >> network_stats.txt
  grep "average_packet_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_latency\s*/average_packet_latency = /' >> network_stats.txt
  grep "average_hops" m5out/stats.txt | sed 's/system.ruby.network.average_hops\s*/average_hops = /' >> network_stats.txt
  
  # 获取 total_packets_received
  total_packets_received=$(grep "packets_received::total" m5out/stats.txt | awk '{print $2}')
  
  # 获取 num_cpus
  num_cpus=$(grep -c "cpu" m5out/stats.txt)
  
  # 获取 sim_cycles
  sim_cycles=$(grep "simTicks" m5out/stats.txt | awk '{print $2}')
  
  # 计算 reception_rate
  reception_rate=$(echo "$total_packets_received / $num_cpus / $sim_cycles" | bc -l)
  
  # 输出 reception_rate 到 network_stats.txt
  echo "reception_rate = $reception_rate" >> network_stats.txt
  
  ```

- cycle和tick有什么区别？看上去指令里的sim-cycles就是stats.txt输出中的simTicks

  - sim-cycles实际上应该叫sim-ticks

- ticks好像会自动补足到偶数 比如sim-cycle=9999的时候就会执行10000个tick，10001的时候就会执行10002个

- Input parameter options for garnet_synth_traffic.py:

  - ```bash
    ./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py -h
    ```

  - ```
    usage: garnet_synth_traffic.py [-h] [-n NUM_CPUS] [--sys-voltage SYS_VOLTAGE]
                                   [--sys-clock SYS_CLOCK] [--list-mem-types]
                                   [--mem-type {CfiMemory,DDR3_1600_8x8,DDR3_2133_8x8,DDR4_2400_16x4,DDR4_2400_4x16,DDR4_2400_8x8,DDR5_4400_4x8,DDR5_6400_4x8,DDR5_8400_4x8,DRAMInterface,GDDR5_4000_2x32,HBM_1000_4H_1x128,HBM_1000_4H_1x64,HBM_2000_4H_1x64,HMC_2500_1x32,LPDDR2_S4_1066_1x32,LPDDR3_1600_1x32,LPDDR5_5500_1x16_8B_BL32,LPDDR5_5500_1x16_BG_BL16,LPDDR5_5500_1x16_BG_BL32,LPDDR5_6400_1x16_8B_BL32,LPDDR5_6400_1x16_BG_BL16,LPDDR5_6400_1x16_BG_BL32,NVMInterface,NVM_2400_1x64,QoSMemSinkInterface,SimpleMemory,WideIO_200_1x128}]
                                   [--mem-channels MEM_CHANNELS]
                                   [--mem-ranks MEM_RANKS] [--mem-size MEM_SIZE]
                                   [--enable-dram-powerdown]
                                   [--mem-channels-intlv MEM_CHANNELS_INTLV]
                                   [--memchecker]
                                   [--external-memory-system EXTERNAL_MEMORY_SYSTEM]
                                   [--tlm-memory TLM_MEMORY] [--caches]
                                   [--l2cache] [--num-dirs NUM_DIRS]
                                   [--num-l2caches NUM_L2CACHES]
                                   [--num-l3caches NUM_L3CACHES]
                                   [--l1d_size L1D_SIZE] [--l1i_size L1I_SIZE]
                                   [--l2_size L2_SIZE] [--l3_size L3_SIZE]
                                   [--l1d_assoc L1D_ASSOC] [--l1i_assoc L1I_ASSOC]
                                   [--l2_assoc L2_ASSOC] [--l3_assoc L3_ASSOC]
                                   [--cacheline_size CACHELINE_SIZE] [--ruby]
                                   [-m TICKS] [--rel-max-tick TICKS]
                                   [--maxtime MAXTIME] [-P PARAM]
                                   [--synthetic {uniform_random,tornado,bit_complement,bit_reverse,bit_rotation,neighbor,shuffle,transpose}]
                                   [-i I] [--precision PRECISION]
                                   [--sim-cycles SIM_CYCLES]
                                   [--num-packets-max NUM_PACKETS_MAX]
                                   [--single-sender-id SINGLE_SENDER_ID]
                                   [--single-dest-id SINGLE_DEST_ID]
                                   [--inj-vnet {-1,0,1,2}]
                                   [--ruby-clock RUBY_CLOCK]
                                   [--access-backing-store] [--ports PORTS]
                                   [--numa-high-bit NUMA_HIGH_BIT]
                                   [--interleaving-bits INTERLEAVING_BITS]
                                   [--xor-low-bit XOR_LOW_BIT]
                                   [--recycle-latency RECYCLE_LATENCY]
                                   [--topology TOPOLOGY] [--mesh-rows MESH_ROWS]
                                   [--network {simple,garnet}]
                                   [--router-latency ROUTER_LATENCY]
                                   [--link-latency LINK_LATENCY]
                                   [--link-width-bits LINK_WIDTH_BITS]
                                   [--vcs-per-vnet VCS_PER_VNET]
                                   [--routing-algorithm ROUTING_ALGORITHM]
                                   [--network-fault-model]
                                   [--garnet-deadlock-threshold GARNET_DEADLOCK_THRESHOLD]
                                   [--simple-physical-channels]
    
    options:
      -h, --help            show this help message and exit
      -n NUM_CPUS, --num-cpus NUM_CPUS
      --sys-voltage SYS_VOLTAGE
                            Top-level voltage for blocks running at system power
                            supply
      --sys-clock SYS_CLOCK
                            Top-level clock for blocks running at system speed
      --list-mem-types      List available memory types
      --mem-type {CfiMemory,DDR3_1600_8x8,DDR3_2133_8x8,DDR4_2400_16x4,DDR4_2400_4x16,DDR4_2400_8x8,DDR5_4400_4x8,DDR5_6400_4x8,DDR5_8400_4x8,DRAMInterface,GDDR5_4000_2x32,HBM_1000_4H_1x128,HBM_1000_4H_1x64,HBM_2000_4H_1x64,HMC_2500_1x32,LPDDR2_S4_1066_1x32,LPDDR3_1600_1x32,LPDDR5_5500_1x16_8B_BL32,LPDDR5_5500_1x16_BG_BL16,LPDDR5_5500_1x16_BG_BL32,LPDDR5_6400_1x16_8B_BL32,LPDDR5_6400_1x16_BG_BL16,LPDDR5_6400_1x16_BG_BL32,NVMInterface,NVM_2400_1x64,QoSMemSinkInterface,SimpleMemory,WideIO_200_1x128}
                            type of memory to use
      --mem-channels MEM_CHANNELS
                            number of memory channels
      --mem-ranks MEM_RANKS
                            number of memory ranks per channel
      --mem-size MEM_SIZE   Specify the physical memory size (single memory)
      --enable-dram-powerdown
                            Enable low-power states in DRAMInterface
      --mem-channels-intlv MEM_CHANNELS_INTLV
                            Memory channels interleave
      --memchecker
      --external-memory-system EXTERNAL_MEMORY_SYSTEM
                            use external ports of this port_type for caches
      --tlm-memory TLM_MEMORY
                            use external port for SystemC TLM cosimulation
      --caches
      --l2cache
      --num-dirs NUM_DIRS
      --num-l2caches NUM_L2CACHES
      --num-l3caches NUM_L3CACHES
      --l1d_size L1D_SIZE
      --l1i_size L1I_SIZE
      --l2_size L2_SIZE
      --l3_size L3_SIZE
      --l1d_assoc L1D_ASSOC
      --l1i_assoc L1I_ASSOC
      --l2_assoc L2_ASSOC
      --l3_assoc L3_ASSOC
      --cacheline_size CACHELINE_SIZE
      --ruby
      -m TICKS, --abs-max-tick TICKS
                            Run to absolute simulated tick specified including
                            ticks from a restored checkpoint
      --rel-max-tick TICKS  Simulate for specified number of ticks relative to the
                            simulation start tick (e.g. if restoring a checkpoint)
      --maxtime MAXTIME     Run to the specified absolute simulated time in
                            seconds
      -P PARAM, --param PARAM
                            Set a SimObject parameter relative to the root node.
                            An extended Python multi range slicing syntax can be
                            used for arrays. For example:
                            'system.cpu[0,1,3:8:2].max_insts_all_threads = 42'
                            sets max_insts_all_threads for cpus 0, 1, 3, 5 and 7
                            Direct parameters of the root object are not
                            accessible, only parameters of its children.
      --synthetic {uniform_random,tornado,bit_complement,bit_reverse,bit_rotation,neighbor,shuffle,transpose}
      -i I, --injectionrate I
                            Injection rate in packets per cycle per node. Takes
                            decimal value between 0 to 1 (eg. 0.225). Number of
                            digits after 0 depends upon --precision.
      --precision PRECISION
                            Number of digits of precision after decimal point for
                            injection rate
      --sim-cycles SIM_CYCLES
                            Number of simulation cycles
      --num-packets-max NUM_PACKETS_MAX
                            Stop injecting after --num-packets-max. Set to -1 to
                            disable.
      --single-sender-id SINGLE_SENDER_ID
                            Only inject from this sender. Set to -1 to disable.
      --single-dest-id SINGLE_DEST_ID
                            Only send to this destination. Set to -1 to disable.
      --inj-vnet {-1,0,1,2}
                            Only inject in this vnet (0, 1 or 2). 0 and 1 are
                            1-flit, 2 is 5-flit. Set to -1 to inject randomly in
                            all vnets.
      --ruby-clock RUBY_CLOCK
                            Clock for blocks running at Ruby system's speed
      --access-backing-store
                            Should ruby maintain a second copy of memory
      --ports PORTS         used of transitions per cycle which is a proxy for the
                            number of ports.
      --numa-high-bit NUMA_HIGH_BIT
                            high order address bit to use for numa mapping. 0 =
                            highest bit, not specified = lowest bit
      --interleaving-bits INTERLEAVING_BITS
                            number of bits to specify interleaving in directory,
                            memory controllers and caches. 0 = not specified
      --xor-low-bit XOR_LOW_BIT
                            hashing bit for channel selectionsee MemConfig for
                            explanation of the defaultparameter. If set to 0,
                            xor_high_bit is alsoset to 0.
      --recycle-latency RECYCLE_LATENCY
                            Recycle latency for ruby controller input buffers
      --topology TOPOLOGY   check configs/topologies for complete set
      --mesh-rows MESH_ROWS
                            the number of rows in the mesh topology
      --network {simple,garnet}
                            'simple'|'garnet' (garnet2.0 will be deprecated.)
      --router-latency ROUTER_LATENCY
                            number of pipeline stages in the garnet router. Has to
                            be >= 1. Can be over-ridden on a per router basis in
                            the topology file.
      --link-latency LINK_LATENCY
                            latency of each link the simple/garnet networks. Has
                            to be >= 1. Can be over-ridden on a per link basis in
                            the topology file.
      --link-width-bits LINK_WIDTH_BITS
                            width in bits for all links inside garnet.
      --vcs-per-vnet VCS_PER_VNET
                            number of virtual channels per virtual network inside
                            garnet network.
      --routing-algorithm ROUTING_ALGORITHM
                            routing algorithm in network. 0: weight-based table 1:
                            XY (for Mesh. see garnet/RoutingUnit.cc) 2: Custom
                            (see garnet/RoutingUnit.cc
      --network-fault-model
                            enable network fault model: see
                            src/mem/ruby/network/fault_model/
      --garnet-deadlock-threshold GARNET_DEADLOCK_THRESHOLD
                            network-level deadlock threshold.
      --simple-physical-channels
                            SimpleNetwork links uses a separate physical channel
                            for each virtual network
    ```

- unit of sim-cycles: tick.

- unit of router-latency: Tick

- unit of link-latency: Tick

- The relationship betw Tick and Cycle: One cycle = multiple Ticks. 

- unit of injection rate: Rate<Count, Count>, which is Ratio

  - sysclock是对应cycle时间，默认都是1GHz，也就是一个cycle是1e-9s
  - global frequency是对应tick时间，比如2GHz说明一个tick是5e-10s

- 似乎cpu数量是无量纲的，count只是用来描述包的数量以及tick等的数量的（？）

- Definition of GarnetNetworkInterface and GarnetRouter: src/mem/ruby/network/garnet/GarnetNetwork.py

- 跳Tick在src/cpu/testers/garnet_synthetic_traffic/GarnetSyntheticTraffic.cc里的GarnetSyntheticTraffic::tick()实现，按照injRate比例发包，如果决定发包，发包在GarnetSyntheticTraffic::generatePkt()里实现。

- src/cpu/testers/garnet_synthetic_traffic/GarnetSyntheticTraffic.cc::sendPkt中，sendTimingReq是一个尝试发包的函数，如果发包不成功，就先存到retryPkt里，然后后面由RubyPort去管重发的事情。sendTimingReq在/home/coder66/Desktop/U2-C/AI+X/gem5/src/mem/port.hh里，继续调用/home/coder66/Desktop/U2-C/AI+X/gem5/src/mem/protocol/functional.cc里的send，然后调用/home/coder66/Desktop/U2-C/AI+X/gem5/src/systemc/tlm_bridge/gem5_to_tlm.cc里的recvFunctional，其中调用socket->transport_dbg，但是不知道在哪里

## Lab2

### Task1

- latency-throughput图，按要求，横坐标是injection rate, 纵坐标是各种latency
- 因为是要求10000个sys clock的cycle，所以在2GHz的情况下，sim-cycle应该调成20000（代表20000个tick）
- 

## Lab3 & 4

- 要加routing的话，要改RoutingUnit.hh，改gem5/src/mem/ruby/network/garnet里CommonTypes.hh里的enum Routing Algorithm，和RoutingUnit.hh里的RoutingUnit

- 要加选项的话，比如加NumPods这个选项，要在GarnetNetwork.hh里加函数和变量，然后在Network.py里加parser选项和init_network()，然后要改GarnetNetwork.cc里面的Init，GarnetNetwork()和GarnetNetwork.py里的class GarnetNetwork

- 跑普通routing:

- ```
  ./build/NULL/gem5.opt \
  configs/example/garnet_synth_traffic.py \
  --network=garnet --num-cpus=20 --num-dirs=64 \
  --topology=FatTree --num-pods=4 \
  --inj-vnet=0 --synthetic=uniform_random \
  --sim-cycles=100000 --injectionrate=0.01 --routing-algorithm={TABLE_ = 0, XY_ = 1, CUSTOM_ = 2, FATTREE_ = 3, FATTREE_ADAPTIVE_ = 4, NUM_ROUTING_ALGORITHM_}
  
  scons build/NULL/gem5.opt PROTOCOL=Garnet_standalone -j $(nproc)
  ```

- router的定义在GarnetNetwork.py里的class GarnetRouter里

- 【更正：不能这么做，因为router里引Garnetnetwork，所以会循环引用】自己加congestion value可以定义在router.hh里，然后在GarnetNetwork里给一个id->router*的api并include router.hh

- 自己加congestion value可以定义在GarnetNetwork里
