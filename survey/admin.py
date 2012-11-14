from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from survey.models import UserProfile

# Define an inline admin descriptor for UserProfile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


from survey.models import *
# Register other models



class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title','data_created')
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('type','title','help_text',"id_in_survey",'survey')

admin.site.register(Survey)
admin.site.register(Answer)
admin.site.register(Response)
admin.site.register(Question,QuestionAdmin)
admin.site.register(ParagraphQuestion)
admin.site.register(MultipleChoiceQuestion)
admin.site.register(NumericQuestion)
admin.site.register(CheckboxChoice)
admin.site.register(Collaboration)