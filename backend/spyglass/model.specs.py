# Get CPU available memory
import psutil

# Get system memory info
memory = psutil.virtual_memory()
total_memory_gb = round(memory.total / (2**30))
available_memory_gb = round(memory.available / (2**30))

print(f"Total system memory: {total_memory_gb} GB")
print(f"Available system memory: {available_memory_gb} GB")
print(f"Memory usage: {memory.percent}%")
