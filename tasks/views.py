from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from accounts.permissions import role_required
from .models import Task, TaskAssignment, Submission, Review
from groups.models import Group, GroupMembership
from progress.services import create_audit_log
from notifications.services import notify

User = get_user_model()

# --- MENTOR/ADMIN: INITIALIZE WORK ---
@role_required('mentor', 'coordinator', 'management')
def initialize_task(request):
    """ Creates a Master Task and fans it out to individual, selected, group, or all mentees. """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        desc = request.POST.get('description', '').strip()
        deadline = request.POST.get('deadline')
        points = int(request.POST.get('points_possible', 20))
        target_type = request.POST.get('target_type', 'group')
        category = request.POST.get('category', '').strip()
        resources = request.POST.get('resources', '').strip()
        submission_rules = request.POST.get('submission_rules', '').strip()
        
        task = Task.objects.create(
            title=title,
            description=desc,
            category=category,
            resources=resources,
            submission_rules=submission_rules,
            deadline=deadline,
            points_possible=points,
            target_type=target_type,
            assigned_by=request.user
        )

        mentees_to_assign = []

        if target_type == 'group':
            group_id = request.POST.get('group_id')
            group = get_object_or_404(Group, id=group_id)
            task.target_group = group
            task.save()
            mentees_to_assign = list(User.objects.filter(group_membership__group=group))

        elif target_type == 'individual':
            mentee_id = request.POST.get('mentee_id')
            mentee = get_object_or_404(User, id=mentee_id)
            mentees_to_assign = [mentee]

        elif target_type == 'selected':
            mentee_ids = request.POST.getlist('mentee_ids')
            mentees_to_assign = list(User.objects.filter(id__in=mentee_ids))
            task.selected_mentees.set(mentees_to_assign)

        elif target_type in ['population', 'all']:
            mentees_to_assign = list(User.objects.filter(role='mentee', is_active=True))

        for mentee in mentees_to_assign:
            assignment, created = TaskAssignment.objects.get_or_create(task=task, mentee=mentee)
            notify(
                user=mentee,
                verb='task_assigned',
                title=f'New Task: {title}',
                message=f"You have been assigned '{title}' (Deadline: {deadline}, Points: {points} XP).",
                link=f'/tasks/{assignment.id}/'
            )

        create_audit_log(
            user=request.user,
            action="Task Distributed",
            details=f"Task '{title}' distributed to {len(mentees_to_assign)} mentees ({target_type})."
        )
        
        messages.success(request, f"Task '{title}' distributed to {len(mentees_to_assign)} fellows.")
        return redirect('dashboard:home')
    return redirect('dashboard:home')


# --- COORDINATOR: GLOBAL TASK MANAGER ---
@role_required('coordinator', 'management')
def global_task_manager(request):
    """ Supreme oversight of every task in the system. """
    tasks = Task.objects.all().order_by('-created_at').annotate(
        total=Count('assignments'),
        done=Count('assignments', filter=Q(assignments__status='completed')),
        pending=Count('assignments', filter=Q(assignments__status='submitted'))
    )
    return render(request, 'tasks/task_manager.html', {'tasks': tasks})


# --- MENTOR: REVIEW QUEUE ---
@role_required('mentor', 'coordinator')
def review_queue(request):
    """ Mentor's grading inbox (Oldest First). """
    pending_submissions = Submission.objects.filter(
        assignment__task__assigned_by=request.user
    ).exclude(review__isnull=False).select_related('assignment', 'assignment__task', 'assignment__mentee').order_by('submitted_at')

    return render(request, 'tasks/review_queue.html', {
        'submissions': pending_submissions,
        'count': pending_submissions.count()
    })


# --- MENTEE: TASK REPOSITORY ---
@role_required('mentee')
def my_tasks_list(request):
    assignments = TaskAssignment.objects.filter(mentee=request.user).select_related('task').order_by('task__deadline')
    return render(request, 'tasks/task_list.html', {'assignments': assignments})


