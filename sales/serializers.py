from rest_framework import serializers
from .models import SaleOrder, SaleItem

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ['id', 'category', 'name', 'quantity', 'price', 'total']

class SaleOrderSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    club_name = serializers.CharField(source='club.name', read_only=True)
    
    class Meta:
        model = SaleOrder
        fields = ['id', 'club', 'club_name', 'manager', 'manager_name', 'date', 
                  'total_amount', 'payment_type', 'guests_count', 'items']