from .models import DeliveryOffer, Delivery, Order
from equipment.models import EquipmentRequest


def notifications(request):
    """
    Inject notification counts into every template context automatically.
    """
    if not request.user.is_authenticated:
        return {}

    role = getattr(request.user, 'role', None)

    if role == 'farmer':
        new_orders = Order.objects.filter(
            farmer=request.user, status='pending'
        ).count()
        eq_updates = EquipmentRequest.objects.filter(
            farmer=request.user, status__in=['approved', 'rejected']
        ).count()
        return {
            'new_orders_count': new_orders,
            'equipment_requests_count': eq_updates,
        }

    if role == 'buyer':
        count = Delivery.objects.filter(
            order__buyer=request.user,
            order__shipping_approval='pending',
            offers__status='pending',
        ).distinct().count()
        return {'pending_offers_count': count}

    if role == 'transporter':
        accepted = DeliveryOffer.objects.filter(
            transporter=request.user,
            status='accepted',
            delivery__status='assigned',
        ).count()
        rejected = DeliveryOffer.objects.filter(
            transporter=request.user,
            status='rejected',
        ).count()
        return {
            'accepted_offers_count': accepted,
            'rejected_offers_count': rejected,
        }

    if role == 'ministry':
        pending_eq = EquipmentRequest.objects.filter(status='pending').count()
        return {'pending_equipment_requests': pending_eq}

    return {}
