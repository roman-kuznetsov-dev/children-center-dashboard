from django.contrib import admin
from .models import SaleOrder, SaleItem, CashReceipt


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ('category', 'name', 'quantity', 'price', 'total')
    readonly_fields = ('total',)


@admin.register(SaleOrder)
class SaleOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'club', 'manager', 'date', 'total_amount', 'payment_type', 'guests_count')
    list_filter = ('club', 'payment_type', 'date')
    search_fields = ('club__name', 'manager__username')
    inlines = [SaleItemInline]
    date_hierarchy = 'date'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'admin' or request.user.is_superuser:
            return qs
        if request.user.role in ['manager', 'staff']:
            return qs.filter(club=request.user.club)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and request.user.role != 'admin':
            obj.club = request.user.club
        super().save_model(request, obj, form, change)


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'category', 'name', 'quantity', 'price', 'total')
    list_filter = ('category',)
    search_fields = ('name', 'order__club__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'admin' or request.user.is_superuser:
            return qs
        if request.user.role in ['manager', 'staff']:
            return qs.filter(order__club=request.user.club)
        return qs.none()


@admin.register(CashReceipt)
class CashReceiptAdmin(admin.ModelAdmin):
    """Раздел «Чеки ОФД» в админке"""
    list_display = ('receipt_id', 'club', 'total_amount', 'payment_type', 'guests_count', 'status', 'created_at')
    list_filter = ('status', 'club', 'payment_type', 'created_at')
    search_fields = ('receipt_id',)
    readonly_fields = ('receipt_id', 'club', 'total_amount', 'payment_type', 'guests_count', 'raw_data', 'created_at', 'processed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация о чеке', {
            'fields': ('receipt_id', 'club', 'total_amount', 'payment_type', 'guests_count')
        }),
        ('Статус', {
            'fields': ('status', 'created_at', 'processed_at')
        }),
        ('Сырые данные от ОФД', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'admin' or request.user.is_superuser:
            return qs
        if request.user.role in ['manager', 'staff']:
            return qs.filter(club=request.user.club)
        return qs.none()