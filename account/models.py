from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    username = None  # remove default username
    phone = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=150)
    name_code = models.CharField(max_length=20, editable=False)   # not unique now

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    def save(self, *args, **kwargs):
        if not self.name_code:
            prefix = self.full_name[:4].upper()
            year = timezone.now().year
            self.name_code = f"{prefix}{year}"   # always same
        super().save(*args, **kwargs)


class RelationshipType(models.Model):
    """Stores relationship options (e.g., Father, Mother, Son, etc.)"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class BloodGroup(models.Model):
    """Stores blood group options (e.g., A +ve, B +ve)"""
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class MaritalStatus(models.Model):
    """Stores marital status options (e.g., Single, Married)"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
class TypeOFBusiness(models.Model):
    """Stores marital status options (e.g., Single, Married)"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class TypeOfPayment(models.Model):
    """Stores marital status options (e.g., Single, Married)"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    
class Member(models.Model):
    """Stores member details"""
    yuvak_mandal_id = models.CharField(max_length=255)
    member_name = models.CharField(max_length=255)
    mobile_number = models.BigIntegerField(blank=True, null=True)
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.RESTRICT, null=True, blank=True)
    type_of_business = models.ForeignKey(TypeOFBusiness, on_delete=models.RESTRICT, null=True, blank=True)
    # type_of_payment = models.ForeignKey(TypeOFBusiness, on_delete=models.RESTRICT, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True) 
    address = models.TextField()
    business = models.CharField(max_length=1000)
    samaj_id = models.CharField(max_length=255, help_text="samaj or yuvak id")
    relationship = models.ForeignKey(RelationshipType, on_delete=models.RESTRICT, null=True, blank=True)
    marital_status = models.ForeignKey(MaritalStatus, on_delete=models.RESTRICT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to="members/photos/", null=True, blank=True)
    def __str__(self):
        return self.member_name

class UpdatedRecord(models.Model):
    updated_at = models.DateTimeField()
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True)
    updated_data = models.JSONField()


class Receipt(models.Model):

    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True)
    receipt_number = models.IntegerField(null=True, blank=True)
    amount = models.IntegerField(null=True, blank=True)
    fee_donation = models.ForeignKey(TypeOfPayment, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    purpose = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Determine financial year
            today = self.date or timezone.now().date()
            if today.month >= 4:  # April to December
                fy_start = today.replace(month=4, day=1)
            else:  # January to March
                fy_start = today.replace(year=today.year - 1, month=4, day=1)

            # Get last receipt in this financial year
            last_receipt = Receipt.objects.filter(
                date__gte=fy_start,
                date__lte=today
            ).order_by('receipt_number').last()

            if last_receipt and last_receipt.receipt_number:
                self.receipt_number = last_receipt.receipt_number + 1
            else:
                self.receipt_number = 1  # start from 1 for new financial year

        super().save(*args, **kwargs)