# --- MENTEE: VIEW TASK DETAILS ---
@role_required('mentee', 'mentor', 'coordinator')
def task_detail(request, assignment_id):
    assignment = get_object_or_404(TaskAssignment, id=assignment_id)
    if request.user.role == 'mentee' and assignment.mentee != request.user:
        raise PermissionDenied
    return render(request, 'tasks/task_detail.html', {'assignment': assignment})


# --- MENTEE: SUBMIT ONEDRIVE LINK ---
@role_required('mentee')
def submit_work(request, assignment_id):
    """ Saves OneDrive URL and triggers Audit Log. """
    assignment = get_object_or_404(TaskAssignment, id=assignment_id, mentee=request.user)
    
    if request.method == 'POST':
        link = request.POST.get('onedrive_link')
        notes = request.POST.get('mentee_notes')

        last_submission = assignment.submissions.order_by('-version').first()
        new_version = (last_submission.version + 1) if last_submission else 1

        Submission.objects.create(
            assignment=assignment, onedrive_link=link,
            mentee_notes=notes, version=new_version
        )

        assignment.status = 'submitted'
        assignment.save()

        # Notify Assigner / Mentor
        if assignment.task.assigned_by:
            notify(
                user=assignment.task.assigned_by,
                verb='submission_received',
                title=f'Work Submitted: {assignment.task.title}',
                message=f"{request.user.get_full_name() or request.user.username} submitted deliverable v{new_version}.",
                link='/tasks/review-queue/'
            )

        # --- AUDIT ---
        create_audit_log(
            user=request.user,
            action="Payload Submission",
            details=f"Submitted v{new_version} for task: {assignment.task.title}"
        )

        messages.success(request, f"Deliverable v{new_version} successfully transmitted for evaluation.")
    
    return redirect('dashboard:mentee_dashboard')


# --- MENTOR: GRADING SUITE ---
@role_required('mentor', 'coordinator', 'management')
def review_submission(request, submission_id):
    """ Official Evaluation logic with Audit, Notifications, and Point triggers. """
    submission = get_object_or_404(Submission, id=submission_id)
    assignment = submission.assignment

    if request.user.role == 'mentor' and assignment.task.assigned_by != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')
        needs_redo = request.POST.get('requires_resubmission') == 'on'

        Review.objects.update_or_create(
            submission=submission,
            defaults={
                'reviewer': request.user,
                'score': score,
                'feedback': feedback,
                'requires_resubmission': needs_redo
            }
        )

        if needs_redo:
            assignment.status = 'resubmission'
            audit_action = "Resubmission Requested"
            messages.warning(request, f"Feedback published. Resubmission requested for {assignment.mentee.username}.")
            notify(
                user=assignment.mentee,
                verb='resubmission_required',
                title=f'Resubmission Required: {assignment.task.title}',
                message=f"Mentor reviewed your submission with score {score}/{assignment.task.points_possible}. Feedback: {feedback[:100]}",
                link=f'/tasks/{assignment.id}/'
            )
        else:
            assignment.status = 'completed'
            audit_action = "Grade Published"
            messages.success(request, f"Evaluation confirmed. {assignment.mentee.username} scored {score}/{assignment.task.points_possible}.")
            notify(
                user=assignment.mentee,
                verb='submission_reviewed',
                title=f'Grade Published: {assignment.task.title}',
                message=f"Congratulations! You scored {score}/{assignment.task.points_possible} on '{assignment.task.title}'.",
                link=f'/tasks/{assignment.id}/'
            )
        
        assignment.save()

        # --- AUDIT ---
        create_audit_log(
            user=request.user,
            action=audit_action,
            details=f"Evaluated {assignment.mentee.username} on '{assignment.task.title}'. Score: {score}/{assignment.task.points_possible}."
        )

        return redirect('tasks:review_queue')

    return render(request, 'tasks/review_suite.html', {'submission': submission})