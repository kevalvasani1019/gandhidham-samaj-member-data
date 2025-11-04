from django.urls import path
from .views import Home,  MemberListView, AddFormCreateView, ReceiptListView, delete_receipt, edit_member,  get_members, get_next_receipt_number, get_receipt, receipt_detail, receipt_edit, receipt_view
from django.conf import settings
from django.conf.urls.static import static
from .views import CustomLoginView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', Home.as_view(), name='home'),
    # path('login', Login.as_view(), name='login'),

    path('member/', MemberListView.as_view(), name='members'),
    path('add-member/', AddFormCreateView.as_view(), name='add_member'),
path('receipt/', receipt_view, name='receipt'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html'), name='password_reset'),
    path('get_members/', get_members, name='get_members'),
    path('get_next_receipt_number/', get_next_receipt_number, name='get_next_receipt_number'),
    path('get_receipts/',  ReceiptListView.as_view(), name='get_receipts'),
    path('receipt/<int:pk>/', receipt_detail, name='receipt_detail'),
    path("member/<int:pk>/edit/", edit_member, name="edit_member"),

    path('delete-receipt/<int:pk>/', delete_receipt, name='delete_receipt'),

    path('receipt/<int:receipt_id>/edit/', receipt_edit, name='receipt_edit'), 
    path('get_receipt/<int:id>/', get_receipt, name='get_receipt'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)