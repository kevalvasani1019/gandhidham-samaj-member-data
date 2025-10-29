from django.urls import path
from .views import Home, MemberListView, AddFormCreateView, edit_member,  get_members, get_next_receipt_number, get_receipts, receipt_view
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('member/', MemberListView.as_view(), name='members'),
    path('add-member/', AddFormCreateView.as_view(), name='add_member'),
path('receipt/', receipt_view, name='receipt'),

    path('get_members/', get_members, name='get_members'),
    path('get_next_receipt_number/', get_next_receipt_number, name='get_next_receipt_number'),
    path('get_receipts/', get_receipts, name='get_receipts'),
    
    path("member/<int:pk>/edit/", edit_member, name="edit_member"),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)