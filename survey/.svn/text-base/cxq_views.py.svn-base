__author__ = 'Administrator'
from django.http import HttpResponse
from django.utils import simplejson
from django.shortcuts import render_to_response
from datetime import datetime
from survey.forms import *
from util import *
from survey.models import *

def showIP(request):
    if request.POST:
        content = request.POST.get("content");
        html = "Your IP is %s" % request.META['REMOTE_ADDR']
        start_time = request.session.get('start_time')
        end_time = datetime.now()
        duration = str(end_time - start_time)
        dict = {"IP":html,"message":duration,}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
#        print duration
#        return HttpResponse(duration)
    start_time = datetime.now()
    request.session['start_time'] = start_time;
    template = "showIP.html"
    data = {}
    return render_to_response(template,data)

def result(request):
    if request.POST:
        answer1 = request.POST.get("answer1");
        answer2 = request.POST.get("answer2");
        answer3 = request.POST.get("answer3");
        start_time = request.session.get('start_time')
        end_time = datetime.now()
        duration = str(end_time - start_time)
        duration = duration.split('.')[0];
        html = "";
        html += "The answer of question %d is %s <br />" % (1,answer1)
        html += "The answer of question %d is %s <br />" % (2,answer2)
        html += "The answer of question %d is %s <br />" % (3,answer3)
        html += "The total time you used is %s <br />" % duration
        dict = {"result":html,}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    template = "showIP.html"
    data = {}
    return render_to_response(template,data)

def register(request):
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            email=form.cleaned_data.get('email')
            dict = {"username":username,
                    "password":password,
                    "email": email,}
            return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    else:
        form = RegistrationForm()
        dict = {"register_form":form}
        template = 'cxq_registration.html'
        return render_to_response(template, dict)

def add_component(request,surveyID=0):###

    if request.POST:
        request.session['question_created_total'] = str(int(request.session['question_created_total'])+1)
        question_no = int(request.session.get("question_created_total")) #This is used to group selections, not for the index.


        question_description = 'Click here to change the description'###
        question_helptext = "Click here to add help text"###
        values = "sample1@#@sample2@#@sample3@#@sample4"###

        if request.POST.get("questionID"):###
            questionID = int(request.POST.get("questionID"))###
            question = Question.objects.get(id=questionID)
            question_description = question.title
            question_helptext = question.help_text
            if question.type in ("multiplechoice","checkbox"):
                if question.type ==  "multiplechoice":
                    choices = question.multiplechoicequestion.choices.all()
                if question.type == "checkbox":
                    choices = question.checkboxquestion.choices.all()
                value = ""
                for choice in choices:
                    value += "%s@#@" % choice.label
                value = value[0:-3]
        
        html = "<div class='singleQuestionDiv'>"
        html += "<span class='question_no'>Q:</span>"
        html += "<span class='question_description editable'>%s</span><br />" % question_description###
        html += "<span class='question_helptext editable hideable'>%s</span><br />" % question_helptext###
        type = request.POST.get("question_type")
        if (type=="paragraph"):
            html += show_paragraph()
        elif (type=="numeric"):
            html += show_numeric()
        elif (type=="checkbox"):
            group_name = question_no
            ###
            html += show_checkbox(group_name,values)
        elif (type=="multiplechoice"):
            group_name = question_no
            ###
            html += show_mcq(group_name,values)
        html+="</div>"
        dict = {"content": html}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    request.session['question_created_total']='0'
    template = "cxq_edit_survey.html"

    survey = ""  ###
    title = "New Survey(Click to change)"
    description = "Add description here"
    surveyID = int(surveyID)
    if surveyID != 0 :
        survey = Survey.objects.get(id=surveyID)
        title = survey.title
        description = survey.description
    dict = {'surveyID':surveyID, 'survey':survey, "title":title, "description":description}  ###
    return render_to_response(template,dict)

def create_survey(request):
    if request.POST:
        survey_title = request.POST.get("survey_title")
        survey_description = request.POST.get("survey_description")
        survey = Survey(title = survey_title)
        survey.description = survey_description
        survey.save()
        surveyID = survey.id
        dict = {"surveyID":surveyID}
        return HttpResponse(simplejson.dumps(dict),mimetype='application/javascript')

def delete_survey(request):
    if request.POST:
        surveyID = int(request.POST.get("surveyID"))
        survey = Survey.objects.get(id=surveyID)
        survey.delete()
        dict = {}
        return HttpResponse(simplejson.dumps(dict),mimetype='application/javascript')

