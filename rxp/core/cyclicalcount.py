import math
import random

"""
creates an integer that cycles back to its minimum
when it reaches its maximum
"""
class CyclicalCount:
    def __init__(self, min=0, max=0):
        self.min = min
        self.num = max
        self.current = min

    def set(self, value=None):
        if not value:
            # pick a new random sequence number
            min = random.randint(0, math.pow(2, 32))  # TODO 2**32 max seq?
        else:
            self.current = value

    def increment(self):
        self.current += 1
        if self.current > self.num:
            self.current = self.min
        return self.current

    def __str__(self):
        # returns current number
        return str(self.current)
