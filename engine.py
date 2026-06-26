import re

#########################
# DB of sketched tables #
#########################

class SketchDB:
    """
        exemple :
            - db.tables["patients"]
            - db.tables["drugs"]
    """
    def __init__(self):
        self.tables = {}

    def add_table(self, table_name, table_sketch):
        self.tables[table_name.lower()] = table_sketch

    def get_table(self, table_name):
        table_name = table_name.lower()

        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' not found 😱 *heart attack*")
        
        return self.tables[table_name]
    

###################################
# Mini Approximate SQL DB #
###################################

class MiniSqlEngine:
    """
        Mini SQL based on sketches.
        It supports : 
            - COUNT(*)
            - AVG(columns)
            - COUNT(*) WHERE ...
            - estimation of join size
    """

    def __init__(self, database):
        self.database = database

    #---------------------------------------------#
    # Principal functions -> execute SQL requests #
    #---------------------------------------------#

    def execute(self, query):
        query = query.strip()
        query_upper = query.upper()

        # COUNT
        if query_upper.startswith("SELECT COUNT(*)"):
            # hard one - with WHERE 😵‍💫
            if re.search(r"\w+\.\w+\s*=\s*\w+\.\w+", query):
                return self._handle_join(query)

            # normal one
            return self._handle_count(query)
        
        # AVG
        if query_upper.startswith("SELECT AVG"):
            return self._handle_avg(query)
        
        # GROUP BY
        if "GROUP BY" in query_upper:
            return self._handle_groupby(query)
        
        # TOP-K
        if query_upper.startswith("SELECT TOP"):
            return self._handle_topk(query)
        
        # COUNT DISTINCT
        if "COUNT(DISTINCT" in query_upper:
            return self._handle_distinct(query)
        
        raise NotImplementedError("/!\ SQL REQUEST not supproted !")
    
    #########
    # COUNT #
    #########

    def _handle_count(self, query):
        """
            Handles : 
                (1) SELECT COUNT(*) FROM ...
                (2) SELECT COUNT(*) FROM ... WHERE column = ... 
        """

        table_match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)

        if not table_match:
            raise ValueError("/!\ missing FROM clause")
        
        table_name = table_match.group(1).lower()
        table = self.database.get_table(table_name)

        # (1)
        if "WHERE" not in query.upper() :
            return table.count()
        
        # (2)
        where_match = re.search(r"WHERE\s+(\w+)\s*=\s*'?(.*?)'?$", query, re.IGNORECASE)
        
        if not where_match:
            raise ValueError("/!\ WHERE syntax is not correct !")
        
        col = where_match.group(1).lower()
        value = where_match.group(2)

        return table.estimate_frequency(col, value)
    

    #######
    # AVG #
    #######

    def _handle_avg(self, query):
        """
            handles : 
                - SELECT AVG(column) FROM ...
        """
        # we extract the column
        avg_match = re.search(r"AVG\((\w+)\)", query, re.IGNORECASE)
        if not avg_match:
            raise ValueError("/!\ AVG syntax error !")
        
        col = avg_match.group(1).lower()

        # then the table
        table_match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)

        if not table_match:
            raise ValueError("/!\ Query syntaxe error !")
        
        table_name = table_match.group(1).lower()
        table = self.database.get_table(table_name)
        
        return table.avg(col)
    
    ########
    # JOIN #
    ########

    def _handle_join(self, query):
        """
            handles : 
                - SELECT COUNT(*) FROM A, B WHERE A.x = B.x
        """

        # we extract the tables
        tables_matche = re.search(r"FROM\s+(\w+)\s*,\s*(\w+)", query, re.IGNORECASE)
        if not tables_matche:
            raise ValueError("/!\ Query syntax error")
        
        table1_name = tables_matche.group(1).lower()
        table2_name = tables_matche.group(2).lower()

        table1 = self.database.get_table(table1_name)
        table2 = self.database.get_table(table2_name)
        
        # then we extract the join columns
        join_match = re.search(r"WHERE\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)", query, re.IGNORECASE)

        if not join_match:
            raise ValueError("/!\ Query syntaxe error !")
        
        col1 = join_match.group(2).lower()
        col2 = join_match.group(4).lower()
        
        # finally we apply the ToW scalar product
        sketch1 = table1.get_join_sketch(col1)
        sketch2 = table2.get_join_sketch(col2)

        
        return sketch1.scalar_product(sketch2)
    
    ############
    # GROUP BY #
    ############
    def _handle_groupby(self, query):
        match = re.search(r"SELECT\s+(\w+)\s*,\s*COUNT\(\*\)\s+FROM\s+(\w+)\s+GROUP BY\s+(\w+)", query, re.IGNORECASE)

        if not match:
            raise ValueError("/!\ GROUP BY syntax error")

        col = match.group(1).lower()
        table_name = match.group(2).lower()

        table = self.database.get_table(table_name)

        return table.group_by_count(col)    

    
    #########
    # TOP-K #
    #########
    def _handle_topk(self, query):

        match = re.search(r"SELECT TOP\s+(\d+)\s+(\w+)\s+FROM\s+(\w+)", query, re.IGNORECASE)

        if not match:
            raise ValueError("/!\TOP-K syntax error")

        k = int(match.group(1))
        col = match.group(2).lower()

        table_name = match.group(3).lower()
        table = self.database.get_table(table_name)

        return table.top_k(col, k) 
    
    ##################
    # Count DISTINCT #
    ##################
    def _handle_distinct(self, query):

        match = re.search(r"COUNT\(DISTINCT\s+(\w+)\)\s+FROM\s+(\w+)", query, re.IGNORECASE)

        if not match:
            raise ValueError("/!\ DISTINCT syntax error")

        col = match.group(1).lower()
        table_name = match.group(2).lower()

        table = self.database.get_table(table_name)

        return table.distinct_count(col)