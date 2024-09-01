from tqdm import tqdm
import subprocess
import numpy as np
import re
import pickle
import matplotlib.pyplot as plt
import os
from os.path import join

ROUTING_MAP = {0:"TABLE", 1:"XY", 3:"DETERMINISTIC", 4:"ADAPTIVE"}
SAVE_DIR = "./Lab4"

def get_title_name(topology, routing_algorithm, num_pods, mesh_rows, num_cpus):
    title_name = f"{topology}_routing_{ROUTING_MAP[routing_algorithm]}"
    if num_pods > 0:
        title_name = f"k={num_pods}_" + title_name
    if mesh_rows > 0:
        mesh_cols = num_cpus // mesh_rows
        title_name = f"{mesh_rows}x{mesh_cols}_" + title_name
    return title_name

def run_stats(topology, routing_algorithm, base_command, num_cpus=20, num_dirs=64, synthetic="uniform_random", num_pods=0, mesh_rows=0):
    base_command = base_command + f"--num-cpus={num_cpus} --num-dirs={num_dirs} --topology={topology} --synthetic={synthetic} --sim-cycles=100000 --routing-algorithm={routing_algorithm}"
    if num_pods > 0:
        base_command += f" --num-pods={num_pods}"
    if mesh_rows > 0:
        base_command += f" --mesh-rows={mesh_rows}"

    injection_rates = [0.01] + np.arange(0.05, 0.71, 0.05).tolist()
    injRate_list = []
    latency_list = []
    network_latency_list = []
    queueing_latency_list = []                         
    average_hops_list = [] 
    reception_rate_list = []

    with tqdm(injection_rates) as pbar:
        for rate in pbar:
            pbar.set_description("injRate {:.2f}".format(rate))
            command = f"{base_command} --injectionrate={rate}"
            subprocess.run(command, shell=True, check=True)
            stats_commands = [
                'echo > network_stats.txt',
                'grep "packets_injected::total" m5out/stats.txt | sed \'s/system.ruby.network.packets_injected::total\\s*/packets_injected = /\' >> network_stats.txt',
                'grep "packets_received::total" m5out/stats.txt | sed \'s/system.ruby.network.packets_received::total\\s*/packets_received = /\' >> network_stats.txt',
                'grep "average_packet_queueing_latency" m5out/stats.txt | sed \'s/system.ruby.network.average_packet_queueing_latency\\s*/average_packet_queueing_latency = /\' >> network_stats.txt',
                'grep "average_packet_network_latency" m5out/stats.txt | sed \'s/system.ruby.network.average_packet_network_latency\\s*/average_packet_network_latency = /\' >> network_stats.txt',
                'grep "average_packet_latency" m5out/stats.txt | sed \'s/system.ruby.network.average_packet_latency\\s*/average_packet_latency = /\' >> network_stats.txt',
                'grep "average_hops" m5out/stats.txt | sed \'s/system.ruby.network.average_hops\\s*/average_hops = /\' >> network_stats.txt',
            ]

            for cmd in stats_commands:
                subprocess.run(cmd, shell=True, check=True)

            total_packets_received = subprocess.run('grep "packets_received::total" m5out/stats.txt | awk \'{print $2}\'', shell=True, check=True, stdout=subprocess.PIPE).stdout.strip()
            num_cpus = subprocess.run('grep -c "cpu" m5out/stats.txt', shell=True, check=True, stdout=subprocess.PIPE).stdout.strip()
            sim_cycles = subprocess.run('grep "simTicks" m5out/stats.txt | awk \'{print $2}\'', shell=True, check=True, stdout=subprocess.PIPE).stdout.strip()

            total_packets_received = float(total_packets_received)
            num_cpus = int(num_cpus)
            sim_cycles = int(sim_cycles)
            reception_rate = total_packets_received / num_cpus / sim_cycles

            with open('network_stats.txt', 'a') as f:
                f.write(f'reception_rate = {reception_rate}\n')


            
            with open('network_stats.txt', 'r') as file:
                content = file.read()

            def find_stats(content, stat_name, stat_list):
                search_pattern = r" = (\d+\.?\d*)"
                stat_value_str = re.search(stat_name + search_pattern, content)

                if stat_value_str:
                    stat_value = stat_value_str.group(1)
                    print(f"{stat_name} {float(stat_value)}")
                    stat_list.append(float(stat_value))
                else:
                    search_pattern = r" = (\.?\d*)"
                    stat_value_str = re.search(stat_name + search_pattern, content)

                    if stat_value_str:
                        stat_value = "0" + stat_value_str.group(1)
                        print(f"{stat_name} {float(stat_value)}")
                        stat_list.append(float(stat_value))
                    else:
                        print(f"未找到 '{stat_name}' 的值")
                        input()
                        stat_list.append(-100)

            injRate_list.append(rate)
            find_stats(content, "average_packet_latency", latency_list)
            find_stats(content, "average_packet_network_latency", network_latency_list)
            find_stats(content, "average_packet_queueing_latency", queueing_latency_list)
            find_stats(content, "average_hops", average_hops_list)
            find_stats(content, "reception_rate", reception_rate_list)
            title_name_prefix = get_title_name(topology, routing_algorithm, num_pods, mesh_rows, num_cpus)
            pbar.set_description(title_name_prefix)
            plt.clf()
            plt.plot(injRate_list, latency_list, marker='o', label="total_latency") 
            plt.plot(injRate_list, network_latency_list, marker='s', label="network_latency")  
            plt.plot(injRate_list, queueing_latency_list, marker='^', label="queueing_latency")  
            plt.legend()
            plt.title(title_name_prefix + "Latency-Throughput")
            plt.xlabel("Injection Rate")
            plt.ylabel("Average Packet Latency")
            plt.grid(True) 
            plt.savefig(join(SAVE_DIR, f"subplot_{title_name_prefix}_LT_curve.jpg"))
        
    title_name_prefix = get_title_name(topology, routing_algorithm, num_pods, mesh_rows, num_cpus)
    print(title_name_prefix)
    pickle.dump({
                    "latency_list": latency_list, 
                    "network_latency_list": network_latency_list, 
                    "queueing_latency_list": queueing_latency_list,
                    "average_hops_list": average_hops_list,
                    "reception_rate_list": reception_rate_list,
                }, 
                open(join(SAVE_DIR, f"{title_name_prefix}_LT_stats.pkl"), "wb"))

