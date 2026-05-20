from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from accounts.views import register, dashboard
from products.views import farmer_dashboard, buyer_dashboard, add_product
from orders.views import place_order
from ministry.views import ministry_dashboard, transporter_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),  # login, logout, etc.
    path('register/', register, name='register'),
    
    # Main Dashboard (redirects by role)
    path('dashboard/', dashboard, name='dashboard'),
    
    # Role dashboards
    path('farmer/dashboard/', farmer_dashboard, name='farmer_dashboard'),
    path('buyer/dashboard/', buyer_dashboard, name='buyer_dashboard'),
    path('transporter/dashboard/', transporter_dashboard, name='transporter_dashboard'),
    path('ministry/dashboard/', ministry_dashboard, name='ministry_dashboard'),
    
    # Other pages
    path('add-product/', add_product, name='add_product'),
    path('place-order/<int:product_id>/', place_order, name='place_order'),
    
    # Home page redirects to login
    path('', lambda r: redirect('login')),
]