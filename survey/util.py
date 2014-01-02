from django.shortcuts import render_to_response
from survey.models import Answer
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers
import json
from datetime import datetime,timedelta

def show_paragraph(max_character=1000,number_of_columns=100, number_of_rows=50,is_required=True):
    require_checked = 'checked'
    print is_required
    if not is_required:
        require_checked = ''
    html = r"<textarea class='paragraph_question' />"\
           r"<div class='hideable' id='attributes'>"\
           r"Max character: <input type='text' class='number_only' value='%d'/>(0-10000)<br >"\
           r"Required: <input type='checkbox' id='is_required' %s/><br >"\
           r"</div>" % (max_character,require_checked)
    return html

def show_numeric(max_value=100, min_value=0,is_required=True):
    require_checked = 'checked'
    if not is_required:
        require_checked = ''
    html = r"<input type='text' class='numeric_question' /><span class=''>(Min value-Max value)</span>"\
           r"<div class='hideable' id='attributes'>"\
           r"Max value: <input type='text' class='number_only' value='%d'/>(-10000~10000)<br >"\
           r"Min value: <input type='text' class='number_only' value='%d'/>(-10000~10000)<br >"\
           r"Required: <input type='checkbox' id='is_required' %s/><br >"\
           r"</div>" % (max_value, min_value,require_checked)
    return html

def show_checkbox_option(group_name, description):
    html = r"<div class='selection'>"\
           r"<input type='checkbox' class='checkbox_option' name='%s'>"\
           r"<span class='editable'>%s</span></input>"\
           r"</div>" % (group_name, description)
    return html

def show_checkbox(group_name, values, max_checked=4, min_checked=0,is_required=True):
    require_checked = 'checked'
    if not is_required:
        require_checked = ''
    values = values.split('@#@')
    html = r"<div class='selections_container sortable'>"
    for value in values:
        html += show_checkbox_option(group_name, value)
    html += r"</div>"
    html += r"<div class='hideable' id='attributes'>"\
            r"Max checked: <input type='text' class='number_only' value='%d'/>(>0)<br >"\
            r"Min checked: <input type='text' class='number_only' value='%d'/>(>0)<br >"\
            r"Required: <input type='checkbox' id='is_required' %s/><br >"\
            r"<button class='addNewSelection'>Add new selection</button>"\
            r"</div>" % (max_checked, min_checked, require_checked)
    return html
def show_mcq_option(group_name,description):
    html = r"<div class='selection'>"\
           r"<input type='radio' class='mcq_option' name='%s'>"\
           r"<span class='editable'>%s</span></input>"\
           r"</div>" % (group_name, description)
    return html

def show_mcq(group_name, values, is_required=True):
    require_checked = 'checked'
    if not is_required:
        require_checked = ''
    values = values.split('@#@')
    html = r"<div class='selections_container sortable'>"
    for value in values:
        html += show_mcq_option(group_name, value)
    html += r"</div>"
    html += r"<div class='hideable' id='attributes'>"\
            r"Required: <input type='checkbox' id='is_required' %s/><br >"\
            r"<button class='addNewSelection'>Add new selection</button>"\
            r"</div>" % require_checked
    return html

def show_scale(max_value=100, min_value=0,increment=1,is_required=True):
    require_checked = 'checked'
    if not is_required:
        require_checked = ''
    html = r"<div class='slider_attr'>(Min: XX; Max: XX; Increment: XX) " \
           r"<br >Value = <span class='slider_value'>XX</span> (slide to change)" \
           r"</div>" \
           r"<div class='slider'></div>"\
           r"<div class='hideable' id='attributes'>"\
           r"Max value: <input type='text' class='number_only' value='%f'/>(-10000~10000)<br >"\
           r"Min value: <input type='text' class='number_only' value='%f'/>(-10000~10000)<br >"\
           r"Increment: <input type='text' class='number_only' value='%f'/>(0~10000)<br >"\
           r"Required: <input type='checkbox' id='is_required' %s/><br >"\
           r"</div>" % (max_value, min_value,increment,require_checked)
    return html
def show_text(max_no_character=255,is_required=True):
    require_checked = 'checked'
    if not is_required:
        require_checked = ''
    html = r"<input type='text' class='text_question' /><span class=''>(Max character: XX)</span>"\
           r"<div class='hideable' id='attributes'>"\
           r"Max character: <input type='text' class='number_only' value='%d'/>(0~255)<br >"\
           r"Required: <input type='checkbox' id='is_required' %s/><br >"\
           r"</div>" % (max_no_character,require_checked)
    return html
