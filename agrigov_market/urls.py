from django.contrib import admin
from django.urls import path, include
from accounts.views import home, register, dashboard, pending_approval, CustomLoginView
from django.contrib.auth.views import LogoutView

from products.views import (
    farmer_dashboard, add_product, delete_product,
    manage_orders, update_order_status,
    sales_tracking, farmer_notifications, farmer_profile,
    my_farm, create_farm, delete_farm,
    buyer_dashboard, buyer_orders, buyer_delivery,
    buyer_invoice, buyer_profile, buyer_cart, buyer_compare,
    cancel_order,
    my_complaints,
    submit_complaint,
)
import chat.views as cv
from orders.views import (
    place_order,
    approve_shipping_price,
    place_order_from_cart,
    transporter_missions, transporter_mission_action,
    set_shipping_price,
    transporter_profile_view, transporter_vehicle_view,
    transporter_areas_view, transporter_messages_view,
    transporter_news_view, transporter_settings_view,
)
from ministry import views as mv
from equipment import views as ev

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Auth ────────────────────────────────────────────────────
    path('accounts/login/',  CustomLoginView.as_view(), name='login'),
path('accounts/logout/', LogoutView.as_view(),      name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', register, name='register'),
    path('pending-approval/', pending_approval, name='pending_approval'),

    # ── Home & Dashboard ─────────────────────────────────────────
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),

    # ── Farmer ──────────────────────────────────────────────────
    path('farmer/dashboard/',       farmer_dashboard,     name='farmer_dashboard'),
    path('farmer/products/add/',    add_product,          name='add_product'),
    path('farmer/products/delete/<int:product_id>/', delete_product, name='delete_product'),
    path('farmer/orders/',          manage_orders,        name='manage_orders'),
    path('farmer/orders/<int:order_id>/status/', update_order_status, name='update_order_status'),
    path('farmer/sales/',           sales_tracking,       name='sales_tracking'),
    path('farmer/notifications/',   farmer_notifications, name='farmer_notifications'),
    path('farmer/profile/',         farmer_profile,       name='farmer_profile'),
    path('farmer/farm/',            my_farm,              name='my_farm'),
    path('farmer/farm/create/',     create_farm,          name='create_farm'),
    path('farmer/farm/<int:farm_id>/delete/', delete_farm,   name='delete_farm'),

    # ── Buyer ───────────────────────────────────────────────────
    path('buyer/dashboard/',        buyer_dashboard,      name='buyer_dashboard'),
    path('buyer/orders/',           buyer_orders,         name='buyer_orders'),
    path('buyer/delivery/',         buyer_delivery,       name='buyer_delivery'),
    path('buyer/invoice/',          buyer_invoice,        name='buyer_invoice'),
    path('buyer/profile/',          buyer_profile,        name='buyer_profile'),
    path('buyer/cart/',             buyer_cart,                name='buyer_cart'),
    path('buyer/cart/checkout/',    place_order_from_cart,     name='place_order_from_cart'),
    path('buyer/compare/',          buyer_compare,        name='buyer_compare'),
    path('buyer/orders/<int:order_id>/cancel/', cancel_order, name='cancel_order'),
    path('place-order/<int:product_id>/', place_order,    name='place_order'),
    path('orders/<int:order_id>/approve-shipping/', approve_shipping_price, name='approve_shipping_price'),

    # ── Transporter ─────────────────────────────────────────────
    path('transporter/dashboard/',  transporter_missions,      name='transporter_dashboard'),
    path('transporter/missions/<int:delivery_id>/action/', transporter_mission_action, name='transporter_mission_action'),
    path('transporter/missions/<int:delivery_id>/set-price/', set_shipping_price, name='set_shipping_price'),
    path('transporter/profile/',    transporter_profile_view,  name='transporter_profile'),
    path('transporter/vehicle/',    transporter_vehicle_view,  name='transporter_vehicle'),
    path('transporter/areas/',      transporter_areas_view,    name='transporter_areas'),
    path('transporter/messages/',   transporter_messages_view, name='transporter_messages'),
    path('transporter/news/',       transporter_news_view,     name='transporter_news'),
    path('transporter/settings/',   transporter_settings_view, name='transporter_settings'),

    # ── Equipment (must be before ministry/ catch-all) ──────────
    path('ministry/equipment/',                              ev.ministry_equipment_list,            name='ministry_equipment'),
    path('ministry/equipment/add/',                          ev.ministry_equipment_add,             name='ministry_equipment_add'),
    path('ministry/equipment/<int:eq_id>/edit/',             ev.ministry_equipment_edit,            name='ministry_equipment_edit'),
    path('ministry/equipment/<int:eq_id>/delete/',           ev.ministry_equipment_delete,          name='ministry_equipment_delete'),
    path('ministry/equipment/requests/',                     ev.ministry_equipment_requests,        name='ministry_equipment_requests'),
    path('ministry/equipment/requests/<int:req_id>/update/', ev.ministry_update_equipment_request,  name='ministry_update_equipment_request'),

    # ── Ministry (Admin) ─────────────────────────────────────────
    path('ministry/',                    mv.ministry_dashboard,   name='ministry_dashboard'),
    path('ministry/users/',              mv.ministry_users,       name='ministry_users'),
    path('ministry/users/<int:user_id>/toggle-active/', mv.toggle_user_active, name='toggle_user_active'),
    path('ministry/users/<int:user_id>/verify/',        mv.verify_user,        name='verify_user'),
    path('ministry/users/<int:user_id>/approve/',       mv.approve_user,       name='approve_user'),
    path('ministry/orders/',             mv.ministry_orders,      name='ministry_orders'),
    path('ministry/orders/<int:order_id>/status/', mv.update_order_status_ministry, name='ministry_order_status'),
    path('ministry/categories/',         mv.ministry_categories,  name='ministry_categories'),
    path('ministry/categories/add/',     mv.add_category,         name='ministry_add_category'),
    path('ministry/categories/<int:cat_id>/edit/', mv.edit_category, name='ministry_edit_category'),
    path('ministry/categories/<int:cat_id>/delete/', mv.delete_category, name='ministry_delete_category'),
    path('ministry/prices/',             mv.ministry_prices,      name='ministry_prices'),
    path('ministry/prices/add/',         mv.add_price,            name='ministry_add_price'),
    path('ministry/prices/<int:price_id>/edit/', mv.edit_price,   name='ministry_edit_price'),
    path('ministry/prices/<int:price_id>/delete/', mv.delete_price, name='ministry_delete_price'),

    # Seasonal price ranges
    path('ministry/price-ranges/',                         mv.ministry_price_ranges, name='ministry_price_ranges'),
    path('ministry/price-ranges/add/',                     mv.add_price_range,       name='ministry_add_price_range'),
    path('ministry/price-ranges/<int:range_id>/edit/',     mv.edit_price_range,      name='ministry_edit_price_range'),
    path('ministry/price-ranges/<int:range_id>/delete/',   mv.delete_price_range,    name='ministry_delete_price_range'),
    path('complaints/',                  my_complaints,        name='my_complaints'),
    path('complaints/submit/',           submit_complaint,     name='submit_complaint'),
    path('ministry/complaints/',         mv.ministry_complaints,  name='ministry_complaints'),
    path('ministry/complaints/<int:complaint_id>/update/', mv.update_complaint, name='ministry_update_complaint'),
    path('ministry/policies/',           mv.ministry_policies,    name='ministry_policies'),
    path('ministry/policies/add/',       mv.add_policy,           name='ministry_add_policy'),
    path('ministry/policies/<int:policy_id>/edit/',   mv.edit_policy,   name='ministry_edit_policy'),
    path('ministry/policies/<int:policy_id>/delete/', mv.delete_policy, name='ministry_delete_policy'),
    path('ministry/reports/',            mv.ministry_reports,     name='ministry_reports'),
    path('ministry/catalogue/',                          mv.ministry_catalogue,      name='ministry_catalogue'),
    # ── Chat ──────────────────────────────────────────────────────────────
    path('chat/',                           cv.chat_list,    name='chat_list'),
    path('chat/order/<int:order_id>/',      cv.chat_room,    name='chat_room'),
    path('chat/order/<int:order_id>/send/', cv.send_message, name='send_message'),
    path('chat/order/<int:order_id>/poll/', cv.get_messages, name='get_messages'),
    # ─────────────────────────────────────────────────────────────────────
    path('ministry/catalogue/add/',                      mv.add_product_type,        name='ministry_add_product_type'),
    path('ministry/catalogue/<int:pt_id>/edit/',         mv.edit_product_type,       name='ministry_edit_product_type'),
    path('ministry/catalogue/<int:pt_id>/delete/',       mv.delete_product_type,     name='ministry_delete_product_type'),
    path('ministry/profile/',            mv.ministry_profile,     name='ministry_profile'),

    # ── Equipment (farmer) ──────────────────────────────────────
    path('farmer/equipment/',                           ev.farmer_equipment_list,             name='farmer_equipment'),
    path('farmer/equipment/<int:equipment_id>/request/', ev.farmer_request_equipment,          name='farmer_request_equipment'),
    path('farmer/equipment/requests/<int:req_id>/cancel/', ev.farmer_cancel_equipment_request, name='farmer_cancel_equipment_request'),
]