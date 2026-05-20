from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.is_approved = False
            user.save()
            return redirect('pending_approval')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def pending_approval(request):
    return render(request, 'registration/pending_approval.html')


class CustomLoginView(LoginView):
    def form_invalid(self, form):
        username = self.request.POST.get('username', '')
        password = self.request.POST.get('password', '')
        try:
            from accounts.models import CustomUser
            user = CustomUser.objects.get(username=username)
            if user.check_password(password) and not user.is_approved:
                return redirect('pending_approval')
        except CustomUser.DoesNotExist:
            pass
        return super().form_invalid(form)


@login_required
def dashboard(request):
    user = request.user
    if not user.is_approved and not user.is_superuser:
        logout(request)
        messages.error(request, 'Your account is pending admin approval.')
        return redirect('login')
    if user.is_superuser or user.is_staff:
        return redirect('ministry_dashboard')
    if user.role == 'farmer':
        return redirect('farmer_dashboard')
    elif user.role == 'buyer':
        return redirect('buyer_dashboard')
    elif user.role == 'transporter':
        return redirect('transporter_dashboard')
    elif user.role == 'ministry':
        return redirect('ministry_dashboard')
    return redirect('login')