def show_date(max_value="", min_value="",start_value="",is_required=True):
    require_checked = 'checked'
    if not is_required:
        require_checked = ''
    now = datetime.now()
    if not max_value:
        max_value = now + timedelta(days=180)
    if not min_value:
        min_value = now - timedelta(days=180)
    if not start_value:
        start_value = now
    max_value = max_value.strftime("%d/%m/%Y")
    min_value = min_value.strftime("%d/%m/%Y")
    start_value = start_value.strftime("%d/%m/%Y")
    html = r"<div class='datepicker_flexible_container'>Date: <input type='text' value='%s' class='datepicker' /><div>"\
           r"<div class='hideable datepicker_flexible_container' id='attributes'>"\
           r"From: <input type='text' value='%s' class='datepicker' /><br >"\
           r"To: <input type='text' value='%s' class='datepicker' /><br >"\
           r"Initial: <input type='text' value='%s' class='datepicker' /><br>"\
           r"Required: <input type='checkbox' id='is_required' %s/>"\
           r"</div>" % (start_value,min_value, max_value,start_value,require_checked)
    return html
def get_datatables_records(request, querySet, columnIndexNameMap, jsonTemplatePath = None, *args):
    """
    Usage:
        querySet: query set to draw data from.
        columnIndexNameMap: field names in order to be displayed.
        jsonTemplatePath: optional template file to generate custom json from.  If not provided it will generate the data directly from the model.

    """

    cols = int(request.GET.get('iColumns',0)) # Get the number of columns
    iDisplayLength =  min(int(request.GET.get('iDisplayLength',10)),100)     #Safety measure. If someone messes with iDisplayLength manually, we clip it to the max value of 100.
    startRecord = int(request.GET.get('iDisplayStart',0)) # Where the data starts from (page)
    endRecord = startRecord + iDisplayLength  # where the data ends (end of page)

    # Pass sColumns
    keys = columnIndexNameMap.keys()
    keys.sort()
    colitems = [columnIndexNameMap[key] for key in keys]
    sColumns = ",".join(map(str,colitems))

    # Ordering data
    iSortingCols =  int(request.GET.get('iSortingCols',0))
    asortingCols = []

    if iSortingCols:
        for sortedColIndex in range(0, iSortingCols):
            sortedColID = int(request.GET.get('iSortCol_'+str(sortedColIndex),0))
            if request.GET.get('bSortable_{0}'.format(sortedColID), 'false')  == 'true':  # make sure the column is sortable first
                sortedColName = columnIndexNameMap[sortedColID]
                sortingDirection = request.GET.get('sSortDir_'+str(sortedColIndex), 'asc')
                if sortingDirection == 'desc':
                    sortedColName = '-'+sortedColName
                asortingCols.append(sortedColName)
        querySet = querySet.order_by(*asortingCols)

    # Determine which columns are searchable
    searchableColumns = []
    for col in range(0,cols):
        if request.GET.get('bSearchable_{0}'.format(col), False) == 'true': searchableColumns.append(columnIndexNameMap[col])

    # Apply filtering by value sent by user
    customSearch = request.GET.get('sSearch', '').encode('utf-8');
    if customSearch != '':
        outputQ = None
        first = True
        for searchableColumn in searchableColumns:
            kwargz = {searchableColumn+"__icontains" : customSearch}
            outputQ = outputQ | Q(**kwargz) if outputQ else Q(**kwargz)
        querySet = querySet.filter(outputQ)

    # Individual column search
    outputQ = None
    for col in range(0,cols):
        if request.GET.get('sSearch_{0}'.format(col), False) > '' and request.GET.get('bSearchable_{0}'.format(col), False) == 'true':
            kwargz = {columnIndexNameMap[col]+"__icontains" : request.GET['sSearch_{0}'.format(col)]}
            outputQ = outputQ & Q(**kwargz) if outputQ else Q(**kwargz)
    if outputQ: querySet = querySet.filter(outputQ)

    iTotalRecords = iTotalDisplayRecords = querySet.count() #count how many records match the final criteria
    querySet = querySet[startRecord:endRecord] #get the slice
    sEcho = int(request.GET.get('sEcho',0)) # required echo response

    if jsonTemplatePath:
        jstonString = render_to_string(jsonTemplatePath, locals()) #prepare the JSON with the response, consider using : from django.template.defaultfilters import escapejs
        response = HttpResponse(jstonString, mimetype="application/javascript")
    else:
        aaData = []
        a = querySet.values()
        for row in a:
            rowkeys = row.keys()
            rowvalues = row.values()
            rowlist = []
            for col in range(0,len(colitems)):
                for idx, val in enumerate(rowkeys):
                    if val == colitems[col]:
                        rowlist.append(str(rowvalues[idx]))
            aaData.append(rowlist)
        response_dict = {}
        response_dict.update({'aaData':aaData})
        response_dict.update({'sEcho': sEcho, 'iTotalRecords': iTotalRecords, 'iTotalDisplayRecords':iTotalDisplayRecords, 'sColumns':sColumns})
        response =  HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
        #prevent from caching datatables result
    add_never_cache_headers(response)
    return response
def isfloat(string):
    try:
        float(string)
    except BaseException as e:
        return False
    return True