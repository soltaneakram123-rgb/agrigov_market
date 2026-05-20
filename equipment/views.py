from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import Equipment, EquipmentRequest


# ── Farmer views ──────────────────────────────────────────────────────────────

@login_required
def farmer_equipment_list(request):
    """Farmer sees all active equipment and their own requests."""
    if request.user.role != 'farmer':
        return redirect('dashboard')

    equipments = Equipment.objects.filter(is_active=True).prefetch_related('requests')
    my_requests = EquipmentRequest.objects.filter(farmer=request.user).select_related('equipment')

    return render(request, 'farmer_equipment.html', {
        'active_page': 'equipment',
        'equipments':  equipments,
        'my_requests': my_requests,
        'user':        request.user,
    })


@login_required
@require_POST
def farmer_request_equipment(request, equipment_id):
    """Farmer submits a request for a specific equipment."""
    if request.user.role != 'farmer':
        return redirect('dashboard')

    equipment = get_object_or_404(Equipment, id=equipment_id, is_active=True)

    # Check availability
    if equipment.available_count < 1:
        messages.error(request, f"❌ الآلة '{equipment.name}' غير متوفرة حالياً.")
        return redirect('farmer_equipment')

    # Prevent duplicate pending requests
    already = EquipmentRequest.objects.filter(
        farmer=request.user, equipment=equipment, status='pending'
    ).exists()
    if already:
        messages.warning(request, "⚠️ لديك طلب قيد الانتظار لهذه الآلة بالفعل.")
        return redirect('farmer_equipment')

    start_date = request.POST.get('start_date')
    end_date   = request.POST.get('end_date')
    reason     = request.POST.get('reason', '').strip()

    if not start_date or not end_date or not reason:
        messages.error(request, "❌ الرجاء ملء جميع الحقول.")
        return redirect('farmer_equipment')

    if end_date < start_date:
        messages.error(request, "❌ تاريخ النهاية يجب أن يكون بعد تاريخ البداية.")
        return redirect('farmer_equipment')

    EquipmentRequest.objects.create(
        farmer=request.user,
        equipment=equipment,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )
    messages.success(request, f"✅ تم إرسال طلبك للآلة '{equipment.name}'. سيتم الرد عليك قريباً.")
    return redirect('farmer_equipment')


@login_required
@require_POST
def farmer_cancel_equipment_request(request, req_id):
    """Farmer cancels a pending request."""
    if request.user.role != 'farmer':
        return redirect('dashboard')

    eq_req = get_object_or_404(EquipmentRequest, id=req_id, farmer=request.user, status='pending')
    eq_req.delete()
    messages.info(request, "تم إلغاء الطلب.")
    return redirect('farmer_equipment')


# ── Ministry (Admin) views ────────────────────────────────────────────────────

def _is_ministry_user(user):
    """Returns True for users with ministry role or superuser/staff."""
    return user.is_superuser or user.is_staff or user.role == 'ministry'


def _require_ministry(request):
    if not _is_ministry_user(request.user):
        return redirect('dashboard')


@login_required
def ministry_equipment_list(request):
    """Admin manages all equipment."""
    if not _is_ministry_user(request.user):
        return redirect('dashboard')

    equipments = Equipment.objects.prefetch_related('requests').order_by('category', 'name')
    return render(request, 'ministry/ministry_equipment.html', {
        'equipments': equipments,
        'categories': Equipment.CATEGORY_CHOICES,
    })


@login_required
@require_POST
def ministry_equipment_add(request):
    if not _is_ministry_user(request.user):
        return JsonResponse({'status': 'error'}, status=403)
    try:
        data = json.loads(request.body)
        eq = Equipment.objects.create(
            name               = data['name'],
            name_ar            = data.get('name_ar', ''),
            category           = data.get('category', 'other'),
            description        = data.get('description', ''),
            image_url          = data.get('image_url', ''),
            quantity_available = int(data.get('quantity_available', 1)),
            price_per_day      = float(data.get('price_per_day', 0)),
            wilaya             = data.get('wilaya', ''),
            is_active          = data.get('is_active', True),
        )
        return JsonResponse({'status': 'ok', 'id': eq.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=400)


@login_required
@require_POST
def ministry_equipment_edit(request, eq_id):
    if not _is_ministry_user(request.user):
        return JsonResponse({'status': 'error'}, status=403)
    eq = get_object_or_404(Equipment, id=eq_id)
    try:
        data = json.loads(request.body)
        eq.name               = data.get('name', eq.name)
        eq.name_ar            = data.get('name_ar', eq.name_ar)
        eq.category           = data.get('category', eq.category)
        eq.description        = data.get('description', eq.description)
        eq.image_url          = data.get('image_url', eq.image_url)
        eq.quantity_available = int(data.get('quantity_available', eq.quantity_available))
        eq.price_per_day      = float(data.get('price_per_day', eq.price_per_day))
        eq.wilaya             = data.get('wilaya', eq.wilaya)
        eq.is_active          = data.get('is_active', eq.is_active)
        eq.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=400)


@login_required
@require_POST
def ministry_equipment_delete(request, eq_id):
    if not _is_ministry_user(request.user):
        return JsonResponse({'status': 'error'}, status=403)
    eq = get_object_or_404(Equipment, id=eq_id)
    eq.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def ministry_equipment_requests(request):
    """Admin reviews all farmer equipment requests."""
    if not _is_ministry_user(request.user):
        return redirect('dashboard')

    reqs = EquipmentRequest.objects.select_related('farmer', 'equipment').order_by('-created_at')
    pending_count  = reqs.filter(status='pending').count()
    approved_count = reqs.filter(status='approved').count()
    rejected_count = reqs.filter(status='rejected').count()

    return render(request, 'ministry/ministry_equipment_requests.html', {
        'requests':       reqs,
        'pending_count':  pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@login_required
@require_POST
def ministry_update_equipment_request(request, req_id):
    """Admin approves or rejects a request."""
    if not _is_ministry_user(request.user):
        return JsonResponse({'status': 'error'}, status=403)

    eq_req = get_object_or_404(EquipmentRequest, id=req_id)
    try:
        data       = json.loads(request.body)
        # frontend sends 'status'; old code used 'action' — accept both
        action     = data.get('status') or data.get('action')
        admin_note = data.get('admin_note', '')

        if action not in ('approved', 'rejected', 'returned'):
            return JsonResponse({'status': 'error', 'msg': 'Invalid action'}, status=400)

        eq_req.status     = action
        eq_req.admin_note = admin_note
        eq_req.save()
        return JsonResponse({'status': 'ok', 'new_status': action})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=400)