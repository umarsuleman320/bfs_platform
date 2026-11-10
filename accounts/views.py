from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django import forms
from .models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.contrib import messages

# --- REGISTRATION FORM ---
# This defines what fields appear on the signup page
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Create Password',
        'class': 'input-field'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

# --- LOGIN VIEW ---
# Handles logging in and sending users to the right dashboard based on role
class BFSLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.role == 'mentee':
            return reverse_lazy('dashboard:mentee_dashboard')
        elif user.role == 'mentor':
            return reverse_lazy('dashboard:mentor_dashboard')
        elif user.role == 'management':
            return reverse_lazy('dashboard:management_dashboard')
        elif user.role == 'coordinator':
            return reverse_lazy('dashboard:coordinator_dashboard')
        return reverse_lazy('core:home')

# --- REGISTER VIEW ---
# Restricted: Only Programme Coordinator and Management can create new users
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:user_directory')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(
                request, 
                "Self-registration is closed. New accounts are provisioned exclusively by Programme Coordinators and Management."
            )
            return redirect('accounts:login')
        if request.user.role not in ['coordinator', 'management']:
            messages.error(
                request, 
                "Access Denied: Only Programme Coordinators and Management can register new fellows."
            )
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.role = 'mentee'
        user.is_verified = True
        user.save()
        messages.success(self.request, f"Fellow account '{user.username}' successfully created.")
        return redirect(self.success_url)
    

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'accounts/profile.html'
    fields = [
        'first_name', 'last_name', 'phone', 'bio', 
        'avatar_url', 'qualification', 'expertise',
        'academic_status', 'interests', 'career_goal',
        'linkedin_url', 'github_url', 'cv_url'
    ]
    success_url = reverse_lazy('dashboard:home')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)


# --- ADMINISTRATIVE USER MANAGEMENT MODULE ---
from django.shortcuts import get_object_or_404
from django.db.models import Q
from accounts.permissions import role_required
from progress.services import create_audit_log

@role_required('coordinator', 'management')
def user_directory(request):
    """
    Searchable and filterable directory of all users in the system.
    Only accessible to Coordinator and Management roles.
    """
    role_filter = request.GET.get('role', 'all')
    search_query = request.GET.get('q', '').strip()

    users = User.objects.all().order_by('-date_joined')

    if role_filter and role_filter != 'all':
        users = users.filter(role=role_filter)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(expertise__icontains=search_query) |
            Q(academic_status__icontains=search_query) |
            Q(interests__icontains=search_query)
        )

    context = {
        'users_list': users,
        'current_role': role_filter,
        'search_query': search_query,
        'total_count': users.count(),
        'mentee_count': User.objects.filter(role='mentee').count(),
        'mentor_count': User.objects.filter(role='mentor').count(),
        'management_count': User.objects.filter(role='management').count(),
        'coordinator_count': User.objects.filter(role='coordinator').count(),
    }
    return render(request, 'accounts/user_list.html', context)


@role_required('coordinator', 'management')
def add_mentor(request):
    """Admin form to register a new mentor with expertise and qualifications."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        expertise = request.POST.get('expertise', '').strip()
        bio = request.POST.get('bio', '').strip()
        phone = request.POST.get('phone', '').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'accounts/user_form.html', {'form_type': 'mentor'})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already registered.")
            return render(request, 'accounts/user_form.html', {'form_type': 'mentor'})

        mentor = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='mentor',
            qualification=qualification,
            expertise=expertise,
            bio=bio,
            phone=phone,
            is_verified=True,
            is_active=True
        )
        mentor.set_password(password)
        mentor.save()

        create_audit_log(
            user=request.user,
            action="Mentor Created",
            details=f"Created mentor account: {mentor.get_full_name()} ({username}) with expertise in {expertise}"
        )
        messages.success(request, f"Mentor '{mentor.get_full_name() or username}' successfully added!")
        return redirect('accounts:user_directory')

    return render(request, 'accounts/user_form.html', {'form_type': 'mentor'})


@role_required('coordinator', 'management')
def add_mentee(request):
    """Admin form to register a new mentee with academic background and goals."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        academic_status = request.POST.get('academic_status', '').strip()
        interests = request.POST.get('interests', '').strip()
        career_goal = request.POST.get('career_goal', '').strip()
        bio = request.POST.get('bio', '').strip()
        phone = request.POST.get('phone', '').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'accounts/user_form.html', {'form_type': 'mentee'})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already registered.")
            return render(request, 'accounts/user_form.html', {'form_type': 'mentee'})

        mentee = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='mentee',
            academic_status=academic_status,
            interests=interests,
            career_goal=career_goal,
            bio=bio,
            phone=phone,
            is_verified=True,
            is_active=True
        )
        mentee.set_password(password)
        mentee.save()

        create_audit_log(
            user=request.user,
            action="Mentee Created",
            details=f"Created mentee account: {mentee.get_full_name()} ({username})"
        )
        messages.success(request, f"Mentee '{mentee.get_full_name() or username}' successfully registered!")
        return redirect('accounts:user_directory')

    return render(request, 'accounts/user_form.html', {'form_type': 'mentee'})


@role_required('coordinator', 'management')
def promote_user(request, user_id):
    """Promotes an existing user to Management or Coordinator without re-registering."""
    target_user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('new_role')

    if new_role in ['mentor', 'management', 'coordinator', 'mentee']:
        old_role = target_user.get_role_display()
        target_user.role = new_role
        if new_role == 'coordinator':
            target_user.is_staff = True
        target_user.save()

        create_audit_log(
            user=request.user,
            action="Role Promotion",
            details=f"Promoted {target_user.username} from {old_role} to {target_user.get_role_display()}."
        )
        messages.success(request, f"Role Updated: {target_user.username} is now a {target_user.get_role_display()}.")

    return redirect('accounts:user_directory')


@role_required('coordinator', 'management')
def toggle_user_status(request, user_id):
    """Activates or deactivates a user account."""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('accounts:user_directory')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status_str = "activated" if target_user.is_active else "deactivated"
    create_audit_log(
        user=request.user,
        action="Account Status Change",
        details=f"User {target_user.username} was {status_str} by {request.user.username}."
    )
    messages.info(request, f"Account {target_user.username} has been {status_str}.")
    return redirect('accounts:user_directory')


@role_required('mentee', 'mentor', 'management', 'coordinator')
def user_detail(request, user_id):
    """Detailed profile view of a mentor, mentee, or coordinator."""
    target_user = get_object_or_404(User, id=user_id)
    
    # Check permissions: mentees can view mentors or group peers, mentors can view their mentees, leaders can view all
    context = {
        'profile_user': target_user,
        'groups': target_user.group_membership.all().select_related('group'),
    }
    return render(request, 'accounts/user_detail.html', context)