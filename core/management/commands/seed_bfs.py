from django.core.management.base import BaseCommand
from accounts.models import User
from groups.models import Group

class Command(BaseCommand):
    help = 'Seeds the Initial Test Environment (Section 6 of Brief)'

    def handle(self, *args, **kwargs):
        # The password everyone will use to login
        TEST_PASSWORD = 'bfs_test2026'

        # 1. Create Groups
        group_names = ['Research Group A', 'Research Group B', 'Research Group C', 'Research Group D', 'Research Group E']
        for name in group_names:
            Group.objects.get_or_create(name=name)
        
        # 2. Create Mentees (5)
        for i in range(1, 6):
            user, created = User.objects.get_or_create(username=f'mentee_{i}', role='mentee', email=f'mentee{i}@example.com')
            user.set_password(TEST_PASSWORD)
            user.save()
        
        # 3. Create Mentors (5)
        for i in range(1, 6):
            user, created = User.objects.get_or_create(username=f'mentor_{i}', role='mentor', email=f'mentor{i}@example.com')
            user.set_password(TEST_PASSWORD)
            user.save()

        # 4. Create Management (2)
        for i in range(1, 3):
            user, created = User.objects.get_or_create(username=f'mgmt_{i}', role='management')
            user.set_password(TEST_PASSWORD)
            user.save()

        # 5. Create Coordinator (1)
        user, created = User.objects.get_or_create(username='coordinator_bfs', role='coordinator')
        user.set_password(TEST_PASSWORD)
        user.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded 13 users with password: {TEST_PASSWORD}'))