def save_survey(request,surveyID):
    if request.POST:
        question_type = request.POST.get("question_type")
        question_no = request.POST.get("question_no")
        question_helptext = request.POST.get("question_helptext")
        question_title = request.POST.get("question_title")
        selections = request.POST.get("selections")
        attributes = request.POST.get("attributes")
        print question_type
        if int(surveyID)==0:
            survey = Survey(title="no title")
            survey.save()
            surveyID = survey.id
        if question_type=="paragraph":
            question = ParagraphQuestion()
        elif question_type == "numeric":
            question = NumericQuestion()
        elif question_type == "multiplechoice":
            question = MultipleChoiceQuestion()
        elif question_type == "checkbox":
            question = CheckboxQuestion()
        else :
            return
        question.survey = Survey.objects.get(id=surveyID)
        question.id_in_survey = question_no
        question.title = question_title
        question.help_text = question_helptext
        question.max_no_characters = 0
        print "1"
        question.save()
        print "2"
        if question_type == "paragraph":
            attributes_list = attributes.split("@#@")
            question.max_no_characters = int(attributes_list[0])
        elif question_type == "numeric":
            attributes_list = attributes.split("@#@")
            question.max_value = int(attributes_list[0])
            question.min_value = int(attributes_list[1])
        elif question_type == "multiplechoice":
            choices = selections.split("@#@")
            choices.pop()
            count = 0
            for choice_label in choices:
                count += 1
                choice  = MultipleChoice()
                choice.question = question
                choice.label = choice_label
                choice.id_in_question = count
                choice.save()
        elif question_type == "checkbox":
            choices = selections.split("@#@")
            choices.pop()
            count = 0
            for choice_label in choices:
                count += 1
                choice  = CheckboxChoice()
                choice.question = question
                choice.label = choice_label
                choice.id_in_question = count
                choice.save()
        else :
            return
        print "3"
        question.save()
        print "4"
        dict = {"surveyID":surveyID}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
def view_survey(request, view_key, *args, **kwargs):
    survey = Survey.objects.get(id = int(view_key))
    questions = survey.questions.order_by('id_in_survey')
    request.session['dt_start'] = datetime.now()
    dict = {'survey' : survey, 'questions' : questions, 'dt_start': datetime.now()}
    return render_to_response('respondent.html', dict)
def multiajax(request):
    template = "cxq_multiajax.html"
    data = {"current":"1"}
    if request.POST:
        total = request.POST.get("total")
        current = request.POST.get("current")
        dict = {"current":current}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
   #     template = "cxq_add_question.html"
#        return render_to_response(template,data)
#            print duration
    #        return HttpResponse(duration)
    return render_to_response(template,data)

def create_response(request):
    if request.POST:
        resp = Response()
        resp.ip_address = request.META['REMOTE_ADDR']
        print resp.ip_address
        resp.dt_start= request.session.get('dt_start')
        print resp.dt_start
        resp.dt_end = datetime.now()
        print resp.dt_end
        resp.survey = Survey.objects.get(id=int(request.POST.get("surveyID")))
        print resp.survey
        resp.save()
        dict = {"responseID":resp.id}
        return HttpResponse(simplejson.dumps(dict),mimetype='application/javascript')
def response_survey(request,responseID):
    if request.POST:
        answer = Answer()
        answer.response = Response.objects.get(id=responseID)
        answer.id_in_response = int(request.POST.get("id_in_response"))
        answer.type = request.POST.get("type")
        answer.value = request.POST.get("value")
        answer.save()
        dict = {}
        return HttpResponse(simplejson.dumps(dict),mimetype='application/javascript')

def data_table(request):

    if request.POST:
        aColumns = ["engine", 'browser', 'platform', 'version', 'grade'];
        sIndexColumn = "id"
        sLimit = ""
        if request.GET.get('iDisplayStart') and request.GET.get('iDisplayStart')!='-1':
            sLimitStart = int(request.GET.get('iDisplayStart'))
            sLimitEnd = int(request.GET.get('iDisplayLength'))+sLimitStart
        if request.GET.get('iSortCol_0'):
            sOrder = ""
            iSortingCols = int(request.GET.get('iSortingCols'))
            for i in range(iSortingCols):
                if (request.GET.get('bSortable_'+request.GET.get('iSortCol_'+str(i)))):
                    sOrder += "'"+aColumns[int(request.GET.get('iSortCol'+str(i)))]+"" \
                               "'"+request.GET.get('sSortDir_'+str(i))+", "
            sOrder = sOrder.rstrip(', ')
        total = request.POST.get("total");
        current = request.POST.get("current");
        dict = {"current":current}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    template = ""
    data = {}
    return render_to_response(template,data)
