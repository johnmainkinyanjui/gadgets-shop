from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product-details/<slug:slug>/', views.productdetails, name='productdetails'),
    path('add-to-cart/<int:pro_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart', views.cart, name='my-cart'), #for viewing the cart page to see what is there
    path('checkout/', views.checkout, name='checkout'),
    # path('added-to-cart/', views.productadded, name='product-added'),
    path('manage-cart/<int:cp_id>', views.managecart, name='manage-cart'),
    path('empty-cart/', views.emptycart, name='empty-cart'),

    
    path('order-confirmation/', views.orderconfirm, name='order-confirmation'),
    path('order-confirmation/', views.orderfailed, name='Order-fail'),

    path('getconfirmation/', views.mpesa_callback, name='mpesa-callback'),
   
]