from django.contrib import admin
from .models import (
    RelationshipType,
    BloodGroup,
    MaritalStatus,
    TypeOFBusiness,
    TypeOfPayment,
    Member,
    UpdatedRecord,
    Receipt
)

# Register simple lookup models
@admin.register(RelationshipType)
class RelationshipTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(MaritalStatus)
class MaritalStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(TypeOFBusiness)
class TypeOFBusinessAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(TypeOfPayment)
class TypeOfPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# Member model
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'yuvak_mandal_id',
        'member_name',
        'mobile_number',
        'blood_group',
        'type_of_business',
        'date_of_birth',
        'marital_status',
        'relationship',
        'created_at'
    )
    list_filter = ('blood_group', 'type_of_business', 'marital_status', 'relationship')
    search_fields = ('member_name', 'yuvak_mandal_id', 'samaj_id', 'mobile_number')
    ordering = ('-created_at',)

# UpdatedRecord model
@admin.register(UpdatedRecord)
class UpdatedRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('member__member_name',)

# Receipt model
@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'receipt_number', 'amount', 'fee_donation')
    list_filter = ('fee_donation',)
    search_fields = ('member__member_name', 'receipt_number')
