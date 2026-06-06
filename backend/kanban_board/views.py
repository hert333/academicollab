# backend/kanban_board/views.py

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Board, Column, Task
from .serializers import BoardSerializer, ColumnSerializer, TaskSerializer

class BoardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Board schemas to be viewed or edited.
    Enforces strict Zero-Trust backend validation via IsAuthenticated permissions.
    """
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]


class ColumnViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Column workflow lanes to be viewed or edited.
    """
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    permission_classes = [IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Task tracking cards to be viewed or edited.
    Contains isolated atomic transaction logic to handle race conditions during drag events.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['patch'], url_path='move')
    def move_task(self, request, pk=None):
        """
        Atomically shifts a target card across lane boundaries or index locations.
        Enforces strict index ordering matrices within the targeted swimlane.
        """
        task = self.get_object()
        target_column_id = request.data.get('target_column_id')
        new_position = request.data.get('position')

        if target_column_id is None or new_position is None:
            return Response(
                {"error": "MALFORMED_PAYLOAD: Missing target_column_id or position vectors."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_position = int(new_position)
            with transaction.atomic():
                # Enforce pessimistic lock across records within the target column to prevent dirty index calculations
                target_column = Column.objects.select_for_update().get(id=target_column_id)
                
                # Fetch sibling objects excluding the current task entity
                siblings = Task.objects.filter(column=target_column).exclude(id=task.id).order_by('position')
                
                # Array manipulation block to reconstruct clean increment sequences
                updated_siblings = list(siblings)
                # Bound insert request inside the actual logical dimensions of the active array
                target_idx = max(0, min(new_position, len(updated_siblings)))
                updated_siblings.insert(target_idx, task)

                # Batch persist recalculated sequence values directly to database rows
                for index, item in enumerate(updated_siblings):
                    item.position = index
                    item.column = target_column
                    item.save(update_fields=['position', 'column'])

            return Response({"status": "SUCCESS", "message": "State layout synchronized."}, status=status.HTTP_200_OK)

        except Column.DoesNotExist:
            return Response({"error": "NOT_FOUND: Target column matrix does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"INTERNAL_ERROR: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'], url_path='update-timeline')
    def update_timeline(self, request, pk=None):
        """
        Updates task chronological boundary constraints with server-side safety checks.
        Enforces strict validation requirements (due_date >= start_date).
        """
        task = self.get_object()
        start_date = request.data.get('start_date')
        due_date = request.data.get('due_date')

        if not start_date or not due_date:
            return Response(
                {"error": "MALFORMED_PAYLOAD: Missing start_date or due_date tracking attributes."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Enforce pessimistic row lock on targeted record to ensure transaction isolation
                locked_task = Task.objects.select_for_update().get(id=task.id)
                locked_task.start_date = start_date
                locked_task.due_date = due_date
                
                # Logical enforcement step to maintain data sanity 
                if str(locked_task.due_date) < str(locked_task.start_date):
                    return Response(
                        {"error": "INVALID_CHRONOLOGY: due_date cannot occur prior to start_date."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                locked_task.save(update_fields=['start_date', 'due_date'])

            return Response({"status": "SUCCESS", "message": "Task timeline synchronized."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"INTERNAL_ERROR: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)