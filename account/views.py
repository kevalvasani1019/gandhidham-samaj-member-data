from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from .models import (
    Member,
    RelationshipType,
    BloodGroup,
    MaritalStatus,
    TypeOFBusiness,
    TypeOfPayment
)
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Member, Receipt, TypeOfPayment
import json


from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import (
    Member, RelationshipType, BloodGroup,
    MaritalStatus, TypeOFBusiness, TypeOfPayment
)


from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Member, RelationshipType, BloodGroup, MaritalStatus, TypeOFBusiness

class AddFormCreateView(CreateView):
    model = Member
    template_name = "add-form.html"
    fields = [
        "yuvak_mandal_id",
        "mobile_number",
        "member_name",
        "relationship",
        "type_of_business",
        "business",
        "date_of_birth",
        "blood_group",
        "marital_status",
        "photo",
    ]
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['relationship_types'] = RelationshipType.objects.all()
        context['blood_groups'] = BloodGroup.objects.all()
        context['marital_statuses'] = MaritalStatus.objects.all()
        context['business_types'] = TypeOFBusiness.objects.all()
        return context

    def form_valid(self, form):
        # Combine address fields into single string
        plot = self.request.POST.get('plot_number', '').strip()
        landmark = self.request.POST.get('landmark', '').strip()
        city = self.request.POST.get('city', '').strip()
        state = self.request.POST.get('state', '').strip()
        form.instance.address = ", ".join(filter(None, [plot, landmark, city, state]))

        # Map business_name input to model field
        form.instance.business = self.request.POST.get('business_name', '').strip()

        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)

