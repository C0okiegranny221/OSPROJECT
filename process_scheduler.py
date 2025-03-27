import gymnasium as gym
from gymnasium import spaces
import numpy as np
import psutil
import pandas as pd

class ProcessSchedulingEnv(gym.Env):
    def __init__(self):
        super(ProcessSchedulingEnv, self).__init__()

        # Define action space (0 = Schedule CPU-bound process, 1 = Schedule I/O-bound process)
        self.action_space = spaces.Discrete(2)

        # Observation space: (User CPU time, System CPU time, Priority, Memory Usage)
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(4,), dtype=np.float32)

        # Load process data
        self.process_data = self.get_process_data()
        self.current_index = 0  # Track which process is being scheduled

        # Initialize state
        self.state = self.process_data.iloc[self.current_index].values.astype(np.float32)
        self.done = False

    def get_process_data(self):
        """Fetch real-time process scheduling data."""
        process_list = []
        for proc in psutil.process_iter(attrs=["pid", "cpu_times", "memory_info", "nice"]):
            try:
                process_list.append({
                    "utime": proc.cpu_times().user if proc.cpu_times() else 0,
                    "stime": proc.cpu_times().system if proc.cpu_times() else 0,
                    "priority": proc.nice(),
                    "mem_usage": proc.memory_info().rss if proc.memory_info() else 0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue  # Skip processes that terminate during iteration
        
        return pd.DataFrame(process_list)

    def step(self, action):
        if self.current_index >= len(self.process_data) - 1:
            self.done = True
            return self.state, 0, self.done, False, {}

        # Get current process metrics
        process = self.process_data.iloc[self.current_index]

        # Compute reward based on action taken
        if action == 0:  # Schedule CPU-intensive process
            reward = -abs(process["utime"] - process["stime"])
        else:  # Schedule I/O-intensive process
            reward = -process["mem_usage"]  # Prefer lower memory usage

        # Move to next process
        self.current_index += 1
        self.state = self.process_data.iloc[self.current_index].values.astype(np.float32)

        return self.state, reward, self.done, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.process_data = self.get_process_data()  # Reload process data
        self.current_index = 0
        self.done = False
        self.state = self.process_data.iloc[self.current_index].values.astype(np.float32)
        return self.state, {}

    def render(self):
        print(f"Current Process - UTime: {self.state[0]}, STime: {self.state[1]}, Priority: {self.state[2]}, Memory Usage: {self.state[3]}")

    def close(self):
        pass
