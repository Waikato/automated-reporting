from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
import reporting.applist as applist
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


@login_required
#@permission_required("hr_forms.can_access_hr_forms")
def index(request):
    # configure template
    template = loader.get_template('hr_forms/index.html')
    context = applist.template_context('hr_forms')
    return HttpResponse(template.render(context, request))
