from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
import json

from products.models import Product
from .models import Order, OrderItem, Delivery, DeliveryOffer
from accounts.models import TransporterProfile


# ─────────────────────── BUYER ──────────────────────────────────────────

@login_required
def place_order(request, product_id):
    if request.user.role != 'buyer':
        return redirect('dashboard')

    product = get_object_or_404(Product, id=product_id, is_available=True)

    if request.method == 'POST':
        # ── Validate quantity ──────────────────────────────────────────
        try:
            quantity = Decimal(request.POST.get('quantity_kg', '1'))
            if quantity <= 0 or quantity > product.quantity_kg:
                raise ValueError("Quantity out of range")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
            return redirect('buyer_dashboard')

        # ── Shipping address (required) ────────────────────────────────
        shipping_address = request.POST.get('shipping_address', '').strip()
        shipping_wilaya  = request.POST.get('shipping_wilaya',  '').strip()
        shipping_phone   = request.POST.get('shipping_phone',   '').strip()
        shipping_notes   = request.POST.get('shipping_notes',   '').strip()

        if not shipping_address or not shipping_wilaya or not shipping_phone:
            messages.error(request, "Please fill in all shipping address fields.")
            return redirect('buyer_dashboard')

        # ── Create order ───────────────────────────────────────────────
        order = Order.objects.create(
            buyer=request.user,
            farmer=product.farm.farmer,
            total_amount=product.price_per_kg * quantity,
            shipping_address=shipping_address,
            shipping_wilaya=shipping_wilaya,
            shipping_phone=shipping_phone,
            shipping_notes=shipping_notes,
            status='pending',
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity_kg=quantity,
            price_at_order=product.price_per_kg,
        )

        # ── Deduct stock ───────────────────────────────────────────────
        product.quantity_kg -= quantity
        if product.quantity_kg <= 0:
            product.quantity_kg = 0
            product.is_available = False
        product.save()

        # ── Create Delivery in 'waiting' state (hidden from transporters
        #    until farmer confirms the order) ───────────────────────────
        Delivery.objects.create(
            order=order,
            pickup_location=product.farm.location or product.farm.name,
            delivery_location=f"{shipping_wilaya} — {shipping_address}",
            status='waiting',
            notes=shipping_notes,
        )

        messages.success(
            request,
            f"✅ Order placed for {quantity} kg of {product.name}! "
            f"Waiting for farmer to confirm."
        )
    return redirect('buyer_dashboard')


# ─────────────────────── TRANSPORTER ────────────────────────────────────

@login_required
@require_POST
def approve_shipping_price(request, order_id):
    """Buyer approves or rejects the cheapest transporter offer."""
    if request.user.role != 'buyer':
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    action = request.POST.get('action')

    # Find the cheapest pending offer for this order's delivery
    try:
        delivery = order.delivery
    except Exception:
        messages.error(request, "No delivery found for this order.")
        return redirect('buyer_orders')

    best_offer = delivery.offers.filter(status='pending').order_by('proposed_price').first()

    if not best_offer:
        messages.error(request, "No offer available for approval.")
        return redirect('buyer_orders')

    if action == 'approve':
        # Accept the best offer, reject all others
        best_offer.status = 'accepted'
        best_offer.save()
        delivery.offers.exclude(id=best_offer.id).update(status='rejected')

        # Assign transporter and price on the delivery & order
        delivery.transporter = best_offer.transporter
        delivery.shipping_price = best_offer.proposed_price
        delivery.status = 'assigned'
        delivery.assigned_at = timezone.now()
        delivery.save()

        order.shipping_price = best_offer.proposed_price
        order.shipping_approval = 'approved'
        order.save()

        messages.success(
            request,
            f"✅ Offer of {best_offer.proposed_price} DA accepted! "
            f"Transporter {best_offer.transporter.get_full_name() or best_offer.transporter.username} assigned."
        )

    elif action == 'reject':
        # Reject only this best offer so the next cheapest remains visible
        best_offer.status = 'rejected'
        best_offer.save()
        messages.info(request, f"❌ Offer of {best_offer.proposed_price} DA rejected.")

    return redirect('buyer_orders')


