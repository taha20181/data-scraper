from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.core.paginator import Paginator

from scraper.models import Session
import pandas as pd
from django.http import HttpResponse


def dashboard_view(request):
    sessions = Session.objects.filter()
    return render(request, "dashboard.html", {
        "total_sessions": sessions.filter(session_type='session').count(),
        "total_posters": sessions.filter(session_type='poster').count(),
        "total_authors": sessions.filter().values_list('authors', flat=True).distinct().count(),
    })


def list_view(request):
    qs = Session.objects.filter().order_by("-id")

    # filter
    type_filter = request.GET.get("type")
    if type_filter:
        qs = qs.filter(session_type=type_filter)

    # search
    search = request.GET.get("search")
    if search:
        qs = qs.filter(session_title__icontains=search)

    paginator = Paginator(qs, 20)
    page = request.GET.get("page")

    return render(request, "list.html", {
        "page_obj": paginator.get_page(page)
    })


def export(request):
    format = request.GET.get("format")
    data = []

    queryset = Session.objects.filter()

    for obj in queryset:
        data.append({
            "Title": str(obj.session_title),
            "Type": obj.session_type,
            "Date": obj.date if obj.date else "",
            "Time": obj.time if obj.time else "",
            "Location": obj.location if obj.location else "",
            "Authors": ", ".join([a for a in obj.authors])
        })

    df = pd.DataFrame(data)

    if format == "xslx":
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = "attachment; filename=export_data.xlsx"
    else:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=export_data.csv"
        df.to_csv(response, index=False)
        return response

    df.to_excel(response, index=False)

    return response