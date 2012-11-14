from survey.models import *
from datetime import datetime
from django.test import TestCase
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Min, Max, Avg, Count
#from survey.views import response_demography_to_chart


from django.test.client import Client

class SurveyTest(TestCase):
    def setUp(self):
        #set up survey
        self.survey = Survey(title='Test survey')
        self.user = User()
        self.user.save()
        self.survey.user = self.user
        self.survey.save()

        # Q1. Multiple choice (id_in_response=0)
        mcq = MultipleChoiceQuestion(type='multiplechoice',
            title='A test for Multiple choice question',
            id_in_survey=0,
            is_required=True,
            survey=self.survey
        )
        mcq.save()

        mc1 = MultipleChoice(label='test label1', id_in_question=0, question=mcq)
        mc1.save()
        mc2 = MultipleChoice(label='test label2', id_in_question=1, question=mcq)
        mc2.save()

        mc3 = MultipleChoice(label='test label3', id_in_question=2, question=mcq)
        mc3.save()

        mc4 = MultipleChoice(label='test label4', id_in_question=3, question=mcq)
        mc4.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='multiplechoice', id_in_response=0, value='0')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='multiplechoice', id_in_response=0, value='1')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='multiplechoice', id_in_response=0, value='1')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 9, 7))
        response.save()
        answer = Answer(response=response, type='multiplechoice', id_in_response=0, value='2')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='multiplechoice', id_in_response=0, value='2')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 20))
        response.save()
        answer = Answer(response=response, type='multiplechoice', id_in_response=0, value='2')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 20))
        response.save()
        answer = Answer(response=response, type='multiplechoice', id_in_response=0, value='3')
        answer.save()


        # Q2. Numeric question (id_in_response=1)

        nq = NumericQuestion(type='numeric',
            title='A test for numeric question',
            id_in_survey=1,
            is_required=True,
            min_value=0.0,
            max_value=100.0,
            survey=self.survey)

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='numeric', id_in_response=1, value='1.0')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='numeric', id_in_response=1, value='2.0')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='numeric', id_in_response=1, value='3.0')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 19))
        response.save()
        answer = Answer(response=response, type='numeric', id_in_response=1, value='4.0')
        answer.save()

        # Q3. Text question (id_in_response=2)

        tq = TextQuestion(type='text',
            title='A test for text question',
            id_in_survey=2,
            is_required=True,
            survey=self.survey)

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime.now())
        response.save()
        answer = Answer(response=response, type='text', id_in_response=2, value='A sample text for text question')
        answer.save()

        cq = CheckboxQuestion(type='checkbox',
            title='A test for checkbox question',
            id_in_survey=3,
            max_checked=4,
            min_checked=1,
            is_required=True,
            survey=self.survey)
        cq.save()

        cq1 = CheckboxChoice(label='test label1', id_in_question=0, question=cq)
        cq1.save()
        cq2 = CheckboxChoice(label='test label2', id_in_question=1, question=cq)
        cq2.save()
        cq3 = CheckboxChoice(label='test label3', id_in_question=2, question=cq)
        cq3.save()
        cq4 = CheckboxChoice(label='test label4', id_in_question=3, question=cq)
        cq4.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 28))
        response.save()
        answer = Answer(response=response, type='checkbox', id_in_response=3, value='0')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 29))
        response.save()
        answer = Answer(response=response, type='checkbox', id_in_response=3, value='3')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 27))
        response.save()
        answer = Answer(response=response, type='checkbox', id_in_response=3, value='2')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 28))
        response.save()
        answer = Answer(response=response, type='checkbox', id_in_response=3, value='1')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 28))
        response.save()
        answer = Answer(response=response, type='checkbox', id_in_response=3, value='1')
        answer.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 28))
        response.save()
        answer = Answer(response=response, type='checkbox', id_in_response=3, value='3')
        answer.save()

        sq = ScaleQuestion(type='scale',
            title='A test for scale question',
            id_in_survey=4,
            start=1,
            end=5,
            label_start="Strongly Agree",
            label_end="Strongly Disagree",
            survey=self.survey)
        sq.save()

        response = Response(survey=self.survey, dt_start=datetime.now(), dt_end=datetime(2012, 10, 28))
        response.save()
        answer = Answer(response=response, type='scale', id_in_response=4, value='1')
        answer.save()


    def test_multiple_choice(self):
        # 1 response for choice 0, 2 response for choice 1, 3 responses for choice 2, 1 response for choice 3

        queryset_answers = Answer.objects.filter(response__survey=self.survey, id_in_response=0)
        self.assertEqual(queryset_answers.filter(value__exact=0).count(), 1)
        self.assertEqual(queryset_answers.filter(value__exact=1).count(), 2)
        self.assertEqual(queryset_answers.filter(value__exact=2).count(), 3)
        self.assertEqual(queryset_answers.filter(value__exact=3).count(), 1)


    def test_numeric(self):
        queryset_answers = Answer.objects.filter(response__survey=self.survey, id_in_response=1)
        self.assertEqual(queryset_answers.aggregate(Min('value'))['value__min'], 1.0)
        self.assertEqual(queryset_answers.aggregate(Max('value'))['value__max'], 4.0)
        self.assertEqual(queryset_answers.aggregate(Avg('value'))['value__avg'], 2.5)

    def test_text(self):
        queryset_answers = Answer.objects.filter(response__survey=self.survey, id_in_response=2)
        self.assertEqual(queryset_answers[0].value, 'A sample text for text question')

    def test_check_box(self):
        queryset_answers = Answer.objects.filter(response__survey=self.survey, id_in_response=3)
        self.assertEqual(queryset_answers.filter(value__exact=0).count(), 1)
        self.assertEqual(queryset_answers.filter(value__exact=1).count(), 2)
        self.assertEqual(queryset_answers.filter(value__exact=2).count(), 1)
        self.assertEqual(queryset_answers.filter(value__exact=3).count(), 2)

    def test_scale(self):
        queryset_answers = Answer.objects.filter(response__survey=self.survey, id_in_response=4)
        self.assertEqual(str(queryset_answers[0].value), '1')




