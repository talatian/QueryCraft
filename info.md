# Project Assumptions

The following assumptions were made during the design and implementation of the solution:

1. **Agent Execution**
   - The agent is assumed to be invoked **synchronously**.
   - However, the implementation follows **LangChain’s Runnable** to enable asynchronous execution with minimal changes if needed.

2. **SQL Query Validation**
   - Accurate SQL validation and guaranteed successful execution **cannot be ensured before running the query** on the database.
   - Therefore, **validation is performed twice**:
     - **Before execution**, to detect basic syntax or structural issues.
     - **During execution**, to handle runtime or logical errors.

3. **Validation Feedback**
   - Validation feedback is stored in the **agent’s internal state**.
   - This feedback is used to **refine and regenerate** invalid or non-executable SQL queries.
   - The agent attempts multiple correction cycles based on the feedback.

4. **Database Independence**
   - The agent is designed to be **independent** and **compatible with any SQL database**.
   - The agent only requires a **database connection URL** and a **list of target table names** to operate.
   - **Query-level access control is not reliably enforceable**, so **authentication and authorization** are assumed to be managed externally by **Django** and the **target database**.

5. **Language Limitation**
   - The system currently has limited support for **Persian queries**, and no specific enhancements have been made to address this.  
   - It is therefore assumed that the system will primarily be used with **English queries**.
