import random
import hashlib
import math
import statistics

#####################
# TUG OF WAR Sketch #
#####################

class TugOfWarSketch():
    """
        Sketch to estimate :
            - F2 moments
            - scalar product
            - join size
        we have : h(x) = +1 if hash pair
                         -1 if hash impair
    """
    def __init__(self, seeds = 0, num_repetitions=101):
        self.num_repetitions = num_repetitions
        self.seeds = [random.randint(0, 10**9) for _ in range(num_repetitions)]
        self.values = [0] * num_repetitions

    def _hash_sign (self, x, seeds):
        """
            returns ±1 depending on  hash parity
        """
        h = hashlib.md5((str(x) + str(seeds)).encode()).hexdigest()
        if int(h, 16) %2 == 0:
            result = 1
        else:
            result = -1
        return result
    
    def update(self, x, count=1):
        """
            Updates sketch with a new value
        """
        for i in range(self.num_repetitions):
            sign = self._hash_sign(x, self.seeds[i])
            self.values[i] += sign * count

    def estimate_f2(self):
        """
            Estimates second frequency moment:
                F2 = sum(f(i)**2)
        """
        estimates = [v*v for v in self.values]
        return statistics.median(estimates)
    
    def scalar_product(self, other):
        """
            estimates scalar product:
                sum(f(x)g(x))
        """
        estimates = []
        for a,b in zip(self.values, other.values):
            estimates.append(a*b)

        return statistics.median(estimates)

    
####################
# COUNT-MIN sketch #
####################
class CountMinSketch:
    """
        Count-Min Sketch to estimate frequencies.
        Error: + epsilon*m
        failure propability : delta
    """
    def __init__(self, epsilon=0.01, delta=0.01):
        self.epsilon = epsilon
        self.delta = delta
        self.s = math.ceil(math.e / epsilon)  #columns
        self.t = math.ceil(math.log2(1/delta))
        self.table = [[0] * self.s for _ in range(self.t)]
        self.seeds = [random.randint(0, 10**9) for _ in range(self.t)]

    def _hash(self, x, seeds):
        h = hashlib.md5((str(x) + str(seeds)).encode()).hexdigest()
        return int(h, 16) % self.s
    
    def update(self, x):
        """
            Insert an element in the sketch
        """
        for i in range (self.t):
            col = self._hash(x, self.seeds[i])
            self.table[i][col] += 1
    
    def estimate(self, x):
        """
            returns min_j CM[j][h_j(x)]
        """
        estimates = []
        for i in range(self.t):
            col = self._hash(x, self.seeds[i])
            estimates.append(self.table[i][col])
        return min(estimates)

#############
# FM Sketch #
#############
class FMSketch:
    def __init__(self):
        self.max_zeros = 0

    def _hash(self, x):
        h = hashlib.md5(str(x).encode()).hexdigest()
        return int(h, 16)

    def _trailing_zeros(self, n):
        if n == 0:
            return 32
        count  = 0
        while n & 1 == 0:
            count +=1
            n >>= 1

        return count 
    
    def update(self, x):
        h = self._hash(x)
        zeros = self._trailing_zeros(h)
        self.max_zeros = max(self.max_zeros, zeros)

    def estimate(self):
        return 2**self.max_zeros
    
##############################################
# TableSketch -> one Sketch per column FAERS #
##############################################

class TableSketch:
    """
        Contains a sketch per column. Exemple : 
            - age
            - sex
            - drug
            - reaction
            - serious    
    """

    def __init__(self):
        self.row_count = 0
        self.col_sums = {}
        self.frequency_sketches = {}
        self.join_sketches = {}
        self.observed_values = {}
        self.distinct_sketches = {}

    def add_column(self, colname):
        """
            Init a sketch by column
        """
        if colname not in self.frequency_sketches:
            self.frequency_sketches[colname] = CountMinSketch()
            self.join_sketches[colname] = TugOfWarSketch()
            self.col_sums[colname] = 0
            self.observed_values[colname] = set()
            self.distinct_sketches[colname] = FMSketch()
    
    def update_row(self, row):
        """
            updates corresponding sktech to column
        """

        self.row_count += 1

        for colname, value in row.items():
            if colname not in self.frequency_sketches:
                self.add_column(colname)
            
            self.frequency_sketches[colname].update(value)

            self.join_sketches[colname].update(value)

            self.observed_values[colname].add(value)

            self.distinct_sketches[colname].update(value)

            if isinstance(value, (int, float)):
                self.col_sums[colname] += value

    def estimate_frequency(self, colname, value):
        return self.frequency_sketches[colname].estimate(value)

    def count(self):
        return self.row_count
    
    def sum(self, colname):
        return self.col_sums[colname]
    
    def avg(self, colname):
        if self.row_count == 0:
            return 0
        return self.sum(colname) / self.count()
    
    def get_join_sketch(self, colname):
        return self.join_sketches[colname]
    
    def group_by_count(self, colname):
        result = {}
        for value in self.observed_values[colname]:
            result[value] = self.estimate_frequency(colname, value)
        return result
    
    def top_k(self, colname, k=10):
        candidates = []

        for value in self.observed_values[colname]:
            freq = self.estimate_frequency(colname=colname, value=value)

            candidates.append((value, freq))
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[:k]
    
    def distinct_count(self, colname):
        return self.distinct_sketches[colname].estimate()