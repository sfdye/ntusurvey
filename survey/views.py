from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from datetime import datetime, timedelta
from util import *
from survey.models import *
from django.contrib.auth.decorators import login_required
from django.core.validators import email_re
from django.core.mail import send_mail
from django.contrib.sites.models import get_current_site
from django.contrib import messages

def home(request):
    if  request.user.is_authenticated():
        return HttpResponseRedirect('/account')
    else:
        return render_to_response('home.html', RequestContext(request))

@login_required()
def print_survey(request, view_key, *args, **kwargs):
    try:
        survey = Survey.objects.get(key=view_key)
    except BaseException as e:
        return error_jump(request)
    if not survey.user.id == request.user.id and not survey.is_collaborator(request.user):
        return error_jump(request,"unauthorized")
    questions = survey.questions.order_by('id_in_survey')
    request.session['dt_start'] = datetime.now()
    dict = {'survey': survey, 'questions': questions, 'dt_start': datetime.now()}
    return render_to_response('print.html', dict, RequestContext(request))


def string_cmp((k1, v1), (k2, v2)):
    return cmp(float(k1), float(k2))

def date_cmp((k1, v1), (k2, v2)):
    return cmp(datetime.strptime(k1, '%d %B'), datetime.strptime(k2, '%d %B'))

import pygeoip
from django.conf import settings
from django.db.models.aggregates import Min, Max, Avg

@login_required()
def analyse(request, view_key=""):
    try:
        survey = Survey.objects.get(key=view_key)
    except BaseException as e:
        return error_jump(request)
    if not survey.user.id == request.user.id and not survey.is_collaborator(request.user):
        return error_jump(request,"unauthorized")


    questions = survey.questions.order_by('id_in_survey')
    raw_data = []

    geo_data = []
    geo_dict = {}
    gi = pygeoip.GeoIP(settings.GEO_DATA_PATH, pygeoip.MEMORY_CACHE)

    responses = Response.objects.filter(survey=survey)
    # how many people skipped each question marked as not required
    no_skipped = []

    respondents_data = []
    time_data = {}
    time_in_seconds = []
    date_dict = {}
    # analyse geoip data of responses

    for response in responses:
        date_str = response.dt_end.strftime('%d %B')
        time_in_seconds.append((response.dt_end - response.dt_start).seconds)
        if date_str not in date_dict:
            date_dict[date_str] = 1
        else:
            date_dict[date_str] += 1
        ip = str(response.ip_address)
        country = gi.country_name_by_addr(ip)
        if country not in geo_dict:
            geo_dict[country] = 1
        else:
            geo_dict[country] += 1
    try:
        time_data['seconds'] = time_in_seconds
        time_data['min'] = min(time_in_seconds)
        time_data['max'] = max(time_in_seconds)
        time_data['avg'] = sum(time_in_seconds) / len(time_in_seconds)
    except BaseException as e:
        pass

    # analyse number of daily responses
    for key, value in sorted(date_dict.items(), cmp=date_cmp):
        respondents_data.append([key, value])

    for key, value in geo_dict.items():
        geo_data.append([key, value])

    # analyse each question
    for question in questions:
        type = question.type
        answers = Answer.objects.filter(response__survey=survey, id_in_response=question.id_in_survey)
        # calc number of skipped responses for this question
        if not question.is_required:
            no_skipped.append(answers.filter(value__exact='').count())
        else:
            no_skipped.append(0)
            # after counting skipped questions, excluding all empty answers
        answers = answers.exclude(value__exact='')

        if type == 'paragraph' or type == 'text':
            # for paragraph and text question, only display all responses
            raw_data.append([answer.value for answer in answers])

        elif type == 'multiplechoice' or type == 'checkbox':
            # get choices
            if type == 'multiplechoice':
                choices = MultipleChoice.objects.filter(question=question)
            else:
                choices = CheckboxChoice.objects.filter(question=question)

            # init list to [0,0,0,0,0...]
            resp_count = [0] * len(choices)
            # calc number of responses for each choice
            for answer in answers:
                for choice in answer.value.split(','):
                    resp_count[int(choice)] += 1

            data_dict = []
            for choice, count in zip(choices, resp_count):
                data_dict.append([str(choice.label), int(count)])

            raw_data.append(data_dict)
        elif type == 'numeric':
            num_dict = {}
            num_dict['data'] = [float(answer.value) for answer in answers]
            num_dict['min_value'] = answers.aggregate(Min('value'))['value__min']
            num_dict['max_value'] = answers.aggregate(Max('value'))['value__max']
            num_dict['avg'] = answers.aggregate(Avg('value'))['value__avg']
            raw_data.append(num_dict)


        elif type == 'scale':
            data_dict = {}
            for answer in answers:
                if answer.value not in data_dict:
                    data_dict[answer.value] = 1
                else:
                    data_dict[answer.value] += 1
            tmp_list = []
            # sort according to key
            for key, value in sorted(data_dict.items(), cmp=string_cmp):
                tmp_list.append([str(key), float(value)])
            raw_data.append(tmp_list)
        elif type == 'date':
            raw_data.append(str(answer.value) for answer in answers)

    zipped = zip(questions, raw_data, no_skipped)

    dict = {'survey': survey,
            'questions': questions,
            # 'dt_start': datetime.now(),
            'responses': responses,
            'zipped': zipped,
            'time_data' : time_data,
            'respondents_data': respondents_data,
            'geo_data': geo_data}
    return render_to_response('analyse.html', dict, RequestContext(request))


