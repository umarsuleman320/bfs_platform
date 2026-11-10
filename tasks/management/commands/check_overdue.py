from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import TaskAssignment
from django.db.models import Q

class Command(BaseCommand):
    help = 'Automatically identifies assignments past deadline and updates status to Overdue.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        
        # We only care about assignments that are still 'todo' or 'submitted'
        # but their parent Task deadline has passed.
        overdue_assignments = TaskAssignment.objects.filter(
            Q(status='todo') | Q(status='submitted'),
            task__deadline__lt=now
        )

        count = overdue_assignments.count()
        
        if count > 0:
            # Update all found assignments to 'overdue'
            overdue_assignments.update(status='overdue')
            self.stdout.write(self.style.SUCCESS(f'System Success: {count} assignments moved to OVERDUE status.'))
        else:
            self.stdout.write(self.style.NOTICE('System Scan: No new overdue assignments detected.'))