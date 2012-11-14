# included in q_view.py

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django import http
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from survey.util import get_datatables_records
from survey.forms import RegistrationForm
from survey.forms import RegistrationForm, EditProfileForm
from django.contrib import auth
from django.contrib.auth import authenticate, login, logout
from survey.models import UserProfile
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import simplejson as json
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.contrib.sites.models import get_current_site
#<!-------->
import sha
from django.core.mail import send_mail

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            new_user = form.save()
            new_user.is_active = False
            new_user.save()

            confirmation_code = sha.new(new_user.username).hexdigest()
            profile = UserProfile(user=new_user, confirmation_code=confirmation_code[0:9])
            profile.save()

            send_registration_confirmation(new_user)

            return render_to_response("account/registration_complete.html")
    else:
        form = RegistrationForm()
    return render_to_response("account/register.html", {'form': form}, context_instance=RequestContext(request))

from django.contrib.sites.models import Site

def send_registration_confirmation(user):
    profile = user.get_profile()
    current_site = Site.objects.get_current()
    subject, from_email, to = "Survey account activation", 'no-reply@localhost', user.email

    link = "http://%s/account/confirm/%s" % (current_site.domain, str(profile.confirmation_code) + "/" + user.username)
    text_content = "Hello and welcome to Stardom Survey. We have sent you this e-mail because you recently registered on Stardom Survey. Please click on the following link to activate your account. %s" % link
    html_content = "Hello and welcome to Stardom Survey.<br />We have sent you this e-mail because you recently registered on Stardom Survey.<br />Please click on the following link to activate your account.<br /><a href='%s'>%s</a>" % (link, link)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')

        # Login using username or email
        user = auth.authenticate(username=username_or_email, password=password)
        if user is None:
            user = auth.authenticate(email=username_or_email, password=password)

        # User must have activated their account through email
        if user is not None and user.is_active:
            # Correct password, and the user is marked "active"
            auth.login(request, user)
            # Redirect to a success page.
            if user.is_superuser:
                return HttpResponseRedirect("/admin")
            else:
                return HttpResponseRedirect("/account")
        else:
            # Show an error page
            return render_to_response("account/login.html", {'error': True}, context_instance=RequestContext(request))
    else:
        return render_to_response("account/login.html", {}, context_instance=RequestContext(request))


def confirm(request, confirmation_code, username):
    user = User.objects.get(username=username)
    profile = user.get_profile()
    if profile.confirmation_code == confirmation_code:
        user.is_active = True
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, user)
    return render_to_response("account/activation_complete.html", {}, context_instance=RequestContext(request))


def check_email(request):
    email = request.GET['email']
    try:
        user = User.objects.get(email=email)
        return HttpResponse('false')
    except User.DoesNotExist:
        return HttpResponse('true')


def check_username(request):
    username = request.GET['username']
    try:
        user = User.objects.get(username=username)
        return HttpResponse('false')
    except User.DoesNotExist:
        return HttpResponse('true')

@login_required()
def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect("/")

@login_required()
def change_password_view(request):
    errors = []

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not request.user.check_password(old_password):
            errors.append("Your old password is wrong.")

        if len(password1) == 0:
            errors.append("New password field cannot be empty.")
        elif password1 != password2:
            errors.append("The two password fields didn't match.")

        if old_password == password1:
            errors.append("New password cannot be same as old password.")

        if len(errors) > 0:
            return render_to_response("account/change_password.html", {'errors': errors},
                context_instance=RequestContext(request))
        else:
            request.user.set_password(password1)
            request.user.save()
            messages.success(request, "You have successfully changed your password")
            return HttpResponseRedirect("/")
    else:
        return render_to_response("account/change_password.html", {'errors': errors},
            context_instance=RequestContext(request))

@login_required
def edit_profile(request):
    form = EditProfileForm()

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user.get_profile())
        if form.is_valid():
            profile = form.save()
            messages.success(request, "You have successfully edited your profile")
            return HttpResponseRedirect("/")
    else:
        form = EditProfileForm(instance=request.user.get_profile())

    return render_to_response("account/edit_profile.html", {'form': form}, context_instance=RequestContext(request))


def get_users_list_index(request):
    #prepare the params
    return render_to_response("account/display_users.html", locals(), context_instance=RequestContext(request))


def get_users_list(request):
    #prepare the params
    #initial querySet
    querySet = User.objects.all()
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {0: 'username', 1: 'first_name', 2: 'last_name', 3: 'email'}
    #path to template used to generate json (optional)

    jsonTemplatePath = r'account/json_userlist'

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, jsonTemplatePath)


def users_listing(request):
    user_list = User.objects.all()
    paginator = Paginator(user_list, 2, 0, True) # Show 25 contacts per page
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
    # If page is not an integer, deliver first page.
        users = paginator.page(1)
    except EmptyPage:
    # If page is out of range (e.g. 9999), deliver last page of results.
        users = paginator.page(paginator.num_pages)

    return render_to_response('account/display_users.html', {"users": users})