def _get_profile(user):
    try:
        return TransporterProfile.objects.get(user=user)
    except TransporterProfile.DoesNotExist:
        return None


@login_required
def transporter_missions(request):
    if request.user.role != 'transporter':
        return redirect('dashboard')

    my_deliveries = Delivery.objects.filter(
        transporter=request.user
    ).select_related('order', 'order__farmer', 'order__buyer') \
     .prefetch_related('order__items__product').order_by('-id')

    # Open deliveries: farmer confirmed, no transporter assigned yet, and
    # this transporter hasn't had their offer rejected already
    available_qs = Delivery.objects.filter(
        status='pending'
    ).select_related('order', 'order__farmer', 'order__buyer') \
     .prefetch_related('order__items__product', 'offers')

    # Annotate each available delivery with this transporter's offer (if any)
    available = []
    for d in available_qs:
        my_offer = d.offers.filter(transporter=request.user).first()
        d.my_offer = my_offer          # None / offer with status
        available.append(d)

    all_deliveries = available + list(my_deliveries)

    active_mission = my_deliveries.filter(status__in=['assigned', 'in_transit']).first()

    return render(request, 'transporter_dashboard.html', {
        'active_page':        'missions',
        'deliveries':         all_deliveries,
        'total_missions':     len(all_deliveries),
        'pending_count':      len(available),
        'progress_count':     my_deliveries.filter(status__in=['assigned', 'in_transit']).count(),
        'delivered_count':    my_deliveries.filter(status='delivered').count(),
        'user':               request.user,
        'has_active_mission': active_mission is not None,
        'active_mission':     active_mission,
    })


@login_required
@require_POST
def set_shipping_price(request, delivery_id):
    """Transporter submits an offer (price) for a pending delivery."""
    if request.user.role != 'transporter':
        return JsonResponse({'status': 'error'}, status=403)

    delivery = get_object_or_404(Delivery, id=delivery_id, status='pending')

    try:
        data = json.loads(request.body)
        price = Decimal(str(data.get('shipping_price', 0)))
        if price <= 0:
            return JsonResponse({'status': 'error', 'msg': 'Price must be positive'}, status=400)
    except Exception:
        return JsonResponse({'status': 'error', 'msg': 'Invalid price'}, status=400)

    # Create or update this transporter's offer (upsert)
    offer, created = DeliveryOffer.objects.update_or_create(
        delivery=delivery,
        transporter=request.user,
        defaults={'proposed_price': price, 'status': 'pending'},
    )

    # Update the order's displayed shipping price to show the current best offer
    best = delivery.offers.filter(status='pending').order_by('proposed_price').first()
    if best:
        delivery.order.shipping_price = best.proposed_price
        delivery.order.shipping_approval = 'pending'
        delivery.order.save()

    return JsonResponse({'status': 'ok', 'price': float(price), 'offer_id': offer.id})


