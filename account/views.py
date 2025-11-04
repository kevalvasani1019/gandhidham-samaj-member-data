from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, ListView, TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


from .models import (
    Member, RelationshipType, BloodGroup, MaritalStatus,
    TypeOFBusiness, TypeOfPayment, Receipt
)

from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True


# -------------------------------------------------------------------
# HOME VIEW
# -------------------------------------------------------------------
class Home(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = [
            {
                'image': 'account/suv.jpg',
                'title': 'Digital Receipts',
                'description': 'Manage and view all your receipts digitally for easier tracking and transparency.'
            },
            {
                'image': 'account/curva.jpg',
                'title': 'Secure Payments',
                'description': 'Every transaction is safe and verified for a seamless and reliable experience.'
            },
            {
                'image': 'account/swift.jpg',
                'title': 'Instant Access',
                'description': 'Access your receipt details anytime, anywhere from your personal dashboard.'
            }
        ]
        return context

# -------------------------------------------------------------------
# ADD MEMBER VIEW (CREATE)
# -------------------------------------------------------------------
from django.conf import settings
from twilio.rest import Client
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
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
    success_url = reverse_lazy('members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['relationship_types'] = RelationshipType.objects.all()
        context['blood_groups'] = BloodGroup.objects.all()
        context['marital_statuses'] = MaritalStatus.objects.all()
        context['business_types'] = TypeOFBusiness.objects.all()
        return context

    def form_valid(self, form):
        # Combine address fields
        plot = self.request.POST.get('plot_number', '').strip()
        landmark = self.request.POST.get('landmark', '').strip()
        city = self.request.POST.get('city', '').strip()
        state = self.request.POST.get('state', '').strip()
        form.instance.address = ", ".join(filter(None, [plot, landmark, city, state]))

        # Business name
        form.instance.business = self.request.POST.get('business_name', '').strip()

        response = super().form_valid(form)

        # ✅ Send Twilio SMS after member is created
        self.send_welcome_sms(form.instance)

        return response

    def send_welcome_sms(self, member):
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message_body = (
                f"Jai Swaminarayan {member.member_name}!\n"
                f"You have been successfully added to Shri Kutch Kadva Patidar Yuvak Mandal Samaj.\n"
                f"Welcome to our community!"
            )

            client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=f"+91{member.mobile_number}"  # Assuming Indian numbers
            )
        except Exception as e:
            print("Twilio SMS Error:", e)

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)


# -------------------------------------------------------------------
# MEMBER LIST VIEW (SEARCH + FILTER)
# -------------------------------------------------------------------
class MemberListView(ListView):
    model = Member
    template_name = 'members.html'
    context_object_name = 'members'
    paginate_by = 20

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


# -------------------------------------------------------------------
# RECEIPT VIEW (ADD + DISPLAY)
# -------------------------------------------------------------------
def receipt_view(request):
    member = None
    receipts = []
    payment_types = TypeOfPayment.objects.all()

    if request.method == "POST":
        print(">>> POST data:", request.POST)  # Debug line
        member_id = request.POST.get('member_id')
        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            messages.error(request, "Member not found.")
            member = None

        if member:
            fee_type_id = request.POST.get('fee_donation')
            fee_type = TypeOfPayment.objects.get(pk=fee_type_id) if fee_type_id else None

            # Auto-generate receipt number if not provided
            receipt_number = request.POST.get('receipt_number')
            if not receipt_number:
                last_receipt = Receipt.objects.order_by('-id').first()
                receipt_number = (last_receipt.receipt_number + 1) if last_receipt else 1

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


# -------------------------------------------------------------------
# API: FETCH MEMBERS (AJAX)
# -------------------------------------------------------------------
def get_members(request):
    ymid = request.GET.get("yuvak_mandal_id", "").strip()
    mobile = request.GET.get("mobile_number", "").strip()
    name = request.GET.get("member_name", "").strip()

    members = Member.objects.all()
    if ymid:
        members = members.filter(yuvak_mandal_id__iexact=ymid)
    elif mobile:
        members = members.filter(mobile_number__iexact=mobile)
    elif name:
        members = members.filter(member_name__icontains=name)

    data = [
        {
            "member_name": m.member_name,
            "mobile_number": m.mobile_number,
            "yuvak_mandal_id": m.yuvak_mandal_id,
            "member_id": m.id,
        }
        for m in members
    ]
    return JsonResponse({"members": data})


# -------------------------------------------------------------------
# API: GET NEXT RECEIPT NUMBER
# -------------------------------------------------------------------
def get_next_receipt_number(request):
    today = timezone.now().date()
    if today.month >= 4:
        fy_start = today.replace(month=4, day=1)
    else:
        fy_start = today.replace(year=today.year - 1, month=4, day=1)

    last_receipt = Receipt.objects.filter(date__gte=fy_start, date__lte=today).order_by('receipt_number').last()
    next_number = (last_receipt.receipt_number + 1) if last_receipt and last_receipt.receipt_number else 1
    return JsonResponse({"next_receipt_number": next_number})


