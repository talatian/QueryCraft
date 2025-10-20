from django.contrib import admin
from .models import Customer, Product, Order


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'registration_date')
    list_display_links = ('id', 'name')
    list_filter = ('registration_date',)
    search_fields = ('name', 'email')
    readonly_fields = ('id',)
    ordering = ('-registration_date', 'name')
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('id', 'name', 'email')
        }),
        ('Registration', {
            'fields': ('registration_date',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price')
    list_display_links = ('id', 'name')
    list_filter = ('category',)
    search_fields = ('name', 'category')
    readonly_fields = ('id',)
    ordering = ('category', 'name')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('id', 'name', 'category', 'price')
        }),
    )


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'order_date', 'quantity', 'status')
    list_display_links = ('id',)
    list_filter = ('status', 'order_date', 'customer__name', 'product__name')
    search_fields = ('customer__name', 'product__name', 'id')
    readonly_fields = ('id',)
    ordering = ('-order_date', 'id')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'customer', 'product')
        }),
        ('Details', {
            'fields': ('order_date', 'quantity', 'status')
        }),
    )
    
    # Customize the form to make it easier to work with
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer":
            kwargs["queryset"] = Customer.objects.order_by('name')
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Register the Order model with the custom admin
admin.site.register(Order, OrderAdmin)


# Custom admin site headers
admin.site.site_header = "QueryCraft Administration"
admin.site.site_title = "QueryCraft Admin"
admin.site.index_title = "Welcome to QueryCraft Administration"