import asyncio
import threading
from queue import Queue
from collections import deque
import pygame
from worldgen import generate_chunk
import config as c

class AsyncChunkManager:
    def __init__(self, chunk_width, view_distance):
        self.chunk_width = chunk_width
        self.view_distance = view_distance
        self.chunk_cache = {}
        self.generation_queue = Queue()
        self.ready_chunks = Queue()
        self.worker_thread = None
        self.running = True
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._chunk_worker, daemon=True)
        self.worker_thread.start()

    def _chunk_worker(self):
        """Background thread for generating chunks"""
        while self.running:
            try:
                if not self.generation_queue.empty():
                    chunk_index, seed = self.generation_queue.get_nowait()
                    if chunk_index not in self.chunk_cache:
                        chunk = generate_chunk(chunk_index, self.chunk_width, c.WORLD_HEIGHT, seed)
                        self.ready_chunks.put((chunk_index, chunk))
                        self.chunk_cache[chunk_index] = True
            except Exception as e:
                print(f"Chunk generation error: {e}")
            pygame.time.wait(1)  # Prevent thread from hogging CPU

    def request_chunks(self, center_chunk, seed):
        """Queue chunks for generation based on view distance"""
        for ci in range(center_chunk - self.view_distance, center_chunk + self.view_distance + 1):
            if ci not in self.chunk_cache:
                self.generation_queue.put((ci, seed))

    def get_ready_chunks(self):
        """Get any completed chunks"""
        ready = {}
        while not self.ready_chunks.empty():
            try:
                chunk_index, chunk = self.ready_chunks.get_nowait()
                ready[chunk_index] = chunk
            except:
                break
        return ready

    def cleanup(self):
        """Stop the worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
