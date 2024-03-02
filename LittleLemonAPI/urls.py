from django.urls import path, include
from . import views

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('menu-items', views.MenuItemListView.as_view()),
    path('menu-items/category', views.CategoryView.as_view()),
    path('menu-items/<int:pk>', views.MenuItemDetailView.as_view()),
    path('groups/managers/users', views.ManagerListView.as_view()),
    path('groups/managers/users/<int:pk>', views.ManagerRemoveView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewListView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryRemoveView.as_view()),
    path('cart/menu-items',views.CartOperationView.as_view()),
    path('orders', views.OrderOperationView.as_view()),
    path('orders/<int:pk>', views.SingleOrderOperaionView.as_view()),  
]