def about(request):
    return render_to_response('about.html', RequestContext(request))


def signup(request):
    return render_to_response('signup.html', RequestContext(request))


def test_view(request):
    return render_to_response('cqx_test.html', RequestContext(request))


def publish(request, publish_key):
    current_site = get_current_site(request)
    dict = {"key": publish_key,
            'SITE_URL' : current_site.domain
    }
    return render_to_response('publish.html', dict, RequestContext(request))


def create_response(request):
    if request.POST:
        resp = Response()
        # get ip address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            resp.ip_address = x_forwarded_for.split(',')[0]
        else:
            resp.ip_address = request.META.get('REMOTE_ADDR')
        resp.dt_start = request.session.get('dt_start')
        resp.dt_end = datetime.now()
        resp.survey = Survey.objects.get(id=int(request.POST.get("surveyID")))
        resp.save()
        dict = {"responseID": resp.id}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    return error_jump(request)
def validate_answer(request):
    if request.POST:
        id_in_response = int(request.POST.get("id_in_response"))
        type = request.POST.get("type")
        value = request.POST.get("value")
        surveyID = int(request.POST.get("surveyID"))
        errors = ""
        li = "<li>Q%d: %s</li>" % (id_in_response, "%s")
        survey = Survey.objects.get(id=surveyID)
        question = survey.questions.get(id_in_survey=id_in_response)
        deadline = survey.deadline
        now = datetime.now()
        if question.is_required and value == "":
            errors += li % "This question is required."
        if now > deadline:
            errors += "<li>This survey is expired already.</li>"
        if type == 'paragraph':
                max_no_characters = question.paragraphquestion.max_no_characters
                length = len(value)
                if length > max_no_characters:
                    errors += li % "Number of characters cannot exceed %d, %d characters are provided." % (
                        max_no_characters, length)
        if type == 'text':
            max_no_characters = question.textquestion.max_no_characters
            length = len(value)
            if length > max_no_characters:
                errors += li % "Number of characters cannot exceed %d, %d characters are provided." % (
                    max_no_characters, length)
        if type == "numeric":
            max_value = question.numericquestion.max_value
            min_value = question.numericquestion.min_value
            value = value.strip()
            if not isfloat(value):
                errors += li % "Legal digits required."
            else:
                value = float(value)
                if value > max_value or value < min_value:
                    errors += li % "Please enter in a number in [%f,%f], %f is provided." % (
                        min_value, max_value, value)
        if type == "checkbox":
            min_checked = question.checkboxquestion.min_checked
            max_checked = question.checkboxquestion.max_checked
            no_checked = len(value.split(","))
            if value == "":
                no_checked = 0
            if no_checked > max_checked or no_checked < min_checked:
                errors += li % "Please choose [%d,%d], %d choices are chosen." % (min_checked, max_checked, no_checked)
        dict = {"errors": errors}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    return error_jump(request)

