### Instructions:
Your task is to convert a question into a SQL query, given a Postgres database schema.
Adhere to these rules:
- **Deliberately go through the question and database schema word by word** to appropriately answer the question
- **Use Table Aliases** to prevent ambiguity. For example, <sql>SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id;</sql>
- When creating a ratio, always cast the numerator as float

### Input:
Generate a SQL query that answers the <question>{question}</question>
This query will run on a database whose schema is represented in this string:
{database_schema}

### Response:
Based on your instructions, here is the SQL query I have generated to answer the <question>{question}</question>:
<sql>{sql_query}</sql>

### Feedback from SQL Execution:
<feedback>{feedback}</feedback>

### Instructions for Correction:
- Carefully review the original SQL query and the feedback provided.
- Identify which parts of the query caused errors or issues according to the feedback.
- Correct the query to fix all the issues mentioned.
- Preserve the intent of the original query and answer the question accurately.

### Corrected SQL Query:
<sql>