os.makedirs(SAVE_DIR, exist_ok=True)
base_command = "./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py --network=garnet --inj-vnet=0 "
# routing
run_stats(topology="FatTree", routing_algorithm=4, base_command=base_command, num_cpus=64, num_dirs=64, synthetic="uniform_random", num_pods=8)
run_stats(topology="FatTree", routing_algorithm=3, base_command=base_command, num_cpus=64, num_dirs=64, synthetic="uniform_random", num_pods=8)
run_stats(topology="FatTree", routing_algorithm=0, base_command=base_command, num_cpus=64, num_dirs=64, synthetic="uniform_random", num_pods=8)

# topology
run_stats(topology="Mesh_XY", routing_algorithm=1, base_command=base_command, num_cpus=16, num_dirs=16, synthetic="uniform_random", mesh_rows=4)
run_stats(topology="FatTree", routing_algorithm=4, base_command=base_command, num_cpus=16, num_dirs=16, synthetic="uniform_random", num_pods=4)
run_stats(topology="Mesh_XY", routing_algorithm=1, base_command=base_command, num_cpus=32, num_dirs=32, synthetic="uniform_random", mesh_rows=8)
run_stats(topology="FatTree", routing_algorithm=4, base_command=base_command, num_cpus=32, num_dirs=32, synthetic="uniform_random", num_pods=6)
run_stats(topology="Mesh_XY", routing_algorithm=1, base_command=base_command, num_cpus=64, num_dirs=64, synthetic="uniform_random", mesh_rows=8)
run_stats(topology="FatTree", routing_algorithm=4, base_command=base_command, num_cpus=64, num_dirs=64, synthetic="uniform_random", num_pods=8)

##############################################################################################
# Gather Plots
##############################################################################################

STATS_MAP = {
    "average_packet_latency": "latency_list", 
    "average_hops": "average_hops_list", 
    "reception_rate": "reception_rate_list",
}


marker_idx = 0
def run_plots(topology, routing_algorithm, num_pods, mesh_rows, num_cpus, stats_name, label, min_injRate_idx = 0, max_injRate_idx = 15, marker_idx = 0, markers=['o', 's', '^', '*', 'x', '+']):
    title_name_prefix = get_title_name(topology, routing_algorithm, num_pods, mesh_rows, num_cpus)
    stats = pickle.load(open(join(SAVE_DIR, f"{title_name_prefix}_LT_stats.pkl"), "rb"))[STATS_MAP[stats_name]]
    injRate_list = [0.01] + np.arange(0.05, 0.71, 0.05).tolist()
    injRate_list = injRate_list[min_injRate_idx : max_injRate_idx]
    stats = stats[min_injRate_idx : max_injRate_idx]
    plt.plot(injRate_list, stats, marker=markers[marker_idx], label=label, alpha=0.8)

