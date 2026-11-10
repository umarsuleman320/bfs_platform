from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date, time
from accounts.models import User
from groups.models import Group, GroupMembership, Pairing, Meeting, MeetingRequest
from tasks.models import Task, TaskAssignment, Submission, Review
from progress.models import Goal, PointsRule, Escalation, AuditLog, Achievement, Feedback
from announcements.models import Announcement
from helpdesk.models import HelpRequest, HelpResponse
from core.models import SiteSettings, Recognition
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Seeds complete demonstration dataset for the BFS Mentorship Platform'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding BFS Mentorship Platform demo data...")
        PASSWORD = 'BfsPlatform2026!'

        # 1. Site Settings
        settings, _ = SiteSettings.objects.get_or_create(id=1)
        settings.programme_name = "Bridge Fellowship Scheme (BFS)"
        settings.contact_email = "support@bfsplatform.org"
        settings.management_can_review = True
        settings.save()
        self.stdout.write("  [+] SiteSettings configured.")

        # 2. Points Rules
        rules = [
            ('task_completed', 'Task Completion Base XP', 20),
            ('task_on_time', 'On-Time Submission Bonus', 10),
            ('achievement_verified', 'Verified Milestone / Achievement', 50),
            ('meeting_attended', 'Mentorship Meeting Attendance', 15),
            ('streak_bonus', '7-Day Consistency Streak', 25),
        ]
        for key, label, pts in rules:
            PointsRule.objects.update_or_create(
                action_key=key,
                defaults={'label': label, 'points': pts, 'is_active': True}
            )
        self.stdout.write("  [+] Points Rules initialized.")

        # 3. Create Groups
        groups_data = [
            ("Research Group A - AI & Medical Imaging", "Deep learning architectures and computer vision applied to pathology and healthcare systems.", 10, 'open'),
            ("Research Group B - Cloud & DevOps Architecture", "Production microservices, Kubernetes orchestration, CI/CD pipelines and zero-downtime releases.", 10, 'approval'),
            ("Research Group C - Full-Stack & Systems Engineering", "Scalable backend frameworks, high-throughput APIs, asynchronous messaging, and modern frontends.", 10, 'approval'),
            ("Research Group D - Cyber Security & Governance", "Network defense, vulnerability assessments, penetration testing, and enterprise compliance.", 8, 'closed'),
            ("Research Group E - Data Science & Analytics", "Statistical modeling, predictive algorithms, business intelligence, and big data visualization.", 12, 'approval'),
        ]
        group_objs = {}
        for name, desc, cap, join_s in groups_data:
            grp, _ = Group.objects.update_or_create(
                name=name,
                defaults={'description': desc, 'capacity': cap, 'join_status': join_s, 'status': 'active'}
            )
            group_objs[name] = grp
        self.stdout.write(f"  [+] {len(group_objs)} Research Groups initialized.")

        # 4. Users: Coordinator & Management
        coord, _ = User.objects.get_or_create(username='coordinator_bfs')
        coord.first_name = "Amina"
        coord.last_name = "Bello"
        coord.email = "coordinator@bfsplatform.org"
        coord.role = 'coordinator'
        coord.is_staff = True
        coord.is_superuser = True
        coord.qualification = "Ph.D Computer Science"
        coord.expertise = "Programme Architecture & AI Systems"
        coord.bio = "Founding Coordinator of the Bridge Fellowship Scheme. Passionate about empowering early-career African researchers and engineers."
        coord.set_password(PASSWORD)
        coord.save()

        mgmt1, _ = User.objects.get_or_create(username='mgmt_1')
        mgmt1.first_name = "Dr. Oladipo"
        mgmt1.last_name = "Adeyemi"
        mgmt1.email = "mgmt1@bfsplatform.org"
        mgmt1.role = 'management'
        mgmt1.is_staff = True
        mgmt1.qualification = "Ph.D, FBCS"
        mgmt1.expertise = "Director of Research & Fellowship Strategy"
        mgmt1.bio = "Oversees programme-wide academic quality, industry advisory council, and research outcomes."
        mgmt1.set_password(PASSWORD)
        mgmt1.save()

        mgmt2, _ = User.objects.get_or_create(username='mgmt_2')
        mgmt2.first_name = "Folashade"
        mgmt2.last_name = "Okoli"
        mgmt2.email = "mgmt2@bfsplatform.org"
        mgmt2.role = 'management'
        mgmt2.is_staff = True
        mgmt2.qualification = "M.Sc, MBA"
        mgmt2.expertise = "Quality Assurance & Strategy Lead"
        mgmt2.bio = "Monitoring programme operational excellence, mentor effectiveness, and mentee career placement metrics."
        mgmt2.set_password(PASSWORD)
        mgmt2.save()

        # 5. Mentors
        mentors_info = [
            ('mentor_1', 'Chukwudi', 'Nnamdi', 'mentor1@bfsplatform.org', 'Ph.D AI/ML', 'Deep Learning, NLP, Healthcare AI', 'Senior AI Research Scientist at DeepHealth Labs. 8+ years mentoring fellows.'),
            ('mentor_2', 'Fatima', 'Zahra', 'mentor2@bfsplatform.org', 'M.Sc Cloud Systems', 'AWS, Kubernetes, Distributed Systems', 'Principal Infrastructure Architect. AWS Certified Solutions Architect Professional.'),
            ('mentor_3', 'Olumide', 'Bakare', 'mentor3@bfsplatform.org', 'B.Sc (Hons)', 'Django, React, Systems Design', 'Staff Software Engineer. Open-source contributor and technical team lead.'),
            ('mentor_4', 'Khadija', 'Aliyu', 'mentor4@bfsplatform.org', 'M.Sc Cyber Security, CISSP', 'Information Security & Zero Trust', 'Enterprise Security Consultant & Ethical Hacker. Focused on threat modeling.'),
            ('mentor_5', 'Emeka', 'Okafor', 'mentor5@bfsplatform.org', 'M.Sc Data Science', 'Big Data, Predictive Modeling, Time Series', 'Lead Data Scientist in FinTech. Specializing in financial modeling and Python analytics.'),
        ]
        mentor_objs = []
        for uname, fname, lname, email, qual, exp, bio in mentors_info:
            usr, _ = User.objects.get_or_create(username=uname)
            usr.first_name = fname
            usr.last_name = lname
            usr.email = email
            usr.role = 'mentor'
            usr.qualification = qual
            usr.expertise = exp
            usr.bio = bio
            usr.linkedin_url = f"https://linkedin.com/in/{uname}"
            usr.set_password(PASSWORD)
            usr.save()
            mentor_objs.append(usr)

        # Assign mentors to groups
        grp_list = list(group_objs.values())
        for idx, mentor in enumerate(mentor_objs):
            grp = grp_list[idx % len(grp_list)]
            grp.mentor = mentor
            grp.coordinator = coord
            grp.save()

        # 6. Mentees
        mentees_info = [
            ('mentee_1', 'Zainab', 'Suleiman', 'mentee1@bfsplatform.org', 'B.Sc Candidate', 'Final Year Undergraduate', 'Medical Imaging & LLMs', 'AI Research Scientist in Global Health', 'Passionate about deep learning applications for early detection of infectious diseases.'),
            ('mentee_2', 'Tunde', 'Balogun', 'mentee2@bfsplatform.org', 'B.Eng Electrical', 'Graduate Intern', 'Infrastructure Automation & CI/CD', 'Cloud Platform Architect', 'Specializing in container runtime security and cloud cost optimization.'),
            ('mentee_3', 'Blessing', 'Eze', 'mentee3@bfsplatform.org', 'B.Sc Computer Science', 'Recent Graduate', 'Python, Django, Microservices', 'Full-Stack Backend Architect', 'Eager to build high-concurrency distributed platforms with modern web standards.'),
            ('mentee_4', 'Musa', 'Garba', 'mentee4@bfsplatform.org', 'B.Tech Info Tech', 'Undergraduate Fellow', 'Network Defense & Threat Hunting', 'SOC Analyst & Penetration Tester', 'Fascinated by defensive operations and packet inspection.'),
            ('mentee_5', 'Grace', 'Adewale', 'mentee5@bfsplatform.org', 'B.Sc Statistics', 'Graduate Fellow', 'Statistical Inference, BI, PowerBI', 'Quantitative Data Analyst', 'Translating complex datasets into actionable executive insights.'),
        ]
        mentee_objs = []
        for uname, fname, lname, email, qual, acad, inter, goal, bio in mentees_info:
            usr, _ = User.objects.get_or_create(username=uname)
            usr.first_name = fname
            usr.last_name = lname
            usr.email = email
            usr.role = 'mentee'
            usr.qualification = qual
            usr.academic_status = acad
            usr.interests = inter
            usr.career_goal = goal
            usr.bio = bio
            usr.linkedin_url = f"https://linkedin.com/in/{uname}"
            usr.github_url = f"https://github.com/{uname}"
            usr.set_password(PASSWORD)
            usr.save()
            mentee_objs.append(usr)

        # 7. Group Memberships
        for idx, mentee in enumerate(mentee_objs):
            grp = grp_list[idx]
            GroupMembership.objects.get_or_create(group=grp, user=mentee)
        # Add mentee_3 also to Group A for cross-track demo
        GroupMembership.objects.get_or_create(group=grp_list[0], user=mentee_objs[2])
        self.stdout.write("  [+] Group memberships populated.")

        # 8. Pairings (1-to-1 and 1-to-many)
        for idx, mentee in enumerate(mentee_objs):
            mentor = mentor_objs[idx]
            grp = grp_list[idx]
            Pairing.objects.get_or_create(
                mentor=mentor, mentee=mentee,
                defaults={'group': grp, 'status': 'active', 'created_by': coord}
            )
        # 1-to-many pairing: mentor_1 also paired with mentee_3
        Pairing.objects.get_or_create(
            mentor=mentor_objs[0], mentee=mentee_objs[2],
            defaults={'group': grp_list[0], 'status': 'active', 'created_by': coord}
        )
        self.stdout.write("  [+] Pairings generated.")

        # 9. Tasks, Assignments, Submissions & Reviews
        now = timezone.now()
        
        # Task 1: Group A - Clinical Diagnostics Literature Review
        t1, _ = Task.objects.get_or_create(
            title="Literature Review on AI in Clinical Diagnostics",
            defaults={
                'description': "Survey modern transformer and CNN applications in pathology, radiological scans, and automated triage.",
                'category': "Research",
                'resources': "https://arxiv.org/abs/2301.00001\nhttps://nature.com/articles/ai-health",
                'submission_rules': "Provide a comprehensive 10-page document formatted in IEEE or ACM template stored on OneDrive with edit/view permissions.",
                'deadline': now + timedelta(days=7),
                'points_possible': 50,
                'target_type': 'group',
                'target_group': grp_list[0],
                'assigned_by': mentor_objs[0]
            }
        )
        # Assignment 1 for mentee_1 (Completed & Graded)
        a1_1, _ = TaskAssignment.objects.get_or_create(task=t1, mentee=mentee_objs[0], defaults={'status': 'completed'})
        a1_1.status = 'completed'
        a1_1.save()
        sub1, _ = Submission.objects.get_or_create(
            assignment=a1_1,
            defaults={
                'onedrive_link': "https://1drv.ms/u/s!Al7Xy9bfs_lit_review_v1",
                'mentee_notes': "Completed review covering 25 peer-reviewed papers from 2023-2026. Focuses on vision transformer self-attention mechanisms.",
                'version': 1
            }
        )
        Review.objects.update_or_create(
            submission=sub1,
            defaults={
                'reviewer': mentor_objs[0],
                'score': 48,
                'feedback': "Exceptional synthesis and critical evaluation of existing architectures! Your comparative analysis table in Section 4 is publication-grade.",
                'requires_resubmission': False
            }
        )

        # Assignment for mentee_3 in Group A (To Do)
        a1_3, _ = TaskAssignment.objects.get_or_create(task=t1, mentee=mentee_objs[2], defaults={'status': 'todo'})

        # Task 2: Group B - Cloud & Kubernetes Manifests
        t2, _ = Task.objects.get_or_create(
            title="Production Docker & Kubernetes Deployment Manifest",
            defaults={
                'description': "Design production-ready Helm charts and K8s manifests including horizontal pod autoscaling, ingress controller TLS termination, and health checks.",
                'category': "DevOps",
                'resources': "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/",
                'submission_rules': "Store your git repo archive and YAML manifests in your BFS OneDrive folder and submit the viewable URL.",
                'deadline': now + timedelta(days=3),
                'points_possible': 40,
                'target_type': 'group',
                'target_group': grp_list[1],
                'assigned_by': mentor_objs[1]
            }
        )
        a2_2, _ = TaskAssignment.objects.get_or_create(task=t2, mentee=mentee_objs[1], defaults={'status': 'submitted'})
        a2_2.status = 'submitted'
        a2_2.save()
        Submission.objects.get_or_create(
            assignment=a2_2,
            defaults={
                'onedrive_link': "https://1drv.ms/u/s!Bk9Z8_k8s_manifests_v1",
                'mentee_notes': "Configured cluster manifests with Prometheus annotations and resource limits.",
                'version': 1
            }
        )

        # Task 3: Population - Bi-Weekly Fellowship Progress Report
        t3, _ = Task.objects.get_or_create(
            title="Bi-Weekly Fellowship Progress & Reflection Log",
            defaults={
                'description': "Reflect on technical hurdles encountered, skill development milestones, and research learnings during the past fortnight.",
                'category': "Professional Development",
                'resources': "https://bfs-platform.org/handbook/reflections",
                'submission_rules': "Submit concise 2-page reflection report via OneDrive share link.",
                'deadline': now + timedelta(days=2),
                'points_possible': 20,
                'target_type': 'population',
                'assigned_by': coord
            }
        )
        for m in mentee_objs:
            a, _ = TaskAssignment.objects.get_or_create(task=t3, mentee=m)
            if m == mentee_objs[0]:
                a.status = 'completed'
                a.save()
                sub, _ = Submission.objects.get_or_create(
                    assignment=a,
                    defaults={'onedrive_link': "https://1drv.ms/u/s!Al7Xy9_reflection_log_m1", 'mentee_notes': "Sprint 2 reflections and blockers resolved.", 'version': 1}
                )
                Review.objects.update_or_create(submission=sub, defaults={'reviewer': mentor_objs[0], 'score': 20, 'feedback': "Great self-awareness and proactive learning."})
            elif m == mentee_objs[1]:
                a.status = 'completed'
                a.save()
                sub, _ = Submission.objects.get_or_create(
                    assignment=a,
                    defaults={'onedrive_link': "https://1drv.ms/u/s!Bk9Z8_reflection_log_m2", 'mentee_notes': "Reflection log submitted.", 'version': 1}
                )
                Review.objects.update_or_create(submission=sub, defaults={'reviewer': mentor_objs[1], 'score': 18, 'feedback': "Solid progress on Docker containers."})
            else:
                a.status = 'todo'
                a.save()

        # Task 4: Population Overdue - Ethics & Research Integrity
        t4, _ = Task.objects.get_or_create(
            title="Foundational Ethics & Research Integrity Certification",
            defaults={
                'description': "Complete the institutional research ethics online module and upload your course completion certificate.",
                'category': "Compliance",
                'resources': "https://research-ethics.org/modules/core-2026",
                'submission_rules': "Upload completion certificate PDF to OneDrive and share accessible link.",
                'deadline': now - timedelta(days=5), # OVERDUE!
                'points_possible': 30,
                'target_type': 'population',
                'assigned_by': mgmt1
            }
        )
        a4_4, _ = TaskAssignment.objects.get_or_create(task=t4, mentee=mentee_objs[3], defaults={'status': 'todo'})
        a4_4.status = 'todo'
        a4_4.save() # This triggers is_overdue property

        a4_5, _ = TaskAssignment.objects.get_or_create(task=t4, mentee=mentee_objs[4], defaults={'status': 'resubmission'})
        a4_5.status = 'resubmission'
        a4_5.save()
        sub4_5, _ = Submission.objects.get_or_create(
            assignment=a4_5,
            defaults={'onedrive_link': "https://1drv.ms/u/s!Grace_certificate_draft", 'mentee_notes': "Submitted screenshot of score.", 'version': 1}
        )
        Review.objects.update_or_create(
            submission=sub4_5,
            defaults={
                'reviewer': mentor_objs[4],
                'score': 15,
                'feedback': "Screenshot is blurry. Please provide the official verified PDF certificate link.",
                'requires_resubmission': True
            }
        )

        # Task 5: Individual Task for Mentee 3
        t5, _ = Task.objects.get_or_create(
            title="REST API Microservice Specification & Schema Design",
            defaults={
                'description': "Write OpenAPI 3.0 specification for authentication and notification microservices using JWT and Redis tokens.",
                'category': "Software Architecture",
                'resources': "https://swagger.io/specification/",
                'submission_rules': "OpenAPI JSON/YAML on OneDrive.",
                'deadline': now + timedelta(days=10),
                'points_possible': 45,
                'target_type': 'individual',
                'assigned_by': mentor_objs[2]
            }
        )
        t5.selected_mentees.add(mentee_objs[2])
        TaskAssignment.objects.get_or_create(task=t5, mentee=mentee_objs[2], defaults={'status': 'todo'})
        self.stdout.write("  [+] Tasks, assignments, submissions, and reviews seeded.")

        # 10. Goals
        goals_data = [
            (mentee_objs[0], "Publish First-Author Paper in High-Impact AI Journal", "Complete comparative analysis and submit manuscript.", 'active', False),
            (mentee_objs[0], "Master PyTorch Model Quantization & TensorRT", "Implement FP16 and INT8 optimizations.", 'completed', True),
            (mentee_objs[1], "Pass AWS Certified Solutions Architect Associate", "Score >= 800 on practice exams.", 'active', False),
            (mentee_objs[2], "Architect High-Throughput Event-Driven Microservices", "Build async pipeline processing 5,000 req/sec.", 'active', True),
            (mentee_objs[3], "Complete Certified Ethical Hacker (CEH) Practice Labs", "Cover 18 lab modules on packet sniffing and perimeter defense.", 'active', True),
            (mentee_objs[4], "Deploy Interactive Streamlit & PowerBI Research Dashboard", "Provide live telemetry on programme KPIs.", 'active', False),
        ]
        for user, title, desc, status, priv in goals_data:
            Goal.objects.get_or_create(mentee=user, title=title, defaults={'description': desc, 'status': status, 'is_private': priv})
        self.stdout.write("  [+] Personal Goals seeded.")

        # 11. Achievements
        ach1, _ = Achievement.objects.get_or_create(
            mentee=mentee_objs[0],
            title="Co-Authored Paper Accepted at IEEE HealthTech 2026",
            defaults={
                'category': 'publication',
                'organisation': "IEEE Transactions on Medical Informatics",
                'description': "Full research paper titled 'Attention Mechanisms for Deep Cellular Segmentation' accepted for oral presentation.",
                'achievement_date': date(2026, 10, 15),
                'evidence_link': "https://1drv.ms/u/s!ieee_paper_acceptance_letter",
                'status': 'verified',
                'reviewed_by': mentor_objs[0],
                'reviewed_at': now - timedelta(days=12),
                'review_notes': "Outstanding achievement! Represents high scientific rigor."
            }
        )
        ach2, _ = Achievement.objects.get_or_create(
            mentee=mentee_objs[1],
            title="AWS Certified Cloud Practitioner Credential",
            defaults={
                'category': 'certification',
                'organisation': "Amazon Web Services",
                'description': "Successfully validated cloud architecture fundamentals with 912/1000 score.",
                'achievement_date': date(2026, 10, 20),
                'evidence_link': "https://1drv.ms/u/s!aws_cert_badge_tunde",
                'status': 'verified',
                'reviewed_by': mentor_objs[1],
                'reviewed_at': now - timedelta(days=7),
                'review_notes': "Verified against Credly official verification API."
            }
        )
        ach3, _ = Achievement.objects.get_or_create(
            mentee=mentee_objs[2],
            title="Runner-Up: National Open-Source Innovation Hackathon",
            defaults={
                'category': 'award',
                'organisation': "TechFest Nigeria & GitHub Campus",
                'description': "Built distributed disaster response alert system using Django and WebSockets.",
                'achievement_date': date(2026, 10, 28),
                'evidence_link': "https://1drv.ms/u/s!hackathon_certificate_blessing",
                'status': 'pending',
                'review_notes': "Awaiting mentor review."
            }
        )
        self.stdout.write("  [+] Achievements seeded.")

        # 12. Meetings & Meeting Requests
        p1 = Pairing.objects.filter(mentor=mentor_objs[0], mentee=mentee_objs[0]).first()
        Meeting.objects.get_or_create(
            title="Sprint 3 Research Alignment & Diagnostics Model Review",
            defaults={
                'pairing': p1,
                'group': grp_list[0],
                'mentor': mentor_objs[0],
                'mentee': mentee_objs[0],
                'agenda': "1. Review literature review draft findings.\n2. Discuss dataset preprocessing for radiological scans.\n3. Agree on next sprint milestones.",
                'meeting_date': (now + timedelta(days=1)).date(),
                'meeting_time': time(14, 0),
                'meeting_platform': "Microsoft Teams",
                'meeting_link': "https://teams.microsoft.com/l/meetup-join/19%3ameeting_bfs_ai_lab",
                'status': 'scheduled',
                'created_by': mentor_objs[0]
            }
        )
        Meeting.objects.get_or_create(
            title="Initial Fellowship Orientation & Career Mapping",
            defaults={
                'pairing': p1,
                'group': grp_list[0],
                'mentor': mentor_objs[0],
                'mentee': mentee_objs[0],
                'agenda': "Welcome session, syllabus walk-through, setup development environments.",
                'meeting_date': (now - timedelta(days=14)).date(),
                'meeting_time': time(10, 0),
                'meeting_platform': "Microsoft Teams",
                'meeting_link': "https://teams.microsoft.com/l/meetup-join/19%3ameeting_bfs_archive",
                'status': 'completed',
                'created_by': mentor_objs[0]
            }
        )
        MeetingRequest.objects.get_or_create(
            mentee=mentee_objs[2],
            mentor=mentor_objs[2],
            topic="Guidance on Django Channels & WebSocket Scalability",
            defaults={
                'pairing': Pairing.objects.filter(mentor=mentor_objs[2], mentee=mentee_objs[2]).first(),
                'agenda': "Would love advice on redis channel layers and connection connection pooling under high load.",
                'proposed_date': (now + timedelta(days=4)).date(),
                'proposed_time': time(16, 0),
                'status': 'pending'
            }
        )
        self.stdout.write("  [+] Meetings and Meeting Requests seeded.")

        # 13. Feedback
        Feedback.objects.get_or_create(
            submitted_by=mentee_objs[0],
            recipient=mentor_objs[0],
            defaults={
                'category': 'session',
                'rating': 5,
                'content': "Dr. Nnamdi provided exceptionally structured and constructive feedback on my literature review. The research roadmap is crystal clear.",
                'is_permanent': True
            }
        )
        Feedback.objects.get_or_create(
            submitted_by=mentor_objs[0],
            recipient=mentee_objs[0],
            defaults={
                'category': 'learning',
                'rating': 5,
                'content': "Zainab demonstrates extraordinary analytical discipline, attention to mathematical detail, and proactive initiative.",
                'is_permanent': True
            }
        )
        Feedback.objects.get_or_create(
            submitted_by=mentee_objs[1],
            recipient=mentor_objs[1],
            defaults={
                'category': 'communication',
                'rating': 5,
                'content': "Engr. Fatima shared real-world enterprise infrastructure tips that helped me understand Kubernetes manifests much faster.",
                'is_permanent': True
            }
        )
        self.stdout.write("  [+] Evaluative Feedback seeded.")

        # 14. Announcements
        Announcement.objects.get_or_create(
            title="Welcome to the 2026 Bridge Fellowship Scheme Cohort!",
            defaults={
                'message': "We are thrilled to formally launch the 2026 BFS Mentorship Cycle. Please check your assigned Research Group, review upcoming task deadlines, connect with your designated mentor, and set your Q1 Personal Development Goals.",
                'audience': 'all',
                'is_priority': True,
                'created_by': coord
            }
        )
        Announcement.objects.get_or_create(
            title="Mandatory Workshop: High-Impact Research Writing & Peer Review",
            defaults={
                'message': "Join our distinguished visiting research fellows this Thursday at 4:00 PM WAT for an interactive masterclass on crafting publication-grade methodology and data visualization sections.",
                'audience': 'mentees',
                'is_priority': False,
                'created_by': mgmt1
            }
        )
        Announcement.objects.get_or_create(
            title="Faculty Briefing: Mid-Quarter Review Protocols & Escalations",
            defaults={
                'message': "Mentors are reminded to review submitted assignments within 72 hours of upload and flag disengaged or defaulting fellows via the Escalation console.",
                'audience': 'mentors',
                'is_priority': False,
                'created_by': mgmt2
            }
        )
        self.stdout.write("  [+] Announcements seeded.")

        # 15. Help Desk Tickets
        tkt1, _ = HelpRequest.objects.get_or_create(
            mentee=mentee_objs[0],
            subject="Accessing IEEE Xplore & Springer Institutional Credentials",
            defaults={
                'message': "Hello Help Desk team, I require proxy credentials to download full-text PDFs for our comparative analysis in Research Group A.",
                'priority': 'high',
                'status': 'in_progress',
                'assigned_to': mentor_objs[0]
            }
        )
        HelpResponse.objects.get_or_create(
            request=tkt1,
            responder=mentor_objs[0],
            defaults={
                'message': "Hi Zainab, institutional access credentials have been provisioned via the academic portal. Check your student inbox for the VPN profile."
            }
        )

        tkt2, _ = HelpRequest.objects.get_or_create(
            mentee=mentee_objs[3],
            subject="Clarification on Ethics Course Certificate Upload Format",
            defaults={
                'message': "Does the platform accept Coursera verification badges or do we strictly need the university signed PDF certificate?",
                'priority': 'normal',
                'status': 'resolved',
                'assigned_to': coord
            }
        )
        HelpResponse.objects.get_or_create(
            request=tkt2,
            responder=coord,
            defaults={
                'message': "Both are accepted, Musa! Just ensure your OneDrive share link has viewer access enabled so your mentor can review."
            }
        )

        HelpRequest.objects.get_or_create(
            mentee=mentee_objs[4],
            subject="Schedule adjustment for statistical modeling group workshop",
            defaults={
                'message': "Requesting permission to attend the afternoon breakout session due to semester exam timetable conflicts.",
                'priority': 'normal',
                'status': 'open',
                'assigned_to': mentor_objs[4]
            }
        )
        self.stdout.write("  [+] Help Desk tickets seeded.")

        # 16. Escalations
        Escalation.objects.get_or_create(
            mentee=mentee_objs[3],
            defaults={
                'raised_by': mentor_objs[3],
                'reason': "Mentee has missed two consecutive group check-ins and the foundational Ethics certification task is overdue by 5 days.",
                'recommended_action': "Coordinator direct telephone outreach and check-in to confirm welfare and internet connectivity.",
                'status': 'open'
            }
        )
        self.stdout.write("  [+] Escalation flagged.")

        # 17. Recognition (Wall of Fame)
        Recognition.objects.get_or_create(
            user=mentee_objs[0],
            type='mentee_of_month',
            defaults={
                'period': "October 2026",
                'badge_title': "Top Research Performer",
                'note': "For co-authoring a peer-reviewed publication in IEEE and achieving a 100% on-time task submission score."
            }
        )
        Recognition.objects.get_or_create(
            user=mentor_objs[0],
            type='mentor_of_month',
            defaults={
                'period': "October 2026",
                'badge_title': "Master Mentor of the Month",
                'note': "Exemplary mentorship engagement, detailed 24-hour turnaround reviews, and inspiring guidance in AI research."
            }
        )
        Recognition.objects.get_or_create(
            user=mentor_objs[1],
            type='hall_of_fame',
            defaults={
                'period': "Inaugural Cohort 2025",
                'badge_title': "Distinguished Fellowship Faculty",
                'note': "Pioneered the Cloud Architecture curriculum and successfully guided 12 fellows into enterprise cloud engineering positions."
            }
        )
        self.stdout.write("  [+] Recognition Wall of Fame seeded.")

        # 18. Notifications
        Notification.objects.get_or_create(
            user=mentee_objs[0],
            title="Task Graded: Literature Review",
            defaults={
                'verb': 'submission_reviewed',
                'message': "Dr. Chukwudi Nnamdi scored your submission 48/50. Great work!",
                'link': "/tasks/",
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            user=mentor_objs[1],
            title="New Submission Ready for Review",
            defaults={
                'verb': 'task_submitted',
                'message': "Tunde Balogun submitted Docker & Kubernetes Deployment Manifest.",
                'link': "/tasks/review/",
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            user=mgmt1,
            title="New Mentee Escalation Raised",
            defaults={
                'verb': 'escalation_raised',
                'message': "Mentor Khadija Aliyu raised an escalation for mentee Musa Garba.",
                'link': "/dashboard/management/",
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            user=coord,
            title="New Help Desk Ticket",
            defaults={
                'verb': 'ticket_created',
                'message': "Grace Adewale submitted ticket regarding workshop schedule adjustment.",
                'link': "/helpdesk/",
                'is_read': False
            }
        )
        self.stdout.write("  [+] Notifications seeded.")

        # 19. Audit Logs
        audit_events = [
            (coord, "Platform Initialized", "Coordinator initialized 2026 Fellowship cycle and group rosters."),
            (mentor_objs[0], "Grade Published", "Scored mentee_1 submission for Task 1: 48/50."),
            (mentor_objs[0], "Achievement Verified", "Verified IEEE publication achievement for mentee_1."),
            (mentor_objs[3], "Escalation Created", "Flagged mentee_4 for disengagement and overdue tasks."),
            (mgmt1, "Announcement Published", "Broadcasted research writing workshop announcement to all mentees."),
        ]
        for usr, act, det in audit_events:
            AuditLog.objects.get_or_create(
                user=usr, action=act,
                defaults={'details': det, 'ip_address': '127.0.0.1'}
            )
        self.stdout.write("  [+] Audit logs recorded.")

        self.stdout.write(self.style.SUCCESS(
            "\nBFS Mentorship Platform Demonstration Environment seeded successfully!\n"
            f"All accounts initialized with password: {PASSWORD}\n"
            "Demo Accounts:\n"
            "  - Coordinator: coordinator_bfs\n"
            "  - Management:  mgmt_1, mgmt_2\n"
            "  - Mentors:     mentor_1 to mentor_5\n"
            "  - Mentees:     mentee_1 to mentee_5\n"
        ))