class MemberListView(ListView):
    model = Member
    template_name = 'members.html'
    context_object_name = 'members'
    paginate_by = 20  # Optional: pagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search_type = self.request.GET.get('search_type')
        search_query = self.request.GET.get('search_query')

        if search_type and search_query:
            if search_type == 'Name':
                queryset = queryset.filter(member_name__icontains=search_query)
            elif search_type == 'Mobile number':
                queryset = queryset.filter(mobile_number__icontains=search_query)
            elif search_type == 'Blood Group':
                queryset = queryset.filter(blood_group__name__icontains=search_query)
            elif search_type == 'Member Id':
                queryset = queryset.filter(yuvak_mandal_id__icontains=search_query)
            elif search_type == 'Business type':
                queryset = queryset.filter(type_of_business__name__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_type'] = self.request.GET.get('search_type', '')
        context['search_query'] = self.request.GET.get('search_query', '')
        return context

from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Member, Receipt, TypeOfPayment
import json

from django.utils import timezone
from django.contrib import messages

from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Member, Receipt, TypeOfPayment


def receipt_view(request):
    member = None
    receipts = []
    payment_types = TypeOfPayment.objects.all()

    if request.method == "POST":
        yuvak_mandal_id = request.POST.get('yuvak_mandal_id')
        try:
            member = Member.objects.get(yuvak_mandal_id=yuvak_mandal_id)
        except Member.DoesNotExist:
            messages.error(request, "Member not found.")
            member = None

        if member:
            fee_type_id = request.POST.get('fee_donation')
            fee_type = TypeOfPayment.objects.get(id=fee_type_id) if fee_type_id else None

            # Auto-generate receipt number if not provided
            receipt_number = request.POST.get('receipt_number')
            if not receipt_number:
                last_receipt = Receipt.objects.order_by('-id').first()
                receipt_number = (last_receipt.receipt_number + 1) if last_receipt else 1

            # Convert to int to avoid ValueError
            try:
                receipt_number = int(receipt_number)
            except ValueError:
                messages.error(request, "Receipt number must be numeric.")
                return render(request, 'reciept.html', {
                    'member': member,
                    'receipts': receipts,
                    'payment_types': payment_types
                })

            # Save the receipt
            Receipt.objects.create(
                receipt_number=receipt_number,
                member=member,
                date=request.POST.get('date') or timezone.now(),
                fee_donation=fee_type,
                purpose=request.POST.get('purpose'),
                amount=request.POST.get('amount') or 0
            )
            messages.success(request, "Receipt saved successfully.")

            receipts = Receipt.objects.filter(member=member).order_by('-date')

    elif request.method == "GET":
        yuvak_mandal_id = request.GET.get('yuvak_mandal_id')
        if yuvak_mandal_id:
            try:
                member = Member.objects.get(yuvak_mandal_id=yuvak_mandal_id)
                receipts = Receipt.objects.filter(member=member).order_by('-date')
            except Member.DoesNotExist:
                member = None

    return render(request, 'reciept.html', {
        'member': member,
        'receipts': receipts,
        'payment_types': payment_types
    })

from django.http import JsonResponse
from .models import Member

def get_members(request):
    # Get search parameters
    ymid = request.GET.get("yuvak_mandal_id", "").strip()
    mobile = request.GET.get("mobile_number", "").strip()
    name = request.GET.get("member_name", "").strip()

    # Start with all members
    members = Member.objects.all()

    # Filter based on available input
    if ymid:
        members = members.filter(yuvak_mandal_id__iexact=ymid)
    elif mobile:
        members = members.filter(mobile_number__iexact=mobile)
    elif name:
        members = members.filter(member_name__icontains=name)

    # Prepare JSON response
    data = [
        {
            "member_name": m.member_name,
            "mobile_number": m.mobile_number,
            "yuvak_mandal_id": m.yuvak_mandal_id
        }
        for m in members
    ]

    return JsonResponse({"members": data})

from django.http import JsonResponse
from django.utils import timezone
from .models import Receipt

from django.utils.dateparse import parse_date
def get_next_receipt_number(request):
    today = timezone.now().date()
    # Determine financial year start
    if today.month >= 4:  # April to December
        fy_start = today.replace(month=4, day=1)
    else:  # Jan-Mar
        fy_start = today.replace(year=today.year - 1, month=4, day=1)

    last_receipt = Receipt.objects.filter(date__gte=fy_start, date__lte=today).order_by('receipt_number').last()
    if last_receipt and last_receipt.receipt_number:
        next_number = last_receipt.receipt_number + 1
    else:
        next_number = 1
    return JsonResponse({"next_receipt_number": next_number})


def get_receipts(request):
    # Get optional filter parameters
    ymid = request.GET.get('yuvak_mandal_id')  # member filter
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Base queryset
    qs = Receipt.objects.all()

    # Filter by member if provided
    if ymid:
        qs = qs.filter(member__yuvak_mandal_id=ymid)

    # Filter by date range if provided
    if from_date:
        qs = qs.filter(date__gte=parse_date(from_date))
    if to_date:
        qs = qs.filter(date__lte=parse_date(to_date))

    # Prepare JSON response
    receipts = [
        {   
            "id": r.pk,
            "receipt_number": r.receipt_number,
            "date": r.date.strftime("%d-%m-%Y"),
            "member_name": r.member.member_name,
            "yuvak_mandal_id": r.member.yuvak_mandal_id,
            "fee_donation": r.fee_donation.name if r.fee_donation else "",
            "amount": str(r.amount),
        }
        for r in qs.order_by('-date')
    ]
    return JsonResponse({"receipts": receipts})

from django.views.generic import TemplateView

class Home(TemplateView):
    template_name = 'home.html'



def edit_member(request, pk):
    """Edit an existing Member"""
    member = get_object_or_404(Member, pk=pk)

    # Load dropdown data
    blood_groups = BloodGroup.objects.all()
    business_types = TypeOFBusiness.objects.all()
    relationship_types = RelationshipType.objects.all()
    marital_statuses = MaritalStatus.objects.all()

    if request.method == "POST":
        member.yuvak_mandal_id = request.POST.get("yuvak_mandal_id")
        member.member_name = request.POST.get("member_name")
        member.mobile_number = request.POST.get("mobile_number")
        member.date_of_birth = request.POST.get("date_of_birth") or None
        member.business = request.POST.get("business")
        member.relationship_id = request.POST.get("relationship") or None
        member.marital_status_id = request.POST.get("marital_status") or None
        member.blood_group_id = request.POST.get("blood_group") or None
        member.type_of_business_id = request.POST.get("business_type") or None

        # Address fields
        plot_number = request.POST.get("plot_number", "")
        landmark = request.POST.get("landmark", "")
        city = request.POST.get("city", "")
        state = request.POST.get("state", "")
        member.address = f"{plot_number}, {landmark}, {city}, {state}"

        # Photo upload
        if "photo" in request.FILES:
            member.photo = request.FILES["photo"]

        member.save()
        messages.success(request, "Member details updated successfully!")
        return redirect("members")  # change to your desired redirect URL name

    # Pre-fill address fields (split for form display)
    address_parts = (member.address or "").split(", ")
    address_context = {
        "plot_number": address_parts[0] if len(address_parts) > 0 else "",
        "landmark": address_parts[1] if len(address_parts) > 1 else "",
        "city": address_parts[2] if len(address_parts) > 2 else "",
        "state": address_parts[3] if len(address_parts) > 3 else "",
    }

    context = {
        "member": member,
        "blood_groups": blood_groups,
        "business_types": business_types,
        "relationship_types": relationship_types,
        "marital_statuses": marital_statuses,
        **address_context,
    }

    return render(request, "edit-form.html", context)


# from twilio.rest import Client
# from django.conf import settings

# def send_sms(to_number, message_body):
#     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#     message = client.messages.create(
#         body=message_body,
#         from_=settings.TWILIO_PHONE_NUMBER,
#         to=to_number
#     )
#     return message.sid

def receipt_detail(request, pk):
    """
    Retrieve and render a specific receipt by primary key.
    """
    receipt = get_object_or_404(Receipt, pk=pk)
    print(":::::::::::::::::::::::::::", receipt)
    # Convert amount to words (optional, using built-in num2words if installed)
    try:
        from num2words import num2words
        amount_in_words = num2words(receipt.amount, to='currency', lang='en_IN').replace("euro", "Rupees").title()
    except ImportError:
        amount_in_words = f"Rupees {receipt.amount} Only" if receipt.amount else ""

    context = {
        "receipt": receipt,
        "amount_in_words": amount_in_words,
    }

    return render(request, "reciept_detail.html", context)
