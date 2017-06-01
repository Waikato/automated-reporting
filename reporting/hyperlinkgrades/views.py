from django.template import loader
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
import reporting.applist as applist
from dbbackend.models import read_last_parameter, write_last_parameter
from reporting.form_utils import get_variable, create_error_response
import reporting.settings
import subprocess
import os.path

DEFAULT_EXPRESSION = '.*(possible b sem 15 completer|possible b sem 15 completion|potential sem b 2015 completion|potential b sem 2015 completion).*'
""" The default expression for matching the links. """


@login_required
@permission_required("hyperlinkgrades.can_access_hyperlinkgrades")
def index(request):
    # configure template
    template = loader.get_template('hyperlinkgrades/index.html')
    context = applist.template_context('hyperlinkgrades')
    context['last_expression'] = read_last_parameter(request.user, 'hyperlinkgrades.expression', def_value=DEFAULT_EXPRESSION)
    context['last_casesensitive_matching'] = bool(read_last_parameter(request.user, 'hyperlinkgrades.casesensitive_matching', def_value='False'))
    context['last_exclude_completions'] = bool(read_last_parameter(request.user, 'hyperlinkgrades.exclude_completions', def_value='True'))
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("hyperlinkgrades.can_access_hyperlinkgrades")
def upload(request):
    # get parameters
    print(request.POST)
    expression = get_variable(request, 'expression', def_value=DEFAULT_EXPRESSION)
    casesensitive_matching = (get_variable(request, 'casesensitive_matching', def_value='off') == 'on')
    exclude_completions = (get_variable(request, 'exclude_completions', def_value='off') == 'on')

    print(expression, casesensitive_matching, exclude_completions)

    pdf = request.FILES['datafile']

    newpdf = pdf.temporary_file_path() + "-linked.pdf"
    csv = pdf.temporary_file_path() + "-linked.csv"
    params = [
        reporting.settings.JAVA,
        "-cp",
        reporting.settings.DOC_MOD_LIB + "/*",
        "nz.ac.waikato.cms.doc.HyperLinkGrades",
        pdf.temporary_file_path(),
        expression,
        newpdf,
        csv,
    ]
    if casesensitive_matching:
        params = params + ["--casesensitive", "true"]
    if exclude_completions:
        params = params + ["--nocompletions", "true"]
    retval = subprocess.call(
        params,
    )
    if retval != 0:
        return create_error_response(request, 'hyperlinkgrades', 'Failed to execute HyperLinkGrades: {0}'.format(retval))

    if not os.path.exists(newpdf):
        return create_error_response(request, 'hyperlinkgrades', 'Failed to generate output!')

    write_last_parameter(request.user, 'hyperlinkgrades.last_expression', expression)
    write_last_parameter(request.user, 'hyperlinkgrades.last_casesensitive_matching', casesensitive_matching)
    write_last_parameter(request.user, 'hyperlinkgrades.last_exclude_completions', exclude_completions)

    data = list()
    with open(newpdf, "rb") as f:
        byte = f.read(1)
        while byte != b"":
            data.append(byte)
            byte = f.read(1)

    # clean up
    if os.path.exists(newpdf):
        os.remove(newpdf)
    if os.path.exists(csv):
        os.remove(csv)

    response = HttpResponse(data, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(os.path.basename(pdf.name))
    return response
