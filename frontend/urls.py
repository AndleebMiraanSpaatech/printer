from django.urls import path
from . import views

app_name = "frontend"

urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('', views.home, name='home'),

    # ----------------- Master Data URLs -----------------
    path('master-data/printer-unit/', views.printer_unit_list, name='printer_unit_list'),
    path('master-data/printer-unit/add/', views.printer_unit_add, name='printer_unit_add'),
    path('master-data/printer-unit/edit/', views.printer_unit_edit, name='printer_unit_edit'),
    
    path('master-data/customer/', views.customer_list, name='customer_list'),
    path('master-data/customer/add/', views.customer_add, name='customer_add'),
    path('master-data/customer/edit/', views.customer_edit, name='customer_edit'),
    
    path('master-data/<str:kebab_case_model>/', views.master_data_list, name='master_data_list'), 
    path('master-data/<str:kebab_case_model>/add/', views.master_data_add, name='master_data_add'), 
    path('master-data/<str:kebab_case_model>/edit/', views.master_data_edit, name='master_data_edit'),
    
    path('purchase/', views.purchase_list, name='purchase_list'),
    path('purchase/add/', views.purchase_add, name='purchase_add'),
    path('purchase/<int:purchase_id>/items/', views.purchase_item_list, name='purchase_item_list'),
    
    path('rental/', views.rental_list, name='rental_list'),
    path('rental/add/', views.rental_add, name='rental_add'),
    path('rental/<int:rental_id>/', views.rental_item_list, name='rental_item_list'),
    path('rental-challan-pdf/<int:rental_id>/', views.rental_challan_pdf, name='rental_challan_pdf'),
    
    path('rental-return/', views.rental_return_list, name='rental_return_list'),
    path('rental-return/add/', views.rental_return_add, name='rental_return_add'),
    path('rental-return/<int:rental_return_id>/', views.rental_return_item_list, name='rental_return_item_list'),
    # path('rental-return-challan-pdf/<int:rental_return_id>/', views.rental_return_challan_pdf, name='rental_return_challan_pdf'),
    
    path('inventory-in-store/', views.inventory_in_store, name='inventory_in_store'),
    path('inventory-on-rent/', views.inventory_on_rent, name='inventory_on_rent'),
    path('inventory-by-status/', views.inventory_by_status, name='inventory_by_status'),
]
