from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Max, OuterRef, Subquery

from orders.models import Order
from accounts.models import CustomUser
from .models import Message


def _get_user_orders(user):
    """Return orders this user participates in."""
    role = getattr(user, 'role', '')
    if role == 'farmer':
        return Order.objects.filter(farmer=user).exclude(status='cancelled')
    elif role == 'buyer':
        return Order.objects.filter(buyer=user).exclude(status='cancelled')
    elif role == 'transporter':
        return Order.objects.filter(delivery__transporter=user).exclude(status='cancelled')
    return Order.objects.none()


def _can_access_order(user, order):
    """Check if user is a participant in this order."""
    role = getattr(user, 'role', '')
    if role == 'farmer'      and order.farmer == user:     return True
    if role == 'buyer'       and order.buyer  == user:     return True
    if role == 'transporter':
        try:
            return order.delivery.transporter == user
        except Exception:
            return False
    return False


@login_required
def chat_list(request):
    """Show all orders the user can chat in."""
    orders = _get_user_orders(request.user).select_related(
        'buyer', 'farmer', 'delivery__transporter'
    ).order_by('-created_at')

    # Annotate with unread count and last message
    order_data = []
    for order in orders:
        msgs = Message.objects.filter(order=order)
        unread = msgs.exclude(sender=request.user).filter(is_read=False).count()
        last_msg = msgs.last()
        order_data.append({
            'order': order,
            'unread': unread,
            'last_msg': last_msg,
        })

    # Determine base template
    role = getattr(request.user, 'role', '')
    base = {'farmer': 'farmer_base.html', 'buyer': 'buyer_base.html',
            'transporter': 'transporter_base.html'}.get(role, 'farmer_base.html')

    return render(request, 'chat/chat_list.html', {
        'active_page': 'messages',
        'order_data':  order_data,
        'base_template': base,
    })


@login_required
def chat_room(request, order_id):
    """Chat room for a specific order."""
    order = get_object_or_404(Order, id=order_id)
    if not _can_access_order(request.user, order):
        return redirect('chat_list')

    # Mark messages as read
    Message.objects.filter(order=order).exclude(sender=request.user).update(is_read=True)

    messages_qs = Message.objects.filter(order=order).select_related('sender')

    # Participants
    participants = [order.buyer, order.farmer]
    try:
        if order.delivery.transporter:
            participants.append(order.delivery.transporter)
    except Exception:
        pass
    participants = [p for p in participants if p and p != request.user]

    role = getattr(request.user, 'role', '')
    base = {'farmer': 'farmer_base.html', 'buyer': 'buyer_base.html',
            'transporter': 'transporter_base.html'}.get(role, 'farmer_base.html')

    return render(request, 'chat/chat_room.html', {
        'active_page':   'messages',
        'order':         order,
        'messages':      messages_qs,
        'participants':  participants,
        'base_template': base,
    })


@login_required
@require_POST
def send_message(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not _can_access_order(request.user, order):
        return JsonResponse({'status': 'error', 'msg': 'Forbidden'}, status=403)

    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'status': 'error', 'msg': 'Empty message'}, status=400)

    msg = Message.objects.create(order=order, sender=request.user, body=body)
    return JsonResponse({
        'status': 'ok',
        'id':   msg.id,
        'body': msg.body,
        'sender': request.user.username,
        'role':   request.user.role,
        'time':   msg.created_at.strftime('%H:%M'),
    })


@login_required
def get_messages(request, order_id):
    """Polling endpoint — return messages since ?since=<id>."""
    order = get_object_or_404(Order, id=order_id)
    if not _can_access_order(request.user, order):
        return JsonResponse({'status': 'error'}, status=403)

    since = int(request.GET.get('since', 0))
    msgs = Message.objects.filter(order=order, id__gt=since).select_related('sender')
    # Mark as read
    msgs.exclude(sender=request.user).update(is_read=True)
    data = [{
        'id':     m.id,
        'body':   m.body,
        'sender': m.sender.username,
        'role':   m.sender.role,
        'mine':   m.sender == request.user,
        'time':   m.created_at.strftime('%H:%M'),
    } for m in msgs]
    return JsonResponse({'status': 'ok', 'messages': data})
