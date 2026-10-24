from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def inventory_dashboard(request):
    """Inventory dashboard view"""
    # This is integrated into the admin dashboard
    pass