stats_name_list = ["average_packet_latency", "average_hops", "reception_rate"]
for stats_name in stats_name_list:
    # Routing
    plt.clf()
    marker_idx = 0
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=8, mesh_rows=0, num_cpus=64, stats_name=stats_name, label="Adaptive", marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=3, num_pods=8, mesh_rows=0, num_cpus=64, stats_name=stats_name, label="Deterministic", marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=0, num_pods=8, mesh_rows=0, num_cpus=64, stats_name=stats_name, label="Table", marker_idx=marker_idx)
    marker_idx += 1
    plt.legend()
    plt.title(f"Latency-{stats_name}")
    plt.xlabel("Injection Rate")
    plt.ylabel(stats_name)
    plt.grid(True) 
    plt.savefig(join(SAVE_DIR, f"Routing_{stats_name}_curve.jpg"))

    # Topology
    # low range
    plt.clf()
    marker_idx = 0
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=8, mesh_rows=0, num_cpus=64, stats_name=stats_name, label="FatTree k=8", min_injRate_idx = 0, max_injRate_idx = 10, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=6, mesh_rows=0, num_cpus=32, stats_name=stats_name, label="FatTree k=6", min_injRate_idx = 0, max_injRate_idx = 10, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=4, mesh_rows=0, num_cpus=16, stats_name=stats_name, label="FatTree k=4", min_injRate_idx = 0, max_injRate_idx = 10, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=8, num_cpus=64, stats_name=stats_name, label="Mesh 8x8", min_injRate_idx = 0, max_injRate_idx = 10, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=8, num_cpus=32, stats_name=stats_name, label="Mesh 8x4", min_injRate_idx = 0, max_injRate_idx = 10, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=4, num_cpus=16, stats_name=stats_name, label="Mesh 4x4", min_injRate_idx = 0, max_injRate_idx = 10, marker_idx=marker_idx)
    marker_idx += 1
    plt.legend()
    plt.title(f"Latency-{stats_name} (low injRate)")
    plt.xlabel("Injection Rate")
    plt.ylabel(stats_name)
    plt.grid(True) 
    plt.savefig(join(SAVE_DIR, f"Topology_{stats_name}_low_curve.jpg"))

    # high range
    plt.clf()
    marker_idx = 0
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=8, mesh_rows=0, num_cpus=64, stats_name=stats_name, label="FatTree k=8", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=6, mesh_rows=0, num_cpus=32, stats_name=stats_name, label="FatTree k=6", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=4, mesh_rows=0, num_cpus=16, stats_name=stats_name, label="FatTree k=4", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=8, num_cpus=32, stats_name=stats_name, label="Mesh 8x4", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=4, num_cpus=16, stats_name=stats_name, label="Mesh 4x4", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=8, num_cpus=64, stats_name=stats_name, label="Mesh 8x8", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    plt.legend()
    plt.title(f"Latency-{stats_name} (high injRate)")
    plt.xlabel("Injection Rate")
    plt.ylabel(stats_name)
    plt.grid(True) 
    plt.savefig(join(SAVE_DIR, f"Topology_{stats_name}_high_curve.jpg"))

    # high range without mesh 8x8
    plt.clf()
    marker_idx = 0
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=8, mesh_rows=0, num_cpus=64, stats_name=stats_name, label="FatTree k=8", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=6, mesh_rows=0, num_cpus=32, stats_name=stats_name, label="FatTree k=6", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="FatTree", routing_algorithm=4, num_pods=4, mesh_rows=0, num_cpus=16, stats_name=stats_name, label="FatTree k=4", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=8, num_cpus=32, stats_name=stats_name, label="Mesh 8x4", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    run_plots(topology="Mesh_XY", routing_algorithm=1, num_pods=0, mesh_rows=4, num_cpus=16, stats_name=stats_name, label="Mesh 4x4", min_injRate_idx = 10, max_injRate_idx = 15, marker_idx=marker_idx)
    marker_idx += 1
    plt.legend()
    plt.title(f"Latency-{stats_name} (high injRate)")
    plt.xlabel("Injection Rate")
    plt.ylabel(stats_name)
    plt.grid(True) 
    plt.savefig(join(SAVE_DIR, f"Topology_{stats_name}_high_woMesh8x8_curve.jpg"))