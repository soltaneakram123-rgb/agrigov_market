from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Product, ProductCategory, ProductType
from farms.models import Farm
from orders.models import Order
from ministry.models import SeasonalPriceRange, current_season, Complaint


def _require_farmer(request):
    if request.user.role != 'farmer':
        return redirect('dashboard')
    return None

def _require_buyer(request):
    if request.user.role != 'buyer':
        return redirect('dashboard')
    return None


# ──────────────────────────── FARMER ────────────────────────────────────

@login_required
def farmer_dashboard(request):
    redir = _require_farmer(request)
    if redir: return redir
    products = Product.objects.filter(farm__farmer=request.user).select_related('category', 'product_type')
    return render(request, 'farmer_dashboard.html', {
        'active_page':        'products',
        'products':           products,
        'total_products':     products.count(),
        'available_products': products.filter(is_available=True, quantity_kg__gt=50).count(),
        'low_stock':          products.filter(is_available=True, quantity_kg__lte=50, quantity_kg__gt=0).count(),
        'out_of_stock':       products.filter(is_available=False).count(),
        'user': request.user,
    })


@login_required
def add_product(request):
    """Farmer picks from predefined ProductType list — price enforced by seasonal range."""
    redir = _require_farmer(request)
    if redir: return redir

    if request.method == 'POST':
        product_type_id = request.POST.get('product_type')
        try:
            pt = ProductType.objects.get(id=product_type_id)
        except ProductType.DoesNotExist:
            messages.error(request, "Please select a valid product from the list.")
            return redirect('add_product')

        price_per_kg = float(request.POST.get('price_per_kg', 0))

        # ── Seasonal price range enforcement ──────────────────────────────────
        season = current_season()
        try:
            price_range = SeasonalPriceRange.objects.get(product_type=pt, season=season)
            if price_per_kg < float(price_range.min_price):
                messages.error(
                    request,
                    f"❌ Price too low! The minimum allowed price for {pt.name} "
                    f"in {price_range.get_season_display()} is "
                    f"{price_range.min_price} DA/kg. You entered {price_per_kg} DA/kg."
                )
                return redirect('add_product')
            if price_per_kg > float(price_range.max_price):
                messages.error(
                    request,
                    f"❌ Price too high! The maximum allowed price for {pt.name} "
                    f"in {price_range.get_season_display()} is "
                    f"{price_range.max_price} DA/kg. You entered {price_per_kg} DA/kg."
                )
                return redirect('add_product')
        except SeasonalPriceRange.DoesNotExist:
            pass  # No range set for this product/season — allow any price
        # ─────────────────────────────────────────────────────────────────────

        farm_id = request.POST.get('farm_id')
        farm = None
        if farm_id:
            farm = Farm.objects.filter(id=farm_id, farmer=request.user).first()
        if not farm:
            farm = Farm.objects.filter(farmer=request.user).first()
        if not farm:
            messages.error(request, "❌ Please register a farm first.")
            return redirect('create_farm')
        cat, _ = ProductCategory.objects.get_or_create(
            name=pt.category, defaults={'description': ''}
        )
        Product.objects.create(
            farm=farm,
            category=cat,
            product_type=pt,
            name=pt.name,
            quantity_kg=request.POST.get('quantity_kg', 0),
            price_per_kg=price_per_kg,
            quality=request.POST.get('quality', 'B'),
            is_available=True
        )
        messages.success(request, f"✅ {pt.name} added to your products!")
        return redirect('farmer_dashboard')

    product_types = ProductType.objects.all().order_by('category', 'name')
    categories_map = {}
    for pt in product_types:
        categories_map.setdefault(pt.get_category_display(), []).append(pt)

    # Attach current season range to each product type for JS display
    season = current_season()
    ranges_map = {}
    for r in SeasonalPriceRange.objects.filter(season=season).select_related('product_type'):
        ranges_map[r.product_type_id] = {
            'min': float(r.min_price),
            'max': float(r.max_price),
            'season': r.get_season_display(),
        }

    farms = Farm.objects.filter(farmer=request.user).order_by('created_at')
    return render(request, 'add_product.html', {
        'product_types':  product_types,
        'categories_map': categories_map,
        'ranges_map_json': ranges_map,
        'current_season': season,
        'active_page':    'products',
        'farms':          farms,
    })


@login_required
def delete_product(request, product_id):
    redir = _require_farmer(request)
    if redir: return redir
    product = get_object_or_404(Product, id=product_id, farm__farmer=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "🗑 Product deleted.")
    return redirect('farmer_dashboard')


