from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib import admin

import shortuuid

class Survey(models.Model):
    user = models.ForeignKey(User)
    key = models.CharField(max_length=22, null=False, unique=True)
    title = models.CharField(max_length=128, null=False)
    description = models.TextField(null=True)
    last_modified = models.DateTimeField(null=True)
    is_published = models.BooleanField(null=False, default=False)
    theme_name = models.CharField(max_length=255, null=True)
    deadline = models.DateTimeField(null=True)
    # create a unique id for the survey
    def __init__(self, *args, **kwargs):
        super(Survey, self).__init__(*args, **kwargs)
        if not self.key:
            self.key = shortuuid.uuid()
        if not self.last_modified:
            self.last_modified = datetime.now()
        if kwargs.get('title'):
            self.title = kwargs['title']

    def __unicode__(self):
        return 'id=%s, key = %s, user=%s, title = %s last_modified = %s is_published=%s' % (
            self.id,
            self.key,
            self.user.username,
            self.title,
            self.last_modified.strftime('%H:%M, %d %B, %Y'),
            self.is_published)

    def get_absolute_url(self):
        return "/view_survey/%s" % self.key

    def get_collaborators(self):
        collaborations = Collaboration.objects.filter(survey_id=self.id)
        users_ids = [c.user_id for c in collaborations]
        return User.objects.filter(id__in=users_ids)

    def get_collaboration(self):
        collaborations = Collaboration.objects.filter(survey_id=self.id)
        return collaborations

    def is_collaborator(self, user):
        if Collaboration.objects.filter(survey_id=self.id, user_id=user.id, is_active=True).exists():
            return True
        else:
            return False

    class Meta:
        ordering = ['id']


class Question(models.Model):
    '''base question class'''
    survey = models.ForeignKey(Survey, related_name='questions')
    id_in_survey = models.IntegerField()
    QUESTION_TYPE_CHOICES = (
        ('multiplechoice', 'MultipleChoiceQuestion'),
        ('checkbox', 'CheckboxQuestion'),
        ('paragraph', 'ParagraphQuestion'),
        ('scale', 'ScaleQuestion'),
        ('numeric', 'NumericQuestion'),
        ('date', 'DateQuestion'),
        ('text', 'TextQuestion')
    )
    type = models.CharField(choices=QUESTION_TYPE_CHOICES, max_length=25)
    title = models.CharField(max_length=500, null=False)
    help_text = models.CharField(max_length=500, null=True)
    is_required = models.BooleanField(default=False)

    def __unicode__(self):
        return 'No.%d, title=%s, type=%s, required=%s' % (self.id_in_survey, self.title, self.type, self.is_required)

    class Meta:
        ordering = ["id_in_survey"]




class ParagraphQuestion(Question):
    max_no_characters = models.IntegerField()

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.type = "paragraph"


class NumericQuestion(Question):
    min_value = models.FloatField(null=True)
    max_value = models.FloatField(null=True)

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.type = "numeric"

    def __unicode__(self):
        return 'title=%s, min=%f, max=%f' % (self.title, self.min_value, self.max_value)


class CheckboxQuestion(Question):
    max_checked = models.IntegerField(null=True)
    min_checked = models.IntegerField(null=True)

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.type = "checkbox"


class CheckboxChoice(models.Model):
    question = models.ForeignKey(CheckboxQuestion, related_name='choices')
    label = models.CharField(max_length=200)
    id_in_question = models.IntegerField()

    def __unicode__(self):
        return 'label%d: %s' % (self.id, self.label)


class MultipleChoiceQuestion(Question):
    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.type = "multiplechoice"


class MultipleChoice(models.Model):
    question = models.ForeignKey(MultipleChoiceQuestion, related_name='choices')
    label = models.CharField(max_length=200)
    id_in_question = models.IntegerField()

    def __unicode__(self):
        return 'label%d: %s' % (self.id_in_question, self.label)


class ScaleQuestion(Question):
    min_value = models.FloatField(null=True)
    max_value = models.FloatField(null=True)
    increment = models.FloatField(null=True)

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.type = "scale"

    def __unicode__(self):
        return 'title=%s, min=%s, max=%s' % (self.title, self.min_value, self.max_value)
class TextQuestion(Question):
    max_no_characters = models.IntegerField(null=True, max_length=255)

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.type = "text"

    def __unicode__(self):
        return 'title=%s, max_no_characters=%d' % (self.title, self.max_no_characters)
class DateQuestion(Question):
    min_value = models.DateField(null=True)
    max_value = models.DateField(null=True)
    start_value = models.DateField(null=True)

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.type = "date"

    def __unicode__(self):
        return 'title=%s, min=%s, max=%s' % (self.title, self.min_value, self.max_value)


class Response(models.Model):
    '''
        Each response has all the answers for the questions
    '''
    ip_address = models.IPAddressField(null=True)
    # start and end datetime for logging the response
    dt_start = models.DateTimeField(null=False)
    dt_end = models.DateTimeField(null=False)
    survey = models.ForeignKey(Survey, related_name="responses")

    def __unicode__(self):
        return 'Survey=%s, %s' % (self.survey.title, self.dt_end.strftime('%d %B'))

    class Meta:
        ordering = ['dt_end']


class Answer(models.Model):
    '''
        answer for each question
    '''

    response = models.ForeignKey(Response)
    # which answer in the response
    id_in_response = models.IntegerField()
    QUESTION_TYPE_CHOICES = (
        ('multiplechoice', 'MultipleChoiceQuestion'),
        ('checkbox', 'CheckboxQuestion'),
        ('paragraph', 'ParagraphQuestion'),
        ('text', 'TextQuestion'),
        ('scale', 'ScaleQuestion'),
        ('numeric', 'NumericQuestion'),
        ('date', 'DateQuestion'),
    )
    type = models.CharField(choices=QUESTION_TYPE_CHOICES, max_length=25)

    #   For Checkbox and Multiple Choice Questions,
    # the value if the list of the id of choices,
    # for example, if box 1,3 are checked, the value
    # will be '1,3', separated by colon.
    #
    #   For other text-bases question, the value
    # will simple be the string value of that answer,
    # for example, an value to the paragraph question
    # will be 'some paragraph here'


    value = models.TextField(null=True)

    def __unicode__(self):
        return 'Survey=%s, Question%d, type=%s, value=%s' % (
        self.response.survey.title, self.id_in_response, self.type, self.value)

    class Meta:
        ordering = ['id_in_response', 'value']


class UserProfile(models.Model):
    confirmation_code = models.CharField(max_length=20, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.CharField(max_length=20, blank=True, null=True)
    im_name = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(User)


class Collaboration(models.Model):
    user = models.ForeignKey(User)
    survey = models.ForeignKey(Survey)
    activation_code = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    date_sent = models.DateTimeField(null=False, auto_now_add=True)