# -------------------------------------------------------------------
# API: GET RECEIPTS (FILTER)
# -------------------------------------------------------------------
from django.views.generic import ListView
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from .models import Receipt

class ReceiptListView(ListView):
    model = Receipt
    paginate_by = 5  # ✅ 5 per page

    def get_queryset(self):
        qs = Receipt.objects.select_related('member', 'fee_donation').all().order_by('-pk')
        ymid = self.request.GET.get('yuvak_mandal_id')
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')

        if ymid:
            qs = qs.filter(member__yuvak_mandal_id=ymid)
        if from_date:
            qs = qs.filter(date__gte=parse_date(from_date))
        if to_date:
            qs = qs.filter(date__lte=parse_date(to_date))

        return qs.order_by('-date')

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()

        # ✅ Pagination logic
        paginator = Paginator(qs, self.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        receipts = [
            {
                "id": r.pk,
                "receipt_number": r.receipt_number,
                "date": r.date.strftime("%d-%m-%Y"),
                "member_name": r.member.member_name if r.member else "",
                "yuvak_mandal_id": r.member.yuvak_mandal_id if r.member else "",
                "fee_donation": r.fee_donation.name if r.fee_donation else "",
                "amount": str(r.amount),
            }
            for r in page_obj.object_list
        ]

        data = {
            "receipts": receipts,
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            }
        }

        return JsonResponse(data)



# -------------------------------------------------------------------
# EDIT MEMBER VIEW
# -------------------------------------------------------------------
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from twilio.rest import Client
from .models import Member, BloodGroup, TypeOFBusiness, RelationshipType, MaritalStatus

def edit_member(request, pk): # Debug line
    member = get_object_or_404(Member, pk=pk)
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

        plot_number = request.POST.get("plot_number", "")
        landmark = request.POST.get("landmark", "")
        city = request.POST.get("city", "")
        state = request.POST.get("state", "")
        member.address = f"{plot_number}, {landmark}, {city}, {state}"

        if "photo" in request.FILES:
            member.photo = request.FILES["photo"]

        member.save()

        # ✅ Send Twilio SMS after successful update
        send_update_sms(member)

        messages.success(request, "Member details updated successfully!")
        return redirect("members")

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


def send_update_sms(member):
    try:
        print(">>> Sending SMS to:", member.mobile_number)  # Debug line
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message_body = (
            f"🙏 Jai Swaminarayan {member.member_name}! 🙏\n"
            f"Your member profile in Shri Kutch Kadva Patidar Yuvak Mandal has been successfully updated.\n"
            f"Thank you for keeping your information up to date!"
        )

        client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+91{member.mobile_number}"
        )
        print(">>> SMS sent successfully!")  # Debug line
    except Exception as e:
        print("Twilio SMS Error:", e)



# -------------------------------------------------------------------
# RECEIPT DETAIL VIEW
# -------------------------------------------------------------------
def receipt_detail(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk)
    try:
        from num2words import num2words
        amount_in_words = num2words(receipt.amount, to='currency', lang='en_IN').replace("euro", "Rupees").title()
    except ImportError:
        amount_in_words = f"Rupees {receipt.amount} Only" if receipt.amount else ""

    return render(request, "reciept_detail.html", {
        "receipt": receipt,
        "amount_in_words": amount_in_words,
    })


# -------------------------------------------------------------------
# RECEIPT EDIT VIEW
# -------------------------------------------------------------------
def receipt_edit(request, receipt_id):
    """✅ Update receipt via fetch() POST"""
    receipt = get_object_or_404(Receipt, id=receipt_id)

    if request.method == 'POST':
        receipt.purpose = request.POST.get('purpose')
        receipt.amount = request.POST.get('amount')
        receipt.date = request.POST.get('date')
        receipt.fee_donation_id = request.POST.get('fee_donation')

        try:
            receipt.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # If directly opened (not via JS)
    payment_types = TypeOfPayment.objects.all()
    return render(request, 'reciept.html', {
        'receipt': receipt,
        'payment_types': payment_types,
        'edit_mode': True,
    })


@csrf_exempt
def delete_receipt(request, pk):
    if request.method == 'POST':
        try:
            receipt = Receipt.objects.get(pk=pk)
            receipt.delete()
            return JsonResponse({'success': True})
        except Receipt.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Not found'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})




def get_receipt(request, id):
    try:
        r = Receipt.objects.select_related('member', 'fee_donation').filter(id=id).first()
        data = {
            'id': r.id,
            'receipt_number': r.receipt_number,
            'date': r.date.strftime('%Y-%m-%d'),
            'member_name': r.member.member_name if r.member else '',
            'yuvak_mandal_id': r.member.yuvak_mandal_id if r.member else '',
            'mobile_number': r.member.mobile_number if r.member else '',
            'fee_donation': r.fee_donation.id if r.fee_donation else '',
            'purpose': r.purpose or '',
            'amount': r.amount or '',
        }
        return JsonResponse({'success': True, 'receipt': data})
    except Receipt.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Receipt not found'})