@login_required
def transporter_mission_action(request, delivery_id):
    if request.user.role != 'transporter' or request.method != 'POST':
        return redirect('dashboard')

    delivery = get_object_or_404(Delivery, id=delivery_id)
    action = request.POST.get('action')

    # 'accept' = submit offer (price must already be set via set_shipping_price)
    if action == 'accept' and delivery.status == 'pending':
        my_offer = delivery.offers.filter(transporter=request.user).first()
        if not my_offer:
            messages.error(request, "❌ Please set a shipping price first before submitting an offer.")
            return redirect('transporter_dashboard')
        messages.success(
            request,
            f"✅ Offer of {my_offer.proposed_price} DA submitted for Mission #MSN-{delivery.id}. "
            f"Waiting for buyer to choose."
        )

    elif action == 'decline':
        if delivery.status == 'pending':
            # Transporter withdraws their offer from an open delivery
            delivery.offers.filter(transporter=request.user).delete()
            messages.info(request, f"تم سحب عرضك من المهمة #MSN-{delivery.id}.")

        elif delivery.status == 'assigned' and delivery.transporter == request.user:
            # Transporter backs out from an already-assigned delivery
            delivery.transporter = None
            delivery.status = 'pending'
            delivery.shipping_price = None
            delivery.order.shipping_price = None
            delivery.order.shipping_approval = 'pending'
            delivery.order.save()
            delivery.save()
            # Reset their accepted offer to pending so mission stays visible
            delivery.offers.filter(transporter=request.user, status='accepted').update(status='pending')
            messages.info(request, f"Mission #MSN-{delivery.id} released.")

    elif action == 'in_transit' and delivery.transporter == request.user \
            and delivery.status == 'assigned':
        delivery.status = 'in_transit'
        delivery.order.status = 'in_transit'
        delivery.order.save()
        delivery.save()
        messages.success(request, "🚚 Status updated to In Transit.")

    elif action == 'delivered' and delivery.transporter == request.user \
            and delivery.status == 'in_transit':
        delivery.status = 'delivered'
        delivery.delivered_at = timezone.now()
        delivery.order.status = 'delivered'
        delivery.order.save()
        delivery.save()
        messages.success(request, "📦 Mission marked as delivered!")

    return redirect('transporter_dashboard')


@login_required
def transporter_profile_view(request):
    if request.user.role != 'transporter':
        return redirect('dashboard')
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name  = request.POST.get('last_name',  request.user.last_name)
        request.user.email      = request.POST.get('email',      request.user.email)
        request.user.phone      = request.POST.get('phone',      request.user.phone)
        request.user.save()
        profile, _ = TransporterProfile.objects.get_or_create(
            user=request.user,
            defaults={'vehicle_type': 'Truck', 'capacity_kg': 1000, 'service_areas': 'Algeria'}
        )
        profile.vehicle_type  = request.POST.get('vehicle_type', profile.vehicle_type)
        profile.capacity_kg   = request.POST.get('capacity_kg', profile.capacity_kg)
        profile.service_areas = request.POST.get('service_areas', profile.service_areas)
        profile.is_available  = request.POST.get('is_available') == 'true'
        profile.save()
        messages.success(request, "✅ Profile updated!")
        return redirect('transporter_profile')
    profile    = _get_profile(request.user)
    deliveries = Delivery.objects.filter(transporter=request.user).prefetch_related('order__items__product')
    return render(request, 'transporter_profile.html', {
        'active_page':     'profile',
        'user':            request.user,
        'profile':         profile,
        'recent_missions': deliveries.order_by('-id')[:5],
        'total_missions':  deliveries.count(),
        'delivered_count': deliveries.filter(status='delivered').count(),
        'progress_count':  deliveries.filter(status__in=['assigned', 'in_transit']).count(),
    })


@login_required
def transporter_vehicle_view(request):
    if request.user.role != 'transporter':
        return redirect('dashboard')
    if request.method == 'POST':
        profile, _ = TransporterProfile.objects.get_or_create(
            user=request.user,
            defaults={'vehicle_type': 'Truck', 'capacity_kg': 1000, 'service_areas': 'Algeria'}
        )
        profile.vehicle_type  = request.POST.get('vehicle_type', profile.vehicle_type)
        profile.capacity_kg   = request.POST.get('capacity_kg', profile.capacity_kg)
        profile.service_areas = request.POST.get('service_areas', profile.service_areas)
        profile.is_available  = request.POST.get('is_available') == 'true'
        profile.save()
        messages.success(request, "✅ Vehicle info updated!")
        return redirect('transporter_vehicle')
    profile    = _get_profile(request.user)
    deliveries = Delivery.objects.filter(transporter=request.user)
    return render(request, 'transporter_vehicle.html', {
        'active_page':     'vehicle',
        'user':            request.user,
        'profile':         profile,
        'total_missions':  deliveries.count(),
        'delivered_count': deliveries.filter(status='delivered').count(),
        'progress_count':  deliveries.filter(status__in=['assigned', 'in_transit']).count(),
    })


