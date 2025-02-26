### Optimized B-Trees for Scalable Data Storage in ML Systems
As part of my work on efficient data structures, I implemented a B-Tree data structure optimized for disk-based storage, a fundamental technique for scalable data handling in machine learning pipelines, databases, and search systems.

# Key Highlights:
- Optimized Data Retrieval for ML Pipelines: Designed a disk-based B-Tree where nodes reside in separate disk blocks, optimizing storage access for large-scale datasets.
- Efficient Key-Value Lookups: Implemented find() and insert() operations, ensuring O(log n) retrieval time, which is crucial for indexing features and training data efficiently.
- Memory-Disk Tradeoff Optimization: Tuned branching factor (m) and leaf size (l) to balance memory and disk access efficiency, simulating real-world ML data storage challenges.
- Binary Search for Log-Time Queries: Enabled fast feature retrieval and indexing, a core optimization in large-scale ML workflows.
- Robust Testing & Debugging: Developed comprehensive test cases using pytest to validate B-Tree operations under various configurations and data distributions.

This project deepened my understanding of I/O-efficient algorithms, hierarchical indexing, and real-world data structure optimization—essential skills for designing high-performance data pipelines and scalable machine learning models.
