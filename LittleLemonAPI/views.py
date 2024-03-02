from rest_framework.exceptions import MethodNotAllowed
from rest_framework import generics
from .models import Category, MenuItems, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CategorySerializer, UserSerializer, CartSerializer, CartAddSerializer, CartRemoveSerializer, OrderSerializer, SingleOrderSerializer, OrderPutSerializer
from .paginations import MenuItemListPagination
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth.models import User, Group
from .permissions import IsDeliveryCrew, IsManager
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import math
from datetime import date

class MenuItemListView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['title', 'category__title']
    ordering_fields = ['price', 'category']
    pagination_class = MenuItemListPagination
    
    def get_permissions(self):
        permission_classes = []
        
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
class CategoryView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
        
    def get_permissions(self):
        permission_classes = []
            
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemSerializer
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        
        if self.request.method == 'PATCH' or self.request.method=='PUT':
            permission_classes.append(IsManager | IsAdminUser)
        if self.request.method == 'DELETE':
            permission_classes.append(IsAdminUser)
        return [permission() for permission in permission_classes]
    
    def put(self, request, *args, **kwargs):
        menuitem = MenuItems.objects.get(pk=self.kwargs['pk'])
        menuitem.title = self.request.data['title']
        menuitem.price = self.request.data['price']
        menuitem.featured = self.request.data['featured']
        menuitem.category = get_object_or_404(Category, id=self.request.data['category'])
        menuitem.save()
        return JsonResponse(status=200, data={'message': 'All Values has been updated'})
        
        
    def patch(self, request, *args, **kwargs):
        menuitem = MenuItems.objects.get(pk =self.kwargs['pk'])
        menuitem.featured = not menuitem.featured
        menuitem.save()
        return JsonResponse(status=200, data={'message':'Featured status of {} change to {}'.format(str(menuitem.title),str(menuitem.featured))})

class ManagerListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = UserSerializer
    queryset = User.objects.filter(groups__name='Manager')
    
    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username= username)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)
            return JsonResponse(status=201,  data={'message':'User added to Managers group'})

class ManagerRemoveView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = UserSerializer
    queryset = User.objects.filter(groups__name='Manager')
    
    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs['pk']
        user = get_object_or_404(User, pk= user_id)
        managers = Group.objects.get(name='Manager')
        if managers.user_set.filter(id=user.id).exists():
            managers.user_set.remove(user)
            return JsonResponse(status=200,  data={'message':'User Deleted Managers group'})  
        else:
            return JsonResponse(status=404, data={'message': 'Not Found'})  

class DeliveryCrewListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = UserSerializer
    queryset = User.objects.filter(groups__name='Delivery crew')
    
    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            deliverycrew = Group.objects.get(name='Delivery crew')
            deliverycrew.user_set.add(user)
            return JsonResponse(status=201,  data={'message':'User added to Delivery Crew group'})

class DeliveryRemoveView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = UserSerializer
    queryset = User.objects.filter(groups__name='Delivery crew')
    
    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs['pk']
        user = get_object_or_404(User, pk= user_id)
        crew = Group.objects.get(name='Delivery crew')
        if crew.user_set.filter(id=user.id).exists():
            crew.user_set.remove(user)
            return JsonResponse(status=200,  data={'message':'User Deleted Managers group'})  
        else:
            return JsonResponse(status=404, data={'message': 'Not Found'})  

class CartOperationView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle]
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        query = Cart.objects.filter(user=self.request.user)
        return query
        
    def post(self, request, *args, **kwargs):
        serializer = CartAddSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            id = request.data['menuitem']
            quantity = request.data['quantity']
            item = get_object_or_404(MenuItems, id = id)
            price = int(quantity)*item.price
            try:
                Cart.objects.create(user=request.user, menuitem_id=id, quantity=quantity, unitprice=item.price, price=price)
            except:
                return JsonResponse(status=409, data={'message':'Item already in cart'})
            return JsonResponse(status=201, data={'message':'Item added to cart!'})

            
        
    def delete(self, request, *arg, **kwargs):
        if 'menuitem' in request.data:
            serializer_classes = CartRemoveSerializer(data=request.data)
            serializer_classes.is_valid(raise_exception=True)
            item = request.data['menuitem']
            cart = get_object_or_404(Cart, user=self.request.user, menuitem=item)
            cart.delete()
            return JsonResponse(status=200, data={'message':'Item removed from cart'})
        else:
            user = request.user.id
            cart = Cart.objects.filter(user_id=user)
            cart.delete()
            return JsonResponse(status=201, data={'message':'All Items removed from the cart'})
    
            
class OrderOperationView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        
        if self.request.user.groups.filter(name='Manager').exists() or self.request.user.is_superuser == True:
            query = Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery crew').exists():
            query = Order.objects.filter(delivery_crew=self.request.user)
        else:
            query = Order.objects.filter(user=self.request.user)
        return query
    
    def get_permissions(self):
        
        if self.request.method == 'GET' or self.request.method == 'POST':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        x=cart.values_list()
        if len(x) == 0:
            return HttpResponseBadRequest()
        total = math.fsum([float(x[-1]) for x in x])
        order = Order.objects.create(user=request.user, status=False, total=total, date=date.today())
        for i in cart.values():
            menuitem = get_object_or_404(MenuItems, id=i['menuitem_id'])
            orderitem = OrderItem.objects.create(order=order, menuitem=menuitem, quantity=i['quantity'], )
            orderitem.save()
        cart.delete()
        return JsonResponse(status=201, data={'message':'Your order has been placed! Your order number is {}'.format(str(order.id))})


class SingleOrderOperaionView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = SingleOrderSerializer
    
    def get_permissions(self):
        
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        if self.request.method == 'PUT' or self.request.method == 'DELETE':
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsDeliveryCrew | IsManager | IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        query = OrderItem.objects.filter(order_id= self.kwargs['pk'])
        return query
    
    def patch(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()
        return JsonResponse(status=200, data={'message': 'Order status of the order id:{} has changed to {} from {}'.format(str(order.id), str(not order.status), str(order.status) )})
    
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')
    
    def put(self, request, *args, **kwargs):
        serializer_item = OrderPutSerializer(data=request.data)
        serializer_item.is_valid(raise_exception=True)
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        crew_pk = self.request.data['delivery_crew']
        crew = get_object_or_404(User, pk=crew_pk)
        order.delivery_crew = crew
        order.save()
        return JsonResponse(status=200, data={'message':'{} has been assigned as a delivery partner for the order id:{}'.format(str(crew.username), str(order.id))})
    
    def delete(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        order_number = str(order.id)
        order.delete()
        return JsonResponse(status=200, data={'message':'order with order id{} has been deleted'.format(order_number)})
    
    
    
                            
         
    
    
    
    
        
        
        
    
        
            
    
            
            
        
        
        
        
        
    