@login_required
def transporter_areas_view(request):
    if request.user.role != 'transporter':
        return redirect('dashboard')
    if request.method == 'POST':
        profile, _ = TransporterProfile.objects.get_or_create(
            user=request.user,
            defaults={'vehicle_type': 'Truck', 'capacity_kg': 1000, 'service_areas': 'Algeria'}
        )
        profile.service_areas = request.POST.get('service_areas', profile.service_areas)
        profile.is_available  = request.POST.get('is_available') == 'true'
        profile.save()
        messages.success(request, "✅ Service areas updated!")
        return redirect('transporter_areas')
    profile    = _get_profile(request.user)
    deliveries = Delivery.objects.filter(transporter=request.user)
    return render(request, 'transporter_areas.html', {
        'active_page':    'areas',
        'user':           request.user,
        'profile':        profile,
        'total_missions': deliveries.count(),
    })


@login_required
def transporter_messages_view(request):
    if request.user.role != 'transporter':
        return redirect('dashboard')
    return render(request, 'transporter_messages.html', {'active_page': 'messages', 'user': request.user})


@login_required
def transporter_news_view(request):
    if request.user.role != 'transporter':
        return redirect('dashboard')
    return render(request, 'transporter_news.html', {'active_page': 'news', 'user': request.user})


@login_required
def transporter_settings_view(request):
    if request.user.role != 'transporter':
        return redirect('dashboard')
    return render(request, 'transporter_settings.html', {'active_page': 'settings', 'user': request.user})

@login_required
def place_order_from_cart(request):
    """Place multiple orders from cart (one per farmer)."""
    if request.user.role != 'buyer' or request.method != 'POST':
        return redirect('dashboard')

    shipping_address = request.POST.get('shipping_address', '').strip()
    shipping_wilaya  = request.POST.get('shipping_wilaya', '').strip()
    shipping_phone   = request.POST.get('shipping_phone', '').strip()
    shipping_notes   = request.POST.get('shipping_notes', '').strip()

    if not shipping_address or not shipping_wilaya or not shipping_phone:
        messages.error(request, "❌ Please fill in all shipping fields.")
        return redirect('buyer_cart')

    # Cart items sent as JSON in hidden field
    import json
    try:
        items = json.loads(request.POST.get('cart_items', '[]'))
    except Exception:
        messages.error(request, "❌ Invalid cart data.")
        return redirect('buyer_cart')

    if not items:
        messages.error(request, "❌ Your cart is empty.")
        return redirect('buyer_cart')

    orders_created = 0
    errors = []

    for item in items:
        try:
            product = Product.objects.get(id=item['id'], is_available=True)
            qty = Decimal(str(item.get('qty', 1)))
            if qty <= 0 or qty > product.quantity_kg:
                errors.append(f"{product.name}: quantity not available ({product.quantity_kg} kg left)")
                continue

            order = Order.objects.create(
                buyer=request.user,
                farmer=product.farm.farmer,
                total_amount=product.price_per_kg * qty,
                shipping_address=shipping_address,
                shipping_wilaya=shipping_wilaya,
                shipping_phone=shipping_phone,
                shipping_notes=shipping_notes,
                status='pending',
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity_kg=qty,
                price_at_order=product.price_per_kg,
            )
            product.quantity_kg -= qty
            if product.quantity_kg <= 0:
                product.quantity_kg = 0
                product.is_available = False
            product.save()

            Delivery.objects.create(
                order=order,
                pickup_location=product.farm.location or product.farm.name,
                delivery_location=f"{shipping_wilaya} — {shipping_address}",
                status='waiting',
                notes=shipping_notes,
            )
            orders_created += 1

        except Product.DoesNotExist:
            errors.append(f"Product ID {item.get('id')} not found or no longer available.")
        except Exception as e:
            errors.append(str(e))

    if orders_created:
        messages.success(request, f"✅ {orders_created} order(s) placed successfully! Waiting for farmers to confirm.")
    for err in errors:
        messages.error(request, f"⚠️ {err}")

    return redirect('buyer_orders')