@login_required
def manage_orders(request):
    redir = _require_farmer(request)
    if redir: return redir
    orders = Order.objects.filter(farmer=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'manage_orders.html', {
        'active_page':      'orders',
        'orders':           orders,
        'pending_count':    orders.filter(status='pending').count(),
        'confirmed_count':  orders.filter(status='confirmed').count(),
        'cancelled_count':  orders.filter(status='cancelled').count(),
        'user': request.user,
    })


@login_required
def update_order_status(request, order_id):
    redir = _require_farmer(request)
    if redir: return redir
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, farmer=request.user)
        new_status = request.POST.get('status')
        if new_status in ['confirmed', 'cancelled']:
            order.status = new_status
            order.save()

            # When farmer confirms → open delivery to transporters
            if new_status == 'confirmed':
                try:
                    delivery = order.delivery
                    delivery.status = 'pending'
                    delivery.save()
                except Exception:
                    pass

            # When farmer cancels → restore product stock
            if new_status == 'cancelled':
                for item in order.items.select_related('product').all():
                    item.product.quantity_kg += item.quantity_kg
                    item.product.is_available = True
                    item.product.save()
                try:
                    order.delivery.delete()
                except Exception:
                    pass

            messages.success(request, f"Order #{order.id} updated to {new_status}.")
    return redirect('manage_orders')


@login_required
def sales_tracking(request):
    redir = _require_farmer(request)
    if redir: return redir
    orders = Order.objects.filter(farmer=request.user).prefetch_related('items__product').order_by('-created_at')
    total_revenue = sum(o.total_amount for o in orders if o.status not in ['cancelled'])
    return render(request, 'sales_tracking.html', {
        'active_page':      'sales',
        'orders':           orders,
        'total_revenue':    total_revenue,
        'total_orders':     orders.count(),
        'pending_orders':   orders.filter(status='pending').count(),
        'delivered_orders': orders.filter(status='delivered').count(),
        'user': request.user,
    })


@login_required
def farmer_notifications(request):
    redir = _require_farmer(request)
    if redir: return redir
    orders = Order.objects.filter(farmer=request.user).order_by('-created_at')
    return render(request, 'farmer_notifications.html', {
        'active_page':      'notifications',
        'recent_orders':    orders[:20],
        'pending_orders':   orders.filter(status='pending').count(),
        'confirmed_orders': orders.filter(status='confirmed').count(),
        'transit_orders':   orders.filter(status='in_transit').count(),
        'delivered_orders': orders.filter(status='delivered').count(),
        'user': request.user,
    })


@login_required
def farmer_profile(request):
    redir = _require_farmer(request)
    if redir: return redir
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name  = request.POST.get('last_name',  request.user.last_name)
        request.user.email      = request.POST.get('email',      request.user.email)
        request.user.phone      = request.POST.get('phone',      request.user.phone)
        request.user.save()
        messages.success(request, "✅ Profile updated!")
        return redirect('farmer_profile')
    farm = Farm.objects.filter(farmer=request.user).first()
    return render(request, 'farmer_profile.html', {
        'active_page':    'profile',
        'user':           request.user,
        'farm':           farm,
        'total_products': Product.objects.filter(farm__farmer=request.user).count(),
        'total_orders':   Order.objects.filter(farmer=request.user).count(),
    })


@login_required
def my_farm(request):
    redir = _require_farmer(request)
    if redir: return redir
    farms  = Farm.objects.filter(farmer=request.user).order_by('created_at')
    orders = Order.objects.filter(farmer=request.user)
    return render(request, 'my_farm.html', {
        'active_page':    'farm',
        'farms':          farms,
        'farm':           farms.first(),
        'user':           request.user,
        'total_products': Product.objects.filter(farm__farmer=request.user).count(),
        'total_orders':   orders.count(),
        'total_revenue':  sum(o.total_amount for o in orders if o.status not in ['cancelled']),
    })


@login_required
def create_farm(request):
    redir = _require_farmer(request)
    if redir: return redir
    if request.method == 'POST':
        name           = request.POST.get('name', '').strip()
        location       = request.POST.get('location', '').strip()
        size_hectares  = request.POST.get('size_hectares', '').strip() or None
        if name and location:
            Farm.objects.create(
                farmer=request.user,
                name=name,
                location=location,
                size_hectares=size_hectares,
            )
            messages.success(request, "🌾 Farm registered successfully!")
            return redirect('my_farm')
    return render(request, 'create_farm.html', {'active_page': 'farm', 'user': request.user})



@login_required
def delete_farm(request, farm_id):
    redir = _require_farmer(request)
    if redir: return redir
    farm = get_object_or_404(Farm, id=farm_id, farmer=request.user)
    if request.method == 'POST':
        farm.delete()
        messages.success(request, "🗑️ Farm deleted successfully.")
    return redirect('my_farm')


# ──────────────────────────── BUYER ─────────────────────────────────────

@login_required
def buyer_dashboard(request):
    redir = _require_buyer(request)
    if redir: return redir
    products   = Product.objects.filter(is_available=True).select_related('farm', 'category', 'product_type')
    my_orders  = Order.objects.filter(buyer=request.user)
    categories = ProductCategory.objects.all()
    return render(request, 'buyer_dashboard.html', {
        'active_page':     'browse',
        'products':        products,
        'categories':      categories,
        'my_orders_count': my_orders.count(),
        'pending_count':   my_orders.filter(status='pending').count(),
        'delivered_count': my_orders.filter(status='delivered').count(),
        'user': request.user,
    })


@login_required
def buyer_orders(request):
    redir = _require_buyer(request)
    if redir: return redir
    orders      = Order.objects.filter(buyer=request.user).prefetch_related(
        'items__product', 'delivery__offers'
    ).order_by('-created_at')
    total_spent = sum(o.total_amount for o in orders if o.status not in ['cancelled'])

    # Annotate each order with the best (lowest) pending offer for the buyer to see
    for o in orders:
        try:
            o.best_offer = o.delivery.offers.filter(status='pending').order_by('proposed_price').first()
        except Exception:
            o.best_offer = None

    return render(request, 'buyer_orders.html', {
        'active_page':    'orders',
        'orders':         orders,
        'transit_count':  orders.filter(status='in_transit').count(),
        'delivered_count': orders.filter(status='delivered').count(),
        'pending_count':  orders.filter(status='pending').count(),
        'total_spent':    total_spent,
        'user': request.user,
    })


@login_required
def buyer_delivery(request):
    redir = _require_buyer(request)
    if redir: return redir
    orders = Order.objects.filter(buyer=request.user).prefetch_related('items__product').order_by('-created_at')
    trackable = orders.filter(status__in=['in_transit', 'confirmed'])

    order_id = request.GET.get('order_id')
    if order_id:
        active = trackable.filter(id=order_id).first() or trackable.first()
    else:
        active = trackable.first()

    return render(request, 'buyer_delivery.html', {
        'active_page':  'delivery',
        'orders':       orders,
        'trackable':    trackable,
        'active_order': active,
        'user':         request.user,
    })


@login_required
def buyer_invoice(request):
    redir = _require_buyer(request)
    if redir: return redir
    orders = Order.objects.filter(buyer=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'buyer_invoice.html', {
        'active_page':    'invoice',
        'orders':         orders,
        'delivered_count': orders.filter(status='delivered').count(),
        'pending_count':  orders.filter(status__in=['pending', 'confirmed', 'in_transit']).count(),
        'cancelled_count': orders.filter(status='cancelled').count(),
        'user': request.user,
    })


