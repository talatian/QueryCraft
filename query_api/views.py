import os

from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from sql_agent.exceptions import DatabaseError, AgentFailure
from sql_agent.orchestrator import SyncAgent

from .serializers import QueryRequestSerializer, QueryResponseSerializer


def get_db_connection_url():
    """Construct the database connection URL from environment variables."""
    return f"postgresql://{os.environ.get('DB_USER', 'postgres')}:{os.environ.get('DB_PASSWORD', 'postgres')}@{os.environ.get('DB_HOST', 'db')}:{os.environ.get('DB_PORT', '5432')}/{os.environ.get('DB_NAME', 'querycraft_db')}"


class QueryAPIView(APIView):
    """
    API endpoint using Django REST Framework Class Based Views to handle natural language queries.
    Receives a JSON with the user's question and returns the result.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate the request data using the serializer
        serializer = QueryRequestSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                QueryResponseSerializer({'error': str(e)}).data, status=status.HTTP_400_BAD_REQUEST
            )

        question = serializer.validated_data['question']

        # Create a SQL agent with DB connection and table information
        sql_agent = SyncAgent(
            db_connection_url=get_db_connection_url(),
            db_table_names=('orders', 'products', 'customers')
        )

        try:
            answer = sql_agent.ask(question=question)
        except (DatabaseError, AgentFailure) as e:
            # Handle known agent/database errors
            return Response(
                QueryResponseSerializer(
                    {'question': question, 'error': str(e)}
                ).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            # Handle unexpected errors
            return Response(
                QueryResponseSerializer(
                    {'question': question, 'error': "An unexpected error occurred. Please contact support."}
                ).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Format and return the successful response
        response_serializer = QueryResponseSerializer({
            'question': question,
            'sql_query': answer["sql_query"],
            'result': answer["result"],
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)
