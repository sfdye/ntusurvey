from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from survey.models import Survey, Collaboration
from django.contrib.auth.models import User
import sha
from django.core.mail import send_mass_mail
from django.contrib import messages
from django.contrib.sites.models import get_current_site
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

import shortuuid
import time

@login_required
def invite(request):
    survey_id = request.POST.get('survey_id');
    collaborators_data = request.POST.get('collaborators');

    # Check whether is a valid request
    if request.method == 'POST' and (len(survey_id) > 0) and (len(collaborators_data) > 0):

        collaborators_username = [u.strip() for u in collaborators_data.split(',')]

        emails = []
        survey = Survey.objects.get(id=survey_id)
        success_user = []
        fail_user = []

        for username in collaborators_username:
            user = None
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass

            try:
                if user is None:
                    user = User.objects.get(email=username)

                if user.id == request.user.id:
                    messages.error(request, "You cannot add yourself as collaborator")
                else:
                    activation_code = shortuuid.uuid()
                    activation_code = activation_code[0:9]

                    if not Collaboration.objects.filter(user=user, survey=survey).exists():
                        Collaboration.objects.create(user=user, survey=survey, activation_code=activation_code)
                        emails.append(('Invitation for collaboration of survey', "http://%s/collaborate/accept/%s" % (get_current_site(request).domain, activation_code), 'noreply@localhost', [user.email]))
                        success_user.append(username)
                    else:
                        messages.error(request, "You have already added %s as collaborator" % username)
            except User.DoesNotExist:
                    fail_user.append(username)

        send_mass_mail(emails)

        if len(fail_user) > 0:
            messages.error(request, "User %s not found" % (', ').join(fail_user))
        if len(success_user) > 0:
            messages.success(request, 'You have successfully invite %s as collaborator' % (', ').join(success_user))

        return HttpResponseRedirect("/account")
    else:
        return HttpResponseRedirect("/account")

def accept(request, activation_code):
    try:
        collaboration = Collaboration.objects.get(activation_code=activation_code)
        collaboration.is_active = True
        collaboration.save()
        survey = Survey.objects.get(id=collaboration.survey_id)
        return render_to_response("collaborate_accept.html", { 'survey': survey }, context_instance=RequestContext(request))
    except Collaboration.DoesNotExist:
        messages.error(request, 'Sorry, the survey you trying to collaborate have been deleted by the owner')
        return HttpResponseRedirect("/")

@login_required
def delete(request, survey_id):
    Collaboration.objects.get(user_id=request.user.id, survey_id=survey_id ).delete();
    messages.success(request, 'You have successfully delete the survey')
    return HttpResponseRedirect("/account")

@login_required
def remove_collaborator(request, survey_id, user_id):
    # Only allow to remove their own survey collaborator
    try:
        Survey.objects.get(user_id=request.user.id, id=survey_id)
        Collaboration.objects.get(user_id=user_id, survey_id=survey_id).delete();
        messages.success(request, 'You have successfully remove the collaborator')
        return HttpResponseRedirect("/account")
    except Survey.DoesNotExist:
        return HttpResponseRedirect("/account")