def response_survey(request, responseID):
    if request.POST:
        answer = Answer()
        answer.response = Response.objects.get(id=responseID)
        answer.id_in_response = int(request.POST.get("id_in_response"))
        answer.type = request.POST.get("type")
        answer.value = request.POST.get("value")
        answer.save()
        dict = {}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    return error_jump(request)
@login_required()
def account(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login')

    surveys = Survey.objects.filter(user=request.user).order_by('-last_modified')
    titles = [str(survey.title) for survey in surveys]
    if request.POST:
        search_value = request.POST.get('search_value')
        if search_value:
            surveys = surveys.filter(title__icontains=search_value)

    collaborations = Collaboration.objects.filter(user_id=request.user.id, is_active=1)
    collaborated_surveys_ids = [c.survey_id for c in collaborations]
    collaborated_surveys = Survey.objects.filter(id__in=collaborated_surveys_ids)
    print collaborations
    return render_to_response('account.html',
        {'surveys': surveys, 'titles': titles, 'collaborated_surveys': collaborated_surveys}, RequestContext(request))


@login_required
def edit_account(request):
    return render_to_response('edit_account.html', RequestContext(request))


def edit_survey(request, view_key=""):
    if request.POST:
        request.session['question_created_total'] = str(int(request.session['question_created_total']) + 1)
        question_no = int(
            request.session.get("question_created_total")) #This is used to group selections, not for the index.

        question_description = 'Click here to change the description'
        question_helptext = "Click here to add help text"
        values = "sample1@#@sample2@#@sample3@#@sample4"
        question = ""

        if request.POST.get("questionID"):
            questionID = int(request.POST.get("questionID"))
            question = Question.objects.get(id=questionID)
            question_description = question.title
            question_helptext = question.help_text
            if question.type in ("multiplechoice", "checkbox"):
                if question.type == "multiplechoice":
                    choices = question.multiplechoicequestion.choices.all()
                if question.type == "checkbox":
                    choices = question.checkboxquestion.choices.all()
                value = ""
                for choice in choices:
                    value += "%s@#@" % choice.label
                values = value[0:-3]

        html = "<div class='singleQuestionDiv'>"
        html += "<span class='question_no'>Q:</span>"
        html += "<span class='question_description editable'>%s</span><br />" % question_description
        html += "<span class='question_helptext editable hideable'>%s</span><br />" % question_helptext
        type = request.POST.get("question_type")
        group_name = question_no
        if request.POST.get("questionID"):
            if type == "paragraph":
                html += show_paragraph(question.paragraphquestion.max_no_characters, is_required=question.is_required)
            elif type == "numeric":
                html += show_numeric(question.numericquestion.max_value, question.numericquestion.min_value,
                    question.is_required)
            elif type == "checkbox":
                html += show_checkbox(group_name, values, question.checkboxquestion.max_checked,
                    question.checkboxquestion.min_checked, question.is_required)
            elif type == "multiplechoice":
                html += show_mcq(group_name, values, question.is_required)
            elif type == "scale":
                html += show_scale(max_value=question.scalequestion.max_value,
                    min_value=question.scalequestion.min_value, increment=question.scalequestion.increment,
                    is_required=question.is_required)
            elif type == "date":
                html += show_date(min_value=question.datequestion.min_value,
                    max_value=question.datequestion.max_value, start_value=question.datequestion.start_value,
                    is_required=question.is_required)
            elif type == "text":
                html += show_text(max_no_character=question.textquestion.max_no_characters,
                    is_required=question.is_required)
        else:
            if type == "paragraph":
                html += show_paragraph()
            elif type == "numeric":
                html += show_numeric()
            elif type == "checkbox":
                html += show_checkbox(group_name, values)
            elif type == "multiplechoice":
                html += show_mcq(group_name, values)
            elif type == "scale":
                html += show_scale()
            elif type == "date":
                html += show_date()
            elif type == "text":
                html += show_text()
        html += "</div>"
        dict = {"content": html}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    request.session['question_created_total'] = '0'

    is_collaborator = False
    collaborators = ""
    survey = ""
    title = "New Survey(Click to change)"
    description = "Add description here"
    deadline = datetime.now() + timedelta(days=7)
    #    surveyID = int(surveyID)
    surveyID = 0
    try:
        if view_key != "":
            surveyID = Survey.objects.get(key=view_key).id
    except BaseException as e:
        return error_jump(request)
    if surveyID != 0:
        survey = Survey.objects.get(id=surveyID)
        is_collaborator = survey.is_collaborator(request.user)
        collaborators = []
        for collaborator in survey.collaboration_set.all():
            collaborators.append(str(collaborator.user.id))
        collaborators = ",".join(collaborators)
        title = survey.title
        description = survey.description
        deadline = survey.deadline
    deadline = deadline.strftime("%d/%m/%Y")

    dict = {'surveyID': surveyID, 'survey': survey, "title": title, "description": description, "deadline": deadline,
            'is_collaborator': is_collaborator, 'collaborators': collaborators}
    template = "edit_survey.html"
    return render_to_response(template, dict, RequestContext(request))


def validate_survey(request):
    if request.POST:
        question_type = request.POST.get("question_type")
        question_no = int(request.POST.get("question_no"))
        question_helptext = request.POST.get("question_helptext")
        question_title = request.POST.get("question_title")
        selections = request.POST.get("selections")
        selections = selections.split("@#@")
        attributes = request.POST.get("attributes")
        attributes = attributes.split("@#@")
        survey_title = request.POST.get("survey_title").strip()
        survey_description = request.POST.get("survey_description")
        survey_deadline = request.POST.get("survey_deadline")
        survey_deadline = survey_deadline.strip()
        survey_same_title = Survey.objects.filter(title=survey_title,user=request.user)
        print survey_same_title
        surveyID = int(request.POST.get("surveyID"))
        errors = ""
        li = "<li>Q%d: %s</li>" % (question_no, "%s")
        if survey_title == "New Survey(Click to change)" or survey_title == "Click here to add...":
            survey_title = ""
        if len(survey_same_title)>0 and question_no==1 and (surveyID==0 or not Survey.objects.get(id=surveyID).title==survey_title):
            errors += "<li>%s: %s</li>" % (
                "Survey title", "You have already created a survey with the same title.")
        if len(survey_title)==0 and question_no==1:
            errors += "<li>%s: %s</li>" % (
                "Survey title", "Please enter a title..")
        if len(survey_title) > 128 and question_no == 1:
            errors += "<li>%s: %s</li>" % (
                "Survey title", "Number of characters cannot exceed %d, %d characters are provided.") % (
                          128, len(survey_title))
        if len(survey_description) > 10000 and question_no == 1:
            errors += "<li>%s: %s</li>" % (
                "Survey description", "Number of characters cannot exceed %d, %d characters are provided.") % (
                          10000, len(survey_description))
        try:
            select_time = datetime.strptime(survey_deadline, "%d/%m/%Y")
            if select_time < datetime.now():
                errors += "<li>%s: %s</li>" % ("Survey deadline", "Please choose one after today's date.")
        except BaseException as e:
            errors += "<li>%s: %s</li>" % ("Survey deadline", "The date format is invalid, please select one.")
        if len(question_title) > 500:
            errors += li % "%s -- Cannot exceed 500 characters, %d characters provided." % (
                "Question title", len(question_title))
        if len(question_helptext) > 500:
            errors += li % "%s -- Cannot exceed 500 characters, %d characters provided." % (
                "Question help text", len(question_helptext))
        if question_type == 'paragraph':
                max_no_characters = attributes[0]
                try:
                    max_no_characters = int(max_no_characters)
                    if max_no_characters > 10000 or max_no_characters < 0:
                        errors += li % "%s -- Please enter in an integer in [0,10000], %d provided." % (
                            "Max character", max_no_characters)
                except BaseException as e:
                    errors += li % "%s -- Please enter in an integer in [0,10000]." % "Max character"
        if question_type == 'text':
            max_no_characters = attributes[0]
            try:
                max_no_characters = int(max_no_characters)
                if max_no_characters > 255 or max_no_characters < 0:
                    errors += li % "%s -- Please enter in an integer in [0,255], %d provided." % (
                        "Max character", max_no_characters)
            except BaseException as e:
                errors += li % "%s -- Please enter in an integer in [0,255]." % "Max character"
        if question_type == "numeric":
            max_value = attributes[0]
            min_value = attributes[1]
            try:
                max_value = float(max_value)
                min_value = float(min_value)
                if max_value > 10000 or max_value < -10000:
                    errors += li % "%s -- Please enter in a float in [-10000,10000], %f provided." % (
                        "Max value", max_value)
                if min_value > 10000 or min_value < -10000:
                    errors += li % "%s -- Please enter in a float in [-10000,10000], %f provided." % (
                        "Min value", min_value)
                if max_value < min_value:
                    errors += li % "Max value must be greater than min value."
            except BaseException as e:
                errors += li % "Max & Min value must be floats in [-10000, 10000]"
        if question_type == "scale":
            max_value = attributes[0]
            min_value = attributes[1]
            increment = attributes[2]
            try:
                max_value = float(max_value)
                min_value = float(min_value)
                increment = float(increment)
                if max_value > 10000 or max_value < -10000:
                    errors += li % "%s -- Please enter in a float in [-10000,10000], %f provided." % (
                        "Max value", max_value)
                if min_value > 10000 or min_value < -10000:
                    errors += li % "%s -- Please enter in a float in [-10000,10000], %f provided." % (
                        "Min value", min_value)
                if increment > 10000 or increment <= 0:
                    errors += li % "%s -- Please enter in a float in (-0,10000], %f provided." % (
                        "Increment", increment)
                if max_value < min_value:
                    errors += li % "Max value must be greater than min value."
            except BaseException as e:
                errors += li % "Max,Min and increment value must be invalid floats"
        if question_type == "date":
            min_value = attributes[0]
            max_value = attributes[1]
            start_value = attributes[2]
            try:
                max_value = datetime.strptime(max_value,"%d/%m/%Y")
                min_value = datetime.strptime(min_value,"%d/%m/%Y")
                start_value = datetime.strptime(start_value,"%d/%m/%Y")
                if max_value < min_value:
                    errors += li % "Max value must be greater than min value."
                if max_value<start_value or min_value>start_value:
                    errors += li % "Start value must be between max value and min value."
            except BaseException as e:
                errors += li % "Max,Min and start value must be invalid date"
        if question_type == "multiplechoice":
            pass
        if question_type == "checkbox":
            max_checked = attributes[0]
            min_checked = attributes[1]
            no_of_selections = len(selections) - 1
            try:
                max_checked = int(max_checked)
                min_checked = int(min_checked)
                if max_checked < 0 or max_checked > no_of_selections:
                    errors += li % "%s -- Please enter in an integer in [0,%d], %d provided." % (
                        "Max checked", no_of_selections, max_checked)
                if min_checked < 0 or min_checked > no_of_selections:
                    errors += li % "%s -- Please enter in an integer in [0,%d], %d provided." % (
                        "Min checked", no_of_selections, min_checked)
                if max_checked < min_checked:
                    errors += li % "Max checked must be greater than min checked."
            except BaseException as e:
                errors += li % "Max & Min checked must be integer in [0, %d]" % no_of_selections
        dict = {"errors": errors}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    return error_jump(request)

def create_survey(request):
    if request.POST:
        survey_title = request.POST.get("survey_title")
        survey_description = request.POST.get("survey_description")
        if survey_title == "New Survey(Click to change)":
            survey_title = "No title"
        if survey_description == "Add description here" or survey_description == "Click here to add...":
            survey_description = ""
        publishBool = request.POST.get("publishBool")
        survey = Survey(title=survey_title)
        survey.description = survey_description
        creator = User.objects.get(id = int(request.POST.get( "creatorID")))
        survey.user = creator
        survey.theme_name = request.POST.get("theme_name")
        deadline = request.POST.get("survey_deadline")
        survey.deadline = datetime.strptime(deadline.strip(), "%d/%m/%Y")
        survey.save()
        collaborators = request.POST.get("collaborators")
        collaborators = collaborators.split(",")
        try:
            collaborators.remove("")
        except BaseException as e:
            pass
        for collaborator_id in collaborators:
            collaboration = Collaboration()
            collaboration.user = User.objects.get(id = int(collaborator_id))
            collaboration.survey = survey
            collaboration.is_active = True
            collaboration.save()

        if publishBool == 'true':
            survey.is_published = True
            survey.save()
        surveyID = survey.id
        dict = {"surveyID": surveyID, "survey_key": survey.key}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    return error_jump(request)
from django.http import Http404

@login_required()
def delete_survey(request, survey_key=""):
    if request.POST:
        surveyID = int(request.POST.get("surveyID"))
        survey = Survey.objects.get(id=surveyID)
        survey.delete()
        dict = {}
        return HttpResponse(simplejson.dumps(dict),mimetype='application/javascript')
    else:
        try:
            survey = Survey.objects.get(key=survey_key)
        except Survey.DoesNotExist:
            raise Http404
        if request.user == survey.user or survey.is_collaborator(request.user):
            survey_title = survey.title
            survey.delete()
            messages.success(request, 'Survey "%s deleted" successfully' % survey_title)
        else:
            return error_jump(request,"unauthorized")
        return HttpResponseRedirect('/account')
    return error_jump(request)

def save_survey(request, surveyID):
    if request.POST:
        question_type = request.POST.get("question_type")
        question_no = request.POST.get("question_no")
        question_helptext = request.POST.get("question_helptext")
        is_required = request.POST.get("is_required")
        if question_helptext == "Click here to add...":
            question_helptext == ""
        question_title = request.POST.get("question_title")
        selections = request.POST.get("selections")
        attributes = request.POST.get("attributes")
        if int(surveyID) == 0:
            survey = Survey(title="no title")
            survey.save()
            surveyID = survey.id
        if question_type == "paragraph":
            question = ParagraphQuestion()
        elif question_type == "numeric":
            question = NumericQuestion()
        elif question_type == "multiplechoice":
            question = MultipleChoiceQuestion()
        elif question_type == "checkbox":
            question = CheckboxQuestion()
        elif question_type == "scale":
            question = ScaleQuestion()
        elif question_type == "text":
            question = TextQuestion()
        elif question_type == "date":
            question = DateQuestion()
        else:
            return
        question.survey = Survey.objects.get(id=surveyID)
        question.id_in_survey = question_no
        question.title = question_title.strip()
        question.help_text = question_helptext
        question.max_no_characters = 0
        if is_required == 'true':
            question.is_required = True
        else:
            question.is_required = False
        question.save()
        if question_type == "paragraph":
            attributes_list = attributes.split("@#@")
            question.max_no_characters = int(attributes_list[0])
        elif question_type == "numeric":
            attributes_list = attributes.split("@#@")
            question.max_value = float(attributes_list[0])
            question.min_value = float(attributes_list[1])
        elif question_type == "multiplechoice":
            choices = selections.split("@#@")
            choices.pop()
            count = 0
            for choice_label in choices:
                count += 1
                choice = MultipleChoice()
                choice.question = question
                choice.label = choice_label
                choice.id_in_question = count
                choice.save()
        elif question_type == "checkbox":
            attributes_list = attributes.split("@#@")
            question.max_checked = int(attributes_list[0])
            question.min_checked = int(attributes_list[1])
            choices = selections.split("@#@")
            choices.pop()
            count = 0
            for choice_label in choices:
                count += 1
                choice = CheckboxChoice()
                choice.question = question
                choice.label = choice_label
                choice.id_in_question = count
                choice.save()
        elif question_type == "scale":
            attributes_list = attributes.split("@#@")
            question.max_value = float(attributes_list[0])
            question.min_value = float(attributes_list[1])
            question.increment = float(attributes_list[2])
        elif question_type == "date":
            attributes_list = attributes.split("@#@")
            question.min_value = datetime.strptime(attributes_list[0].strip(),"%d/%m/%Y")
            question.max_value = datetime.strptime(attributes_list[1].strip(),"%d/%m/%Y")
            question.start_value = datetime.strptime(attributes_list[2].strip(),"%d/%m/%Y")
        elif question_type == "text":
            attributes_list = attributes.split("@#@")
            question.max_no_characters = int(attributes_list[0])
        else:
            return
        question.save()
        dict = {"surveyID": surveyID}
        return HttpResponse(simplejson.dumps(dict), mimetype='application/javascript')
    return error_jump(request)


def respondent(request):
    return render_to_response('respondent.html', RequestContext(request))

from survey.models import Survey

def view_survey(request, view_key, *args, **kwargs):
    survey = Survey.objects.get(key=view_key)
    questions = survey.questions.order_by('id_in_survey')
    request.session['dt_start'] = datetime.now()
    theme_name = survey.theme_name
    deadline = survey.deadline
    now = datetime.now()
    expired = False
    if now > deadline:
        expired = True
    deadline = deadline.strftime("%A, %B %d, %Y   %H:%M:%S")
    if not theme_name:
        theme_name = "grass"
    dict = {'survey': survey, 'questions': questions, 'dt_start': datetime.now(), 'theme_name': theme_name,
            'deadline': deadline, 'expired': expired}
    return render_to_response('respondent.html', dict, RequestContext(request))

#def view_survey(request, view_key, *args, **kwargs):
# #   survey = Survey.objects.get(id = view_key)
#    survey = Survey.objects.get(key = view_key)
#    questions = survey.questions.order_by('id_in_survey')
#    return render_to_response('respondent.html', {'survey' : survey, 'questions' : questions}, RequestContext(request))

def error_jump(request, error_type="404"):
    message = ""
    next_link = ""
    if error_type == "not_login":
        message = "Sorry, please log in before do it."
        next_link = "/account/login/"
    if error_type == "unauthorized":
        message = "Sorry, you are unauthorized to do this. Please check again."
        next_link = "/"
    if error_type == "404":
        message = "Sorry, the page is not found. "
        next_link = "/"
    if error_type == "edit_published_survey":
        message = "Sorry, you cannot edit a published survey"
        next_link = "/"
    if error_type == "response_unpublished_survey":
        message = "Sorry, the survey hasn't be published."
        next_link = "/"
    dict = {'message': message, 'next_link': next_link}
    return render_to_response('error.html', dict, RequestContext(request))


def complete(request, view_key=""):
    return render_to_response('complete.html', {"view_key": view_key}, RequestContext(request))


def is_valid_email(email):
    return True if email_re.match(email) else False


def share_survey(request):
    survey_id = request.POST.get('survey_id');
    email_data = request.POST.get('collaborators');
    owner_message = request.POST.get('owner_message');

    success_emails = []
    fail_emails = []

    emails = [e.strip() for e in email_data.split(',')]

    for e in emails:
        if is_valid_email(e):
            success_emails.append(e)
        else:
            fail_emails.append(e)

    survey = Survey.objects.get(id=survey_id)
    survey_url = "http://%s%s" % (get_current_site(request).domain, survey.get_absolute_url())

    if request.user.first_name and request.user.last_name:
        message = "%s %s (%s) invites you to take the survey.\n\nFollow this link to open the survey:\n%s\n\n%s" % (
        request.user.first_name, request.user.last_name, request.user.email, survey_url, owner_message)
    else:
        message = "%s (%s) invites you to take the survey.\n\nFollow this link to open the survey:\n%s\n\n%s" % (
        request.user.username, request.user.email, survey_url, owner_message)

    send_mail('You are invited to do a survey', message, "noreply@%s" % get_current_site(request).domain,
        success_emails)

    if len(fail_emails) > 0:
        messages.error(request, "Email %s is invalid" % (', ').join(fail_emails))
    if len(success_emails) > 0:
        messages.success(request, 'You have successfully share with %s' % (', ').join(success_emails))

    return HttpResponseRedirect("/account")