@login_required
def download_invoice(request, order_id):
    redir = _require_buyer(request)
    if redir: return redir

    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    items = order.items.select_related('product').all()

    # ── Build PDF in memory ──────────────────────────────────────────
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    green  = colors.HexColor('#1e4620')
    lgreen = colors.HexColor('#e8f5e9')
    gray   = colors.HexColor('#777777')

    title_style  = ParagraphStyle('title',  fontSize=22, textColor=green,  fontName='Helvetica-Bold', spaceAfter=2)
    sub_style    = ParagraphStyle('sub',    fontSize=10, textColor=gray,   fontName='Helvetica')
    label_style  = ParagraphStyle('label',  fontSize=9,  textColor=gray,   fontName='Helvetica')
    value_style  = ParagraphStyle('value',  fontSize=10, textColor=colors.black, fontName='Helvetica-Bold')
    section_style= ParagraphStyle('sect',   fontSize=11, textColor=green,  fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    total_style  = ParagraphStyle('total',  fontSize=14, textColor=green,  fontName='Helvetica-Bold', alignment=TA_RIGHT)

    subtotal       = float(order.total_amount)
    shipping_price = float(order.shipping_price) if order.shipping_price else 0
    grand_total    = subtotal + shipping_price

    story = []

    # ── Header ──
    story.append(Paragraph("AgriGov Market", title_style))
    story.append(Paragraph("Agricultural Marketplace Platform — Algeria", sub_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=green))
    story.append(Spacer(1, 0.4*cm))

    # ── Invoice meta (two-column) ──
    inv_number = f"INV-{order.id:05d}"
    meta_data = [
        [Paragraph("INVOICE", ParagraphStyle('inv', fontSize=18, textColor=green, fontName='Helvetica-Bold')),
         Paragraph(f"<b>{inv_number}</b>", ParagraphStyle('invr', fontSize=13, fontName='Helvetica-Bold', alignment=TA_RIGHT))],
        [Paragraph(f"Date: {order.created_at.strftime('%d %B %Y')}", label_style),
         Paragraph(f"Status: <b>{'Paid' if order.status == 'delivered' else order.get_status_display()}</b>",
                   ParagraphStyle('sr', fontSize=9, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor('#155724') if order.status == 'delivered' else colors.HexColor('#856404'),
                                  alignment=TA_RIGHT))],
    ]
    meta_tbl = Table(meta_data, colWidths=['60%', '40%'])
    meta_tbl.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── Bill To / From ──
    parties_data = [
        [Paragraph("BILL TO", label_style), Paragraph("FROM", label_style)],
        [Paragraph(f"<b>{request.user.get_full_name() or request.user.username}</b>", value_style),
         Paragraph(f"<b>{order.farmer.get_full_name() or order.farmer.username}</b>", value_style)],
        [Paragraph(order.shipping_wilaya or '—', sub_style),
         Paragraph(order.farmer.email or '—', sub_style)],
        [Paragraph(order.shipping_address or '—', sub_style), Paragraph('', sub_style)],
        [Paragraph(order.shipping_phone or '—', sub_style), Paragraph('', sub_style)],
    ]
    parties_tbl = Table(parties_data, colWidths=['50%', '50%'])
    parties_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), lgreen),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,0), 8),
        ('TEXTCOLOR',  (0,0), (-1,0), green),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('BOX',  (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('LINEAFTER', (0,0), (0,-1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(parties_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Items Table ──
    story.append(Paragraph("Order Items", section_style))
    item_header = ['#', 'Product', 'Farm', 'Qty (kg)', 'Unit Price', 'Total']
    item_rows   = [item_header]
    for idx, item in enumerate(items, 1):
        unit_p = float(item.product.price_per_kg) if item.product.price_per_kg else 0
        line_t = unit_p * float(item.quantity_kg)
        item_rows.append([
            str(idx),
            item.product.name,
            item.product.farm.name if hasattr(item.product, 'farm') else '—',
            f"{item.quantity_kg} kg",
            f"{unit_p:,.0f} DA",
            f"{line_t:,.0f} DA",
        ])

    items_tbl = Table(item_rows, colWidths=[0.7*cm, 5*cm, 3.5*cm, 2*cm, 2.5*cm, 2.5*cm])
    items_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), green),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('ALIGN',         (3,0), (-1,-1), 'RIGHT'),
        ('ALIGN',         (0,0), (0,-1), 'CENTER'),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, lgreen]),
        ('GRID',          (0,0), (-1,-1), 0.25, colors.HexColor('#dddddd')),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── Totals ──
    totals_data = [
        ['', 'Subtotal',  f"{subtotal:,.0f} DA"],
        ['', 'Shipping',  f"{shipping_price:,.0f} DA"],
        ['', 'TOTAL DUE', f"{grand_total:,.0f} DA"],
    ]
    totals_tbl = Table(totals_data, colWidths=[9.2*cm, 4*cm, 3*cm])
    totals_tbl.setStyle(TableStyle([
        ('ALIGN',         (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME',      (1,2), (-1,2), 'Helvetica-Bold'),
        ('FONTSIZE',      (1,2), (-1,2), 12),
        ('TEXTCOLOR',     (1,2), (-1,2), green),
        ('BACKGROUND',    (1,2), (-1,2), lgreen),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEABOVE',     (1,2), (-1,2), 1, green),
    ]))
    story.append(totals_tbl)
    story.append(Spacer(1, 1*cm))

    # ── Footer ──
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Thank you for using AgriGov Market. This document was generated automatically.",
        ParagraphStyle('footer', fontSize=8, textColor=gray, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)

    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{inv_number}.pdf"'
    return response


@login_required
def buyer_profile(request):
    redir = _require_buyer(request)
    if redir: return redir
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name  = request.POST.get('last_name',  request.user.last_name)
        request.user.email      = request.POST.get('email',      request.user.email)
        request.user.phone      = request.POST.get('phone',      request.user.phone)
        request.user.save()
        messages.success(request, "✅ Profile updated!")
        return redirect('buyer_profile')
    orders      = Order.objects.filter(buyer=request.user).prefetch_related('items__product')
    total_spent = sum(o.total_amount for o in orders if o.status not in ['cancelled'])
    return render(request, 'buyer_profile.html', {
        'active_page':    'profile',
        'user':           request.user,
        'total_orders':   orders.count(),
        'total_spent':    total_spent,
        'delivered_count': orders.filter(status='delivered').count(),
        'recent_orders':  orders.order_by('-created_at')[:4],
    })


@login_required
def buyer_cart(request):
    redir = _require_buyer(request)
    if redir: return redir
    wilayas = [(i+1, w) for i, w in enumerate([
        'Adrar','Chlef','Laghouat','Oum El Bouaghi','Batna','Béjaïa','Biskra','Béchar',
        'Blida','Bouira','Tamanrasset','Tébessa','Tlemcen','Tiaret','Tizi Ouzou','Alger',
        'Djelfa','Jijel','Sétif','Saïda','Skikda','Sidi Bel Abbès','Annaba','Guelma',
        'Constantine','Médéa','Mostaganem','MSila','Mascara','Ouargla','Oran','El Bayadh',
        'Illizi','Bordj Bou Arréridj','Boumerdès','El Tarf','Tindouf','Tissemsilt',
        'El Oued','Khenchela','Souk Ahras','Tipaza','Mila','Aïn Defla','Naâma',
        'Aïn Témouchent','Ghardaïa','Relizane','Timimoun','Bordj Badji Mokhtar',
        'Ouled Djellal','Béni Abbès','In Salah','In Guezzam','Touggourt','Djanet',
        'El MGhair','El Meniaa'
    ])]
    return render(request, 'buyer_cart.html', {'active_page': 'cart', 'user': request.user, 'wilayas': wilayas})


@login_required
def buyer_compare(request):
    redir = _require_buyer(request)
    if redir: return redir
    products   = Product.objects.filter(is_available=True).select_related('farm', 'category', 'product_type').order_by('price_per_kg')
    categories = ProductCategory.objects.all()
    prices     = [float(p.price_per_kg) for p in products]
    avg_price  = sum(prices) / len(prices) if prices else 0
    return render(request, 'buyer_compare.html', {
        'active_page':    'compare',
        'products':       products,
        'categories':     categories,
        'farmers_count':  products.values('farm').distinct().count(),
        'avg_price':      avg_price,
        'cheapest':       products.first(),
        'user': request.user,
    })


@login_required
def cancel_order(request, order_id):
    redir = _require_buyer(request)
    if redir: return redir
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, buyer=request.user, status='pending')
        order.status = 'cancelled'
        order.save()
        # إعادة الكمية للمخزون عند الإلغاء
        for item in order.items.select_related('product').all():
            product = item.product
            product.quantity_kg += item.quantity_kg
            product.is_available = True
            product.save()
        messages.success(request, f"Order #{order.id} cancelled.")
    return redirect('buyer_orders')

# ─────────────────────── COMPLAINTS (Farmer & Buyer) ─────────────────────────

@login_required
def my_complaints(request):
    if request.user.role not in ('farmer', 'buyer'):
        return redirect('dashboard')
    complaints = Complaint.objects.filter(from_user=request.user).order_by('-created_at')
    template = 'farmer_complaints.html' if request.user.role == 'farmer' else 'buyer_complaints.html'
    return render(request, template, {
        'active_page': 'complaints',
        'complaints':  complaints,
        'open_count':  complaints.filter(status='open').count(),
        'resolved_count': complaints.filter(status='resolved').count(),
    })


@login_required
def submit_complaint(request):
    if request.user.role not in ('farmer', 'buyer'):
        return redirect('dashboard')
    if request.method == 'POST':
        subject     = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        if subject and description:
            Complaint.objects.create(
                from_user=request.user,
                subject=subject,
                description=description,
            )
            messages.success(request, '✅ Your complaint has been submitted. We will review it shortly.')
        else:
            messages.error(request, '❌ Please fill in all required fields.')
    return redirect('my_complaints')