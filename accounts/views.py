from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    from accounts.models import CustomUser
    from products.models import Product
    from orders.models import Order

    # عدد الفلاحين المعتمدين
    farmers_count = CustomUser.objects.filter(role='farmer', is_approved=True).count()

    # عدد المنتجات المتاحة
    products_count = Product.objects.filter(is_available=True).count()

    # عدد الناقلين المعتمدين
    transporters_count = CustomUser.objects.filter(role='transporter', is_approved=True).count()

    # نسبة الرضا: الطلبات المسلّمة من مجموع الطلبات المنتهية
    total_closed = Order.objects.filter(status__in=['delivered', 'cancelled']).count()
    delivered = Order.objects.filter(status='delivered').count()
    if total_closed > 0:
        satisfaction = round((delivered / total_closed) * 100)
    else:
        satisfaction = 0

    # عدد الولايات المغطاة (من الشحنات المسلّمة)
    wilayas_count = Order.objects.filter(
        shipping_wilaya__isnull=False
    ).exclude(shipping_wilaya='').values('shipping_wilaya').distinct().count()

    stats = {
        'farmers_count': farmers_count,
        'products_count': products_count,
        'transporters_count': transporters_count,
        'satisfaction': satisfaction,
        'wilayas_count': wilayas_count,
    }

    return render(request, 'index.html', {'stats': stats})


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