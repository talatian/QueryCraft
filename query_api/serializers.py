from rest_framework import serializers


class ResultSerializer(serializers.Serializer):
    columns = serializers.ListField(child=serializers.CharField())
    rows = serializers.ListField(child=serializers.ListField(child=serializers.CharField()))
    total_rows = serializers.IntegerField()


class QueryResponseSerializer(serializers.Serializer):
    question = serializers.CharField(allow_null=True)
    sql_query = serializers.CharField(allow_null=True)
    result = ResultSerializer(allow_null=True)
    error = serializers.CharField(allow_null=True)

class QueryRequestSerializer(serializers.Serializer):
    question = serializers.CharField(required=True, help_text="The natural language question to be converted to SQL")
    
    def validate_question(self, value):
        if not value.strip():
            raise serializers.ValidationError("Question cannot be empty or whitespace only")
        return value.strip()