from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from groups.models import Group, Pairing, Meeting
from tasks.models import Task, TaskAssignment, Submission
from progress.models import Goal, Achievement, PointsRule

class BFSSystemIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "BfsPlatform2026!"

        # Create 4 test users for each role
        self.coordinator = User.objects.create_user(
            username='coord_test', email='coord@test.com', password=self.password,
            role='coordinator', is_staff=True, is_superuser=True
        )
        self.mgmt = User.objects.create_user(
            username='mgmt_test', email='mgmt@test.com', password=self.password,
            role='management'
        )
        self.mentor = User.objects.create_user(
            username='mentor_test', email='mentor@test.com', password=self.password,
            role='mentor'
        )
        self.mentee = User.objects.create_user(
            username='mentee_test', email='mentee@test.com', password=self.password,
            role='mentee'
        )

        # Create Group and Pairing
        self.group = Group.objects.create(name="AI Research Group", mentor=self.mentor, coordinator=self.coordinator)
        self.pairing = Pairing.objects.create(mentor=self.mentor, mentee=self.mentee, group=self.group)

    def test_public_and_auth_pages_accessible(self):
        """Verify that all public and entry pages load successfully without 404."""
        # 1. Homepage
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # 2. Direct /login/ (user reported 404 fix verification)
        resp = self.client.get('/login/')
        self.assertEqual(resp.status_code, 200)

        # 3. /accounts/login/
        resp = self.client.get('/accounts/login/')
        self.assertEqual(resp.status_code, 200)

        # 4. Direct /register/ redirects unauthenticated visitors to login
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

        # 5. /accounts/register/ also redirects unauthenticated visitors to login
        resp = self.client.get('/accounts/register/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

        # 6. Wall of fame
        resp = self.client.get('/wall-of-fame/')
        self.assertEqual(resp.status_code, 200)

    def test_registration_restricted_to_management_and_coordinator(self):
        """Only Coordinator and Management can access user registration."""
        # Mentee cannot register users
        self.client.login(username='mentee_test', password=self.password)
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 302)

        # Mentor cannot register users
        self.client.login(username='mentor_test', password=self.password)
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 302)

        # Coordinator CAN register users
        self.client.login(username='coord_test', password=self.password)
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 200)

        # Management CAN register users
        self.client.login(username='mgmt_test', password=self.password)
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 200)

    def test_anonymous_redirects_to_login(self):
        """Unauthenticated requests to protected dashboards must redirect to login."""
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
        # Should redirect to login
        self.assertTrue('/login/' in response.url or '/accounts/login/' in response.url)

    def test_mentee_dashboard_and_workflows(self):
        """Mentee can access mentee dashboard, view tasks, and access personal goals."""
        self.client.login(username='mentee_test', password=self.password)
        
        # 1. Dashboard
        resp = self.client.get(reverse('dashboard:mentee_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # 2. Tasks
        resp = self.client.get(reverse('tasks:my_tasks_list'))
        self.assertEqual(resp.status_code, 200)

        # 3. Goals
        resp = self.client.get(reverse('progress:goals'))
        self.assertEqual(resp.status_code, 200)

        # 4. Leaderboard
        resp = self.client.get(reverse('progress:leaderboard'))
        self.assertEqual(resp.status_code, 200)

        # 5. Helpdesk
        resp = self.client.get(reverse('helpdesk:home'))
        self.assertEqual(resp.status_code, 200)

        # 6. Meeting Request Page
        resp = self.client.get(reverse('groups:request_meeting'))
        self.assertEqual(resp.status_code, 200)

        # 7. Achievement Submission Page
        resp = self.client.get(reverse('progress:submit_achievement'))
        self.assertEqual(resp.status_code, 200)

        # 8. Feedback Page
        resp = self.client.get(reverse('progress:feedback'))
        self.assertEqual(resp.status_code, 200)

        # 9. Profile Page
        resp = self.client.get(reverse('accounts:profile'))
        self.assertEqual(resp.status_code, 200)

        # 10. Notifications Page
        resp = self.client.get(reverse('notifications:list'))
        self.assertEqual(resp.status_code, 200)

    def test_mentor_dashboard_and_workflows(self):
        """Mentor can access mentor dashboard, review queue, meetings, and achievements."""
        self.client.login(username='mentor_test', password=self.password)
        
        # 1. Dashboard
        resp = self.client.get(reverse('dashboard:mentor_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # 2. Review Submissions
        resp = self.client.get(reverse('tasks:review_queue'))
        self.assertEqual(resp.status_code, 200)

        # 3. Meetings List
        resp = self.client.get(reverse('groups:meeting_list'))
        self.assertEqual(resp.status_code, 200)

        # 4. Schedule Meeting
        resp = self.client.get(reverse('groups:schedule_meeting'))
        self.assertEqual(resp.status_code, 200)

        # 5. Achievements List
        resp = self.client.get(reverse('progress:achievements'))
        self.assertEqual(resp.status_code, 200)

        # 6. Escalations List
        resp = self.client.get(reverse('progress:escalation_list'))
        self.assertEqual(resp.status_code, 200)

    def test_management_dashboard_and_workflows(self):
        """Management can access management dashboard, Wall of Fame, Announcements, Points Rules."""
        self.client.login(username='mgmt_test', password=self.password)
        
        # 1. Dashboard
        resp = self.client.get(reverse('dashboard:management_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # 2. Wall of Fame
        resp = self.client.get(reverse('core:wall_of_fame'))
        self.assertEqual(resp.status_code, 200)

        # 3. Manage Wall of Fame
        resp = self.client.get(reverse('core:manage_wall_of_fame'))
        self.assertEqual(resp.status_code, 200)

        # 4. Announcements List & Create
        resp = self.client.get(reverse('announcements:list'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('announcements:create_announcement'))
        self.assertEqual(resp.status_code, 200)

        # 5. Points Rules Admin
        resp = self.client.get(reverse('progress:points_rules'))
        self.assertEqual(resp.status_code, 200)

        # 6. Audit Log & At-Risk
        resp = self.client.get(reverse('progress:audit_log'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('progress:at_risk_list'))
        self.assertEqual(resp.status_code, 200)

    def test_coordinator_dashboard_and_admin_consoles(self):
        """Coordinator has full access to user directory, groups, pairings, and dashboards."""
        self.client.login(username='coord_test', password=self.password)
        
        # 1. Dashboard
        resp = self.client.get(reverse('dashboard:coordinator_dashboard'))
        self.assertEqual(resp.status_code, 200)

        # 2. User Directory & Add User forms
        resp = self.client.get(reverse('accounts:user_directory'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('accounts:add_mentor'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('accounts:add_mentee'))
        self.assertEqual(resp.status_code, 200)

        # 3. Groups List & Create
        resp = self.client.get(reverse('groups:group_list'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('groups:create_group'))
        self.assertEqual(resp.status_code, 200)

        # 4. Pairings Console & Create
        resp = self.client.get(reverse('groups:pairing_list'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('groups:create_pairing'))
        self.assertEqual(resp.status_code, 200)

    def test_global_search(self):
        """Global search returns matching users and groups."""
        self.client.login(username='coord_test', password=self.password)
        resp = self.client.get(reverse('core:search') + '?q=AI')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "AI Research Group")
