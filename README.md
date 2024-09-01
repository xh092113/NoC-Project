# Adaptive FatTree

>  The NoC project for course 'AI+X Computing Acceleration: From Algorithms Development, Analysis, to Deployment'
>
> By Xinghan Li & Bowen Yang, IIIS, THU

## 1 Topology

## 2 Implementation

### 2.1 FatTree Topology

### 2.2 The Deterministic Routing Algorithm

### 2.3 The Adaptive Routing Algorithm

## 3 Evaluation

> **To reproduce the results, run command 'python LT_curve_gather.py' under directory 'gem5'.**

### 3.1 Routing Comparations

- We conducted three sets of experiments using different configurations of Mesh and FatTree topologies (Mesh 4$\times$4, Mesh 8$\times$4, Mesh 8$\times$8, FatTree with pod size 4/6/8. The experiments were designed to measure average packet latency at different injection rates to simulate real-world network traffic conditions.

- | ![latency-all](/home/coder66/Desktop/U2-C/AI+X/NoC-Project/pics/latency-all.jpg) | ![latency-highinjrate](/home/coder66/Desktop/U2-C/AI+X/NoC-Project/pics/latency-highinjrate.jpg) | ![latency-lowinjrate](/home/coder66/Desktop/U2-C/AI+X/NoC-Project/pics/latency-lowinjrate.jpg) |
  | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |

- The experimental results clearly demonstrate that FatTree topologies excel in **stability and scalability**, particularly under high traffic conditions. Unlike Mesh configurations, which experienced a significant increase in latency with higher injection rates, FatTree maintained lower and more consistent latency levels. This performance advantage is crucial for environments requiring reliable network performance even during peak traffic periods.

- In conclusion, FatTree's superior handling of dense traffic and its scalability make it a compelling choice for modern network infrastructures. Its consistent performance across varying conditions suggests that it can effectively support the growing demands of data-intensive applications and large-scale network operations.

### 3.2 Topology Comparations



## 4 Division of Labor

