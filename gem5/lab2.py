import os
import subprocess
import re
import matplotlib.pyplot as plt

# Parameters
network = "garnet"
num_cpus = 64
num_dirs = 64
topology = "Mesh_XY"
mesh_rows = 8
inj_vnet = 0
traffic_type = "uniform_random"  # You can modify this later if needed
sim_cycles = 20000
injection_rates = [i / 100.0 for i in range(1, 51)]  # 0.01 to 0.5 in steps of 0.01
gem5_exec = "./build/NULL/gem5.opt"
config_script = "configs/example/garnet_synth_traffic.py"
output_dir = "m5out"
stat_file = os.path.join(output_dir, "stats.txt")

# Initialize lists for plotting
avg_queueing_latencies = []
avg_network_latencies = []
avg_latencies = []
avg_hops = []

# Run simulations for each injection rate
for inj_rate in injection_rates:
    print(f"Running simulation for injection rate: {inj_rate}")
    # Build the command
    command = [
        gem5_exec,
        config_script,
        f"--network={network}",
        f"--num-cpus={num_cpus}",
        f"--num-dirs={num_dirs}",
        f"--topology={topology}",
        f"--mesh-rows={mesh_rows}",
        f"--inj-vnet={inj_vnet}",
        f"--synthetic={traffic_type}",
        f"--sim-cycles={sim_cycles}",
        f"--injectionrate={inj_rate}"
    ]
    
    # Run the simulation
    print(f"Running simulation with injection rate: {inj_rate}")
    subprocess.run(command, check=True)
    
    # Extract relevant data from stats.txt
    with open(stat_file, 'r') as f:
        stats_data = f.read()
    
    # Use regular expressions to find specific stats
    avg_queueing_latency_match = re.search(r'system.ruby.network.average_packet_queueing_latency\s+(\d+(\.\d+)?)', stats_data)
    avg_network_latency_match = re.search(r'system.ruby.network.average_packet_network_latency\s+(\d+(\.\d+)?)', stats_data)
    avg_latency_match = re.search(r'system.ruby.network.average_packet_latency\s+(\d+(\.\d+)?)', stats_data)
    avg_hop_match = re.search(r'system.ruby.network.average_hops\s+(\d+(\.\d+)?)', stats_data)
    
    if avg_latency_match and avg_hop_match:
        avg_queueing_latency = float(avg_queueing_latency_match.group(1))
        avg_network_latency = float(avg_network_latency_match.group(1))
        avg_latency = float(avg_latency_match.group(1))
        avg_hop = float(avg_hop_match.group(1))
        
        avg_queueing_latencies.append(avg_queueing_latency)
        avg_network_latencies.append(avg_network_latency)
        avg_latencies.append(avg_latency)
        avg_hops.append(avg_hop)

        print(f"Average Queueing Latency: {avg_queueing_latency}")
        print(f"Average Network Latency: {avg_network_latency}")
        print(f"Average Latency: {avg_latency}")
        print(f"Average Hops: {avg_hop}")
    else:
        print(f"Warning: Failed to extract stats for injection rate {inj_rate}")

# Plotting the results
plt.figure(figsize=(10, 6))
plt.plot(injection_rates, avg_queueing_latencies, label='Average Queueing Latency (cycles)', marker='o')
plt.plot(injection_rates, avg_network_latencies, label='Average Network Latency (cycles)', marker='o')
plt.plot(injection_rates, avg_latencies, label='Average Latency (cycles)', marker='o')
plt.plot(injection_rates, avg_hops, label='Average Hops', marker='x')
plt.xlabel('Injection Rate')
plt.ylabel('Metrics')
plt.title('Network Performance Metrics vs. Injection Rate')
plt.legend()
plt.grid(True)
plt.savefig('lab2-result.png')
plt.show()
