import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text

from sql_agent.orchestrator import SyncAgent


class TestSqlAgent(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for testing
        self.db_connection_url = "sqlite:///:memory:"
        self.engine = create_engine(self.db_connection_url)
        self.db_table_names = ('orders', 'products', 'customers')

        # Create tables and insert test data
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE customers (
                    id INT PRIMARY KEY,
                    name VARCHAR(255)
                );
            """))
            conn.execute(text("""
                CREATE TABLE products (
                    id INT PRIMARY KEY,
                    name VARCHAR(255),
                    price DECIMAL(10, 2)
                );
            """))
            conn.execute(text("""
                CREATE TABLE orders (
                    id INT PRIMARY KEY,
                    customer_id INT,
                    product_id INT,
                    quantity INT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
            """))
            conn.execute(text("INSERT INTO customers (id, name) VALUES (1, 'Alice'), (2, 'Bob');"))
            conn.execute(
                text("INSERT INTO products (id, name, price) VALUES (1, 'Laptop', 1200.00), (2, 'Mouse', 25.00);"))
            conn.execute(text(
                "INSERT INTO orders (id, customer_id, product_id, quantity) VALUES (1, 1, 1, 1), (2, 1, 2, 2), (3, 2, 1, 1);"))
            conn.commit()

    def tearDown(self):
        # Remove the test database file
        if os.path.exists("test.db"):
            os.remove("test.db")

    @patch('sql_agent.graph.sql_generator')
    def test_ask_question_success(self, mock_sql_generator):
        # Mock the SQL generator to return a predictable query
        mock_sql_generator.invoke.return_value = "SELECT * FROM orders"

        # Create a SQLite repository from the existing engine to share the in-memory database
        from sql_agent.repositories.sqlite_repository import SQLiteRepository
        repository = SQLiteRepository(engine=self.engine)

        # Initialize the agent
        agent = SyncAgent(
            repository=repository,
            db_table_names=self.db_table_names
        )

        # Ask a question
        question = "Show me all orders"
        result = agent.ask(question)

        # Assertions
        self.assertEqual(result['sql_query'], "SELECT * FROM orders")
        self.assertIsNotNone(result['result'])
        self.assertEqual(len(result['result'].rows), 3)
        self.assertEqual(result['result'].columns, ['id', 'customer_id', 'product_id', 'quantity'])

    @patch('sql_agent.graph.sql_generator')
    @patch('sql_agent.graph.sql_corrector')
    def test_ask_question_with_validation_failure(self, mock_sql_corrector, mock_sql_generator):
        # Mock the generator to return an invalid query that will fail validation
        mock_sql_generator.invoke.return_value = "DROP TABLE orders"
        # Mock the corrector to also return an invalid query, so validation keeps failing
        mock_sql_corrector.invoke.return_value = "DELETE FROM customers"

        # Create a SQLite repository from the existing engine to share the in-memory database
        from sql_agent.repositories.sqlite_repository import SQLiteRepository
        repository = SQLiteRepository(engine=self.engine)

        # Initialize the agent with a low max_generations to trigger failure quickly
        agent = SyncAgent(
            repository=repository,
            db_table_names=self.db_table_names,
            max_generations=2  # Limit to 2 generations
        )

        # Ask a question - generation will create invalid SQL, correction will also fail
        question = "Show me all orders"
        try:
            result = agent.ask(question)
            # If we get here without an exception, the test failed to trigger expected behavior
            self.fail("Expected AgentFailure was not raised")
        except Exception as e:
            # The agent should fail after max generations of invalid SQL
            self.assertIn("could not answer the question", str(e).lower())

    @patch('sql_agent.graph.sql_generator')
    @patch('sql_agent.graph.sql_corrector')
    def test_ask_question_with_execution_failure(self, mock_sql_corrector, mock_sql_generator):
        # Mock the generator to return a query that will cause execution error
        mock_sql_generator.invoke.return_value = "SELECT * FROM non_existent_table"
        # Mock the corrector to also return a query that will cause execution error
        mock_sql_corrector.invoke.return_value = "SELECT name FROM another_non_existent_table"

        # Create a SQLite repository from the existing engine to share the in-memory database
        from sql_agent.repositories.sqlite_repository import SQLiteRepository
        repository = SQLiteRepository(engine=self.engine)

        # Initialize the agent with a low max_generations to trigger failure quickly
        agent = SyncAgent(
            repository=repository,
            db_table_names=self.db_table_names,
            max_generations=2  # Limit to 2 generations
        )

        # Ask a question - generation will create SQL that causes execution error, correction will also fail
        question = "Show me all orders"
        try:
            result = agent.ask(question)
            # If we get here without an exception, the test failed to trigger expected behavior
            self.fail("Expected AgentFailure was not raised")
        except Exception as e:
            # The agent should fail after max generations of queries causing execution errors
            self.assertIn("could not answer the question", str(e).lower())

    @patch('sql_agent.graph.sql_generator')
    @patch('sql_agent.graph.sql_corrector')
    def test_ask_question_empty_query(self, mock_sql_corrector, mock_sql_generator):
        # Mock the generator to return an empty query that will fail validation
        mock_sql_generator.invoke.return_value = ""
        # Mock the corrector to also return an empty query, so validation keeps failing
        mock_sql_corrector.invoke.return_value = ""

        # Create a SQLite repository from the existing engine to share the in-memory database
        from sql_agent.repositories.sqlite_repository import SQLiteRepository
        repository = SQLiteRepository(engine=self.engine)

        # Initialize the agent with a low max_generations to trigger failure quickly
        agent = SyncAgent(
            repository=repository,
            db_table_names=self.db_table_names,
            max_generations=2  # Limit to 2 generations
        )

        # Ask a question - generation will create empty SQL, correction will also fail
        question = "Show me all orders"
        try:
            result = agent.ask(question)
            # If we get here without an exception, the test failed to trigger expected behavior
            self.fail("Expected AgentFailure was not raised")
        except Exception as e:
            # The agent should fail after max generations of empty SQL
            self.assertIn("could not answer the question", str(e).lower())

    @patch('sql_agent.graph.sql_generator')
    @patch('sql_agent.graph.sql_corrector')
    def test_model_regeneration_after_validation_failure(self, mock_sql_corrector, mock_sql_generator):
        # Track how many times each mock is called
        call_count = {'generator': 0, 'corrector': 0}
        
        def generator_side_effect(*args, **kwargs):
            call_count['generator'] += 1
            if call_count['generator'] == 1:
                return "DROP TABLE orders"  # Invalid on first try
            else:
                return "SELECT * FROM orders"  # Valid on subsequent tries
                
        def corrector_side_effect(*args, **kwargs):
            call_count['corrector'] += 1
            return "SELECT * FROM orders"  # Valid corrected query
            
        mock_sql_generator.invoke.side_effect = generator_side_effect
        mock_sql_corrector.invoke.side_effect = corrector_side_effect

        # Create a SQLite repository from the existing engine to share the in-memory database
        from sql_agent.repositories.sqlite_repository import SQLiteRepository
        repository = SQLiteRepository(engine=self.engine)

        # Initialize the agent
        agent = SyncAgent(
            repository=repository,
            db_table_names=self.db_table_names
        )

        # Ask a question
        question = "Show me all orders"
        result = agent.ask(question)

        # Assertions - the first generation should have failed validation, triggering correction
        # The corrected query should have been successful
        self.assertEqual(result['sql_query'], "SELECT * FROM orders")
        self.assertIsNotNone(result['result'])  # Should have a result from the corrected query
        self.assertEqual(len(result['result'].rows), 3)
        self.assertEqual(result['result'].columns, ['id', 'customer_id', 'product_id', 'quantity'])
        # Should have been called generator once, corrector once
        self.assertEqual(call_count['generator'], 1)  # Generator called once
        self.assertEqual(call_count['corrector'], 1)  # Corrector should be called once after validation failure

    @patch('sql_agent.graph.sql_generator')
    @patch('sql_agent.graph.sql_corrector')
    def test_ask_question_incorrect_sql_structure(self, mock_sql_corrector, mock_sql_generator):
        # Mock the generator to return a query without SELECT and FROM, which will fail validation
        mock_sql_generator.invoke.return_value = "UPDATE customers SET name = 'Test'"
        # Mock the corrector to also return a query without SELECT and FROM, so validation keeps failing
        mock_sql_corrector.invoke.return_value = "DELETE FROM orders"

        # Create a SQLite repository from the existing engine to share the in-memory database
        from sql_agent.repositories.sqlite_repository import SQLiteRepository
        repository = SQLiteRepository(engine=self.engine)

        # Initialize the agent with a low max_generations to trigger failure quickly
        agent = SyncAgent(
            repository=repository,
            db_table_names=self.db_table_names,
            max_generations=2  # Limit to 2 generations
        )

        # Ask a question - generation will create SQL with incorrect structure, correction will also fail
        question = "Show me all orders"
        try:
            result = agent.ask(question)
            # If we get here without an exception, the test failed to trigger expected behavior
            self.fail("Expected AgentFailure was not raised")
        except Exception as e:
            # The agent should fail after max generations of SQL with incorrect structure
            self.assertIn("could not answer the question", str(e).lower())
