class ExactTable:
    def __init__(self):
        self.rows = 0
        self.frequencies = {}
        self.sums = {}
        self.distinct_values = {}

    def update_row(self, row):
        self.rows += 1

        for col, value in row.items():

            if col not in self.frequencies:
                self.frequencies[col] = {}

            if value not in self.frequencies[col]:
                self.frequencies[col][value] = 0

            self.frequencies[col][value] +=1

            if isinstance(value, (int, float)):
                if col not in self.sums:
                    self.sums[col] = 0
                self.sums[col] += value

            if col not in self.distinct_values:
                self.distinct_values[col] = set()
            self.distinct_values[col].add(value)
    
    def count(self):
        return self.rows
    
    def frequency(self, col, value):
        return self.frequencies.get(col, {}).get(value, 0)
    
    def avg(self, col):
        return self.sums[col] / self.count()
    
    def distinct_count(self, colname):
        return len(self.distinct_values.get(colname, set())) 