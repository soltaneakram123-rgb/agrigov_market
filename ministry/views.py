from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Q
from django.utils import timezone
import json

from accounts.models import CustomUser
from orders.models import Order, Delivery
from products.models import Product, ProductCategory, ProductType
from farms.models import Farm
from .models import OfficialPrice, Policy, Complaint, SeasonalPriceRange, SEASON_CHOICES, current_season


def ministry_required(view_func):
    """Decorator: allow only ministry or superuser accounts."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_superuser or request.user.role == 'ministry'):
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Dashboard ────────────────────────────────────────────────────────────────

@ministry_required
def ministry_dashboard(request):
    context = {
        'total_users':    CustomUser.objects.count(),
        'total_farmers':  CustomUser.objects.filter(role='farmer').count(),
        'total_buyers':   CustomUser.objects.filter(role='buyer').count(),
        'total_orders':   Order.objects.count(),
        'total_products': Product.objects.count(),
        'total_farms':    Farm.objects.count(),
        'total_revenue':  Order.objects.filter(status='delivered').aggregate(
                              t=Sum('total_amount'))['t'] or 0,
        'pending_orders': Order.objects.filter(status='pending').count(),
        'recent_orders':  Order.objects.select_related('buyer', 'farmer')
                              .order_by('-created_at')[:10],
        'official_prices': OfficialPrice.objects.select_related('category')
                              .order_by('-valid_from')[:10],
        'categories':     ProductCategory.objects.annotate(
                              product_count=Count('product')),
        'open_complaints': Complaint.objects.filter(status='open').count(),
        'active_policies': Policy.objects.filter(status='active').count(),
        'pending_approvals': CustomUser.objects.filter(is_approved=False, is_superuser=False).count(),
        # ── Chart data ────────────────────────────────────────────────
        'orders_pending':   Order.objects.filter(status='pending').count(),
        'orders_confirmed': Order.objects.filter(status='confirmed').count(),
        'orders_transit':   Order.objects.filter(status='in_transit').count(),
        'orders_delivered': Order.objects.filter(status='delivered').count(),
        'orders_cancelled': Order.objects.filter(status='cancelled').count(),
        'total_transporters': CustomUser.objects.filter(role='transporter').count(),
        'total_ministry':     CustomUser.objects.filter(role='ministry').count(),
        'products_available': Product.objects.filter(is_available=True).count(),
        'products_unavailable': Product.objects.filter(is_available=False).count(),
        'category_stats': list(
            ProductCategory.objects.annotate(cnt=Count('product'))
            .values('name', 'cnt').order_by('-cnt')[:7]
        ),
    }
    return render(request, 'ministry/ministry_dashboard.html', context)


# ─── Users ────────────────────────────────────────────────────────────────────

@ministry_required
def ministry_users(request):
    role = request.GET.get('role', '')
    search = request.GET.get('q', '')
    approval = request.GET.get('approval', '')
    users = CustomUser.objects.all()
    if role:
        users = users.filter(role=role)
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
    if approval == 'pending':
        users = users.filter(is_approved=False, is_superuser=False)
    elif approval == 'approved':
        users = users.filter(is_approved=True)
    stats = {
        'total': CustomUser.objects.count(),
        'farmers': CustomUser.objects.filter(role='farmer').count(),
        'buyers': CustomUser.objects.filter(role='buyer').count(),
        'transporters': CustomUser.objects.filter(role='transporter').count(),
        'pending_approvals': CustomUser.objects.filter(is_approved=False, is_superuser=False).count(),
    }
    return render(request, 'ministry/ministry_users.html', {
        'users': users.order_by('-date_joined'),
        'stats': stats,
        'role_filter': role,
        'approval_filter': approval,
        'search': search,
    })


@ministry_required
@require_POST
def toggle_user_active(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    user.is_active = not user.is_active
    user.save()
    return JsonResponse({'status': 'ok', 'is_active': user.is_active})


@ministry_required
@require_POST
def verify_user(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    user.is_verified = not user.is_verified
    user.save()
    return JsonResponse({'status': 'ok', 'is_verified': user.is_verified})


@ministry_required
@require_POST
def approve_user(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    user.is_approved = not user.is_approved
    # Approving also activates the account; revoking deactivates it
    user.is_active = user.is_approved
    user.save()
    return JsonResponse({'status': 'ok', 'is_approved': user.is_approved})


# ─── Orders ───────────────────────────────────────────────────────────────────

@ministry_required
def ministry_orders(request):
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')
    orders = Order.objects.select_related('buyer', 'farmer').prefetch_related('items')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search:
        orders = orders.filter(
            Q(buyer__username__icontains=search) |
            Q(farmer__username__icontains=search) |
            Q(id__icontains=search)
        )
    stats = {
        'total': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'in_transit': Order.objects.filter(status='in_transit').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
        'revenue': Order.objects.filter(status='delivered').aggregate(
                       t=Sum('total_amount'))['t'] or 0,
    }
    return render(request, 'ministry/ministry_orders.html', {
        'orders': orders.order_by('-created_at'),
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
    })


@ministry_required
@require_POST
def update_order_status_ministry(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    valid = [s[0] for s in Order.STATUS_CHOICES]
    if new_status in valid:
        order.status = new_status
        order.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


# ─── Categories ───────────────────────────────────────────────────────────────

@ministry_required
def ministry_categories(request):
    categories = ProductCategory.objects.annotate(
        product_count=Count('product')
    ).order_by('name')
    return render(request, 'ministry/ministry_categories.html', {
        'categories': categories,
        'total': categories.count(),
    })


@ministry_required
@require_POST
def add_category(request):
    data = json.loads(request.body)
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    if not name:
        return JsonResponse({'status': 'error', 'msg': 'Name required'}, status=400)
    cat, created = ProductCategory.objects.get_or_create(name=name, defaults={'description': description})
    return JsonResponse({'status': 'ok', 'id': cat.id, 'name': cat.name, 'created': created})


@ministry_required
@require_POST
def edit_category(request, cat_id):
    cat = get_object_or_404(ProductCategory, pk=cat_id)
    data = json.loads(request.body)
    cat.name = data.get('name', cat.name).strip()
    cat.description = data.get('description', cat.description).strip()
    cat.save()
    return JsonResponse({'status': 'ok'})


@ministry_required
@require_POST
def delete_category(request, cat_id):
    cat = get_object_or_404(ProductCategory, pk=cat_id)
    cat.delete()
    return JsonResponse({'status': 'ok'})


# ─── Prices ───────────────────────────────────────────────────────────────────

@ministry_required
def ministry_prices(request):
    prices = OfficialPrice.objects.select_related('category').order_by('-valid_from')
    categories = ProductCategory.objects.all()
    today = timezone.now().date()
    active_count = prices.filter(valid_from__lte=today, valid_to__gte=today).count()
    return render(request, 'ministry/ministry_prices.html', {
        'prices': prices,
        'categories': categories,
        'active_count': active_count,
        'total': prices.count(),
        'today': today,
    })


@ministry_required
@require_POST
def add_price(request):
    data = json.loads(request.body)
    cat = get_object_or_404(ProductCategory, pk=data.get('category_id'))
    price = OfficialPrice.objects.create(
        category=cat,
        price_per_kg=data['price_per_kg'],
        valid_from=data['valid_from'],
        valid_to=data['valid_to'],
    )
    return JsonResponse({'status': 'ok', 'id': price.id})


@ministry_required
@require_POST
def edit_price(request, price_id):
    price = get_object_or_404(OfficialPrice, pk=price_id)
    data = json.loads(request.body)
    price.price_per_kg = data.get('price_per_kg', price.price_per_kg)
    price.valid_from = data.get('valid_from', price.valid_from)
    price.valid_to = data.get('valid_to', price.valid_to)
    price.save()
    return JsonResponse({'status': 'ok'})


@ministry_required
@require_POST
def delete_price(request, price_id):
    price = get_object_or_404(OfficialPrice, pk=price_id)
    price.delete()
    return JsonResponse({'status': 'ok'})


# ─── Complaints ───────────────────────────────────────────────────────────────

@ministry_required
def ministry_complaints(request):
    status_filter = request.GET.get('status', '')
    complaints = Complaint.objects.select_related('from_user')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    stats = {
        'total': Complaint.objects.count(),
        'open': Complaint.objects.filter(status='open').count(),
        'in_review': Complaint.objects.filter(status='in_review').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
    }
    return render(request, 'ministry/ministry_complaints.html', {
        'complaints': complaints.order_by('-created_at'),
        'stats': stats,
        'status_filter': status_filter,
    })


@ministry_required
@require_POST
def update_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    data = json.loads(request.body)
    complaint.status = data.get('status', complaint.status)
    complaint.resolution_note = data.get('resolution_note', complaint.resolution_note)
    complaint.save()
    return JsonResponse({'status': 'ok'})


# ─── Policies ─────────────────────────────────────────────────────────────────

@ministry_required
def ministry_policies(request):
    policies = Policy.objects.all().order_by('-created_at')
    stats = {
        'total': policies.count(),
        'active': policies.filter(status='active').count(),
        'draft': policies.filter(status='draft').count(),
    }
    return render(request, 'ministry/ministry_policies.html', {
        'policies': policies,
        'stats': stats,
    })


@ministry_required
@require_POST
def add_policy(request):
    data = json.loads(request.body)
    p = Policy.objects.create(
        title=data['title'],
        content=data['content'],
        status=data.get('status', 'draft'),
    )
    return JsonResponse({'status': 'ok', 'id': p.id})


@ministry_required
@require_POST
def edit_policy(request, policy_id):
    p = get_object_or_404(Policy, pk=policy_id)
    data = json.loads(request.body)
    p.title = data.get('title', p.title)
    p.content = data.get('content', p.content)
    p.status = data.get('status', p.status)
    p.save()
    return JsonResponse({'status': 'ok'})


@ministry_required
@require_POST
def delete_policy(request, policy_id):
    p = get_object_or_404(Policy, pk=policy_id)
    p.delete()
    return JsonResponse({'status': 'ok'})


# ─── Reports ─────────────────────────────────────────────────────────────────

@ministry_required
def ministry_reports(request):
    from django.db.models.functions import TruncMonth
    monthly = (Order.objects
               .annotate(month=TruncMonth('created_at'))
               .values('month')
               .annotate(count=Count('id'), revenue=Sum('total_amount'))
               .order_by('month'))

    top_farmers = (CustomUser.objects.filter(role='farmer')
                   .annotate(order_count=Count('sold_orders'),
                             revenue=Sum('sold_orders__total_amount'))
                   .order_by('-revenue')[:10])

    top_products = (Product.objects
                    .annotate(order_count=Count('orderitem'))
                    .order_by('-order_count')[:10])

    context = {
        'monthly': monthly,
        'top_farmers': top_farmers,
        'top_products': top_products,
        'total_revenue': Order.objects.filter(status='delivered').aggregate(
                             t=Sum('total_amount'))['t'] or 0,
        'total_orders': Order.objects.count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
    }
    return render(request, 'ministry/ministry_reports.html', context)


# ─── Profile ─────────────────────────────────────────────────────────────────

@ministry_required
def ministry_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        return redirect('ministry_profile')
    return render(request, 'ministry/ministry_profile.html', {'user': request.user})


# ─── Seasonal Price Ranges ────────────────────────────────────────────────────

@ministry_required
def ministry_price_ranges(request):
    season_filter = request.GET.get('season', '')
    search = request.GET.get('q', '')

    ranges = SeasonalPriceRange.objects.select_related('product_type')
    if season_filter:
        ranges = ranges.filter(season=season_filter)
    if search:
        ranges = ranges.filter(product_type__name__icontains=search)

    product_types = ProductType.objects.all().order_by('name')
    current = current_season()

    stats = {
        'total':  SeasonalPriceRange.objects.count(),
        'spring': SeasonalPriceRange.objects.filter(season='spring').count(),
        'summer': SeasonalPriceRange.objects.filter(season='summer').count(),
        'autumn': SeasonalPriceRange.objects.filter(season='autumn').count(),
        'winter': SeasonalPriceRange.objects.filter(season='winter').count(),
    }

    return render(request, 'ministry/ministry_price_ranges.html', {
        'ranges': ranges.order_by('product_type__name', 'season'),
        'product_types': product_types,
        'season_choices': SEASON_CHOICES,
        'season_filter': season_filter,
        'search': search,
        'stats': stats,
        'current_season': current,
    })


@ministry_required
@require_POST
def add_price_range(request):
    data = json.loads(request.body)
    pt = get_object_or_404(ProductType, pk=data.get('product_type_id'))
    season = data.get('season')
    min_p = float(data.get('min_price', 0))
    max_p = float(data.get('max_price', 0))

    if min_p <= 0 or max_p <= 0:
        return JsonResponse({'status': 'error', 'msg': 'Prices must be positive'}, status=400)
    if min_p >= max_p:
        return JsonResponse({'status': 'error', 'msg': 'Min must be less than Max'}, status=400)

    obj, created = SeasonalPriceRange.objects.update_or_create(
        product_type=pt, season=season,
        defaults={'min_price': min_p, 'max_price': max_p},
    )
    return JsonResponse({
        'status': 'ok',
        'id': obj.id,
        'created': created,
        'product': pt.name,
        'season': obj.get_season_display(),
    })


@ministry_required
@require_POST
def edit_price_range(request, range_id):
    obj = get_object_or_404(SeasonalPriceRange, pk=range_id)
    data = json.loads(request.body)
    min_p = float(data.get('min_price', obj.min_price))
    max_p = float(data.get('max_price', obj.max_price))

    if min_p >= max_p:
        return JsonResponse({'status': 'error', 'msg': 'Min must be less than Max'}, status=400)

    obj.min_price = min_p
    obj.max_price = max_p
    obj.save()
    return JsonResponse({'status': 'ok'})


@ministry_required
@require_POST
def delete_price_range(request, range_id):
    obj = get_object_or_404(SeasonalPriceRange, pk=range_id)
    obj.delete()
    return JsonResponse({'status': 'ok'})


# ─────────────────── PRODUCT CATALOGUE (ProductType) ────────────────────

@ministry_required
def ministry_catalogue(request):
    search = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('category', '')
    pts = ProductType.objects.all()
    if search:
        pts = pts.filter(Q(name__icontains=search) | Q(name_ar__icontains=search))
    if cat_filter:
        pts = pts.filter(category=cat_filter)
    pts = pts.order_by('category', 'name')
    return render(request, 'ministry/ministry_catalogue.html', {
        'active_page': 'catalogue',
        'product_types': pts,
        'total': pts.count(),
        'category_choices': ProductType._meta.get_field('category').choices,
        'current_category': cat_filter,
        'search': search,
    })


@ministry_required
def add_product_type(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=403)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'msg': 'Invalid JSON'}, status=400)
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'status': 'error', 'msg': 'Name is required'}, status=400)
    if ProductType.objects.filter(name=name).exists():
        return JsonResponse({'status': 'error', 'msg': 'A product with this name already exists'}, status=400)
    pt = ProductType.objects.create(
        name=name,
        name_ar=data.get('name_ar', '').strip(),
        category=data.get('category', 'vegetables'),
        image_url=data.get('image_url', '').strip(),
    )
    return JsonResponse({'status': 'ok', 'id': pt.id})


@ministry_required
def edit_product_type(request, pt_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=403)
    pt = get_object_or_404(ProductType, pk=pt_id)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'msg': 'Invalid JSON'}, status=400)
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'status': 'error', 'msg': 'Name is required'}, status=400)
    if ProductType.objects.filter(name=name).exclude(pk=pt_id).exists():
        return JsonResponse({'status': 'error', 'msg': 'Another product already has this name'}, status=400)
    pt.name      = name
    pt.name_ar   = data.get('name_ar', '').strip()
    pt.category  = data.get('category', pt.category)
    pt.image_url = data.get('image_url', '').strip()
    pt.save()
    return JsonResponse({'status': 'ok'})


@ministry_required
def delete_product_type(request, pt_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=403)
    pt = get_object_or_404(ProductType, pk=pt_id)
    if pt.products.exists():
        return JsonResponse({'status': 'error', 'msg': 'Cannot delete — products use this type. Remove them first.'}, status=400)
    pt.delete()
    return JsonResponse({'status': 'ok'})

