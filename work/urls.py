"""
URL configuration for work project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from workapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('', lambda request: render(request, 'get_started.html'), name='get_started'),
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('course/<int:course_id>/subject/create/', AddSubjectView.as_view(), name='add_subject'),
    path('course/<int:course_id>/subject/opinion/create', AddOpinionView.as_view(), name='add_opinion'),
    path('course/<int:course_id>/subject/opinion/<int:opinion_id>/update', UpdateOpinionView.as_view(), name='update_opinion'),
    path('course/<int:course_id>/subject/opinion/<int:opinion_id>/delete', DeleteOpinionView.as_view(), name='delete_opinion'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/create/', AddTestView.as_view(), name='add_test'),
    path('course/<int:course_id>/subject/<int:subject_id>/questionnaire/create/', AddQuestionnaireView.as_view(), name='add_questionnaire'),
    path('course/<int:course_id>/subject/<int:subject_id>/questionnaire/', subject_questionnaire_view, name='sub_quest'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/<int:test_id>/question/create/', AddQuestionView.as_view(), name='add_question'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/<int:test_id>/question/<int:question_id>/answer/create/', AddAnswersView.as_view(), name='answer_question'),
    path('answer/', answer_request_user_view, name='answer_question_user'),
    path('thanks/', thanking_view, name='thanks'),
    path('cv/<int:cv_id>/experience/create/', AddExperienceView.as_view(), name='add_experience'),
    path('cv/<int:cv_id>/hobby/create/', AddHobbyView.as_view(), name='add_hobby'),
    path('cv/<int:cv_id>/skill/create/', AddSkillsView.as_view(), name='add_skill'),
    path('cv/<int:cv_id>/education/create/', AddEducationView.as_view(), name='add_education'),
    path('portfolio/<int:portfolio_id>/project/create/', AddProjectView.as_view(), name='add_project'),
    path('portfolio/<int:portfolio_id>/link/create/', AddLinkView.as_view(), name='add_link'),
    path('offer_jobs/<int:offers_job_id>/offer_jobs_user/', AddOfferJobsUserView.as_view(), name='add_offer_jobs_user'),
    path('offer_jobs/<int:offers_job_id>/offer_jobs_user/update/', UpdateOfferJobsUserView.as_view(), name='update_offer_jobs_user'),
    path('course/<int:course_id>/subject/<int:subject_id>/update/', UpdateSubjectView.as_view(), name='update_subject'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/<int:test_id>/update/', UpdateTestView.as_view(), name='update_test'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/<int:test_id>/question/<int:question_id>/update/', UpdateQuestionView.as_view(), name='update_question'),
    path('course/<int:course_id>/subject/<int:subject_id>/delete/', DeleteSubjectView.as_view(), name='delete_subject'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/<int:test_id>/delete/', DeleteTestView.as_view(), name='delete_test'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/<int:test_id>/question/<int:question_id>/delete/', DeleteQuestionView.as_view(), name='delete_question'),
    path('cv/<int:cv_id>/experience/<int:experience_id>/update/', UpdateExperienceView.as_view(), name='update_experience'),
    path('cv/<int:cv_id>/hobby/<int:hobby_id>/update/', UpdateHobbyView.as_view(), name='update_hobby'),
    path('cv/<int:cv_id>/skill/<int:skill_id>/update/', UpdateSkillsView.as_view(), name='update_skill'),
    path('cv/<int:cv_id>/education/<int:education_id>/update/', UpdateEducationView.as_view(), name='update_education'),
    path('cv/', AddCVView.as_view(), name='add_cv'),
    path('business/<int:business_id>/hr/', AddHRView.as_view(), name='add_hr'),
    path('business/<int:business_id>/hr/<int:hr_id>/update/', UpdateHRView.as_view(), name='update_hr'),
    path('business/<int:business_id>/hr/<int:hr_id>/offer_jobs/create/', AddOfferJobsView.as_view(), name='add_offer_jobs'),
    path('offer_jobs/<int:offer_jobs_id>/delete/', DeleteOffersJobsView.as_view(), name='delete_offer_jobs'),
    path('cv/<int:cv_id>/update/', UpdateCVView.as_view(), name='update_cv'),
    path('business/', AddBusinessView.as_view(), name='add_business'),
    path('business/<int:business_id>/update/', UpdateBusinessView.as_view(), name='update_business'),
    path('course/', AddCourseView.as_view(), name='add_course'),
    path('course/<int:course_id>/update/', UpdateCourseView.as_view(), name='update_course'),
    path('course/<int:course_id>/delete/', DeleteCourseView.as_view(), name='delete_course'),
    path('portfolio/', AddPortfolioView.as_view(), name='add_portfolio'),
    path('portfolio/<int:portfolio_id>/update/', UpdatePortfolioView.as_view(), name='update_portfolio'),
    path('portfolio/<int:portfolio_id>/project/<int:project_id>/update/', UpdateProjectView.as_view(), name='update_project'),
    path('portfolio/<int:portfolio_id>/link/<int:link_id>/update/', UpdateLinkView.as_view(), name='update_link'),
    path('search/business/', search_business, name='search_business'),
    path('search/offers-job/', search_offers_job, name='search_offers_job'),
    path('index/', accepted_offers_job_user, name='index'),
    path('course/user/', course_user, name='course_user'),
    path('offers_job/user/', offers_job_user, name='offers_job_user'),
    path('offers_job/user/created/', offers_job_created_by_user, name='offers_job_created_by_user'),
    path('offers_job/user/<int:offer_id>/', offer_user_to_hr, name='offer_user_to_hr'),
    path('business/<int:business_id>/hr/view/', hr_to_business_view, name='hr_to_business_view'),
    path('search/courses/', search_course_view, name='search_course_view'),
    path('course/<int:course_id>/subject/', subject_to_course_view, name='subject_to_course_view'),
    path('course/certificates/', course_to_certificate_view, name='course_to_certificate_view'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/', subject_to_test_view, name='subject_to_test_view'),
    path('course/<int:course_id>/subject/<int:subject_id>/test/<int:test_id>/questions/', test_to_question_view, name='test_to_question_view'),
    path('course/<int:subject_id>/certificate/', search_stores, name='search_stores'),
    path('course/user/test-scores/', test_score_to_user_view, name='test_score_to_user_view'),
    path('search/portfolio/', search_portfolio, name='search_portfolio'),
    path('search/cv/', search_cv, name='search_cv'),
    path('portfolio/user/', portfolio_to_user_view, name='portfolio_to_user_view'),
    path('cv/user/', cv_to_user_view, name='cv_to_user_view'),
    path('cv/<int:cv_id>/', cv_to_id_view, name='cv_to_id_view'),
    path('business/<int:business_id>/hr/<int:hr_id>/offer_jobs/', offer_jobs_id, name='read_offer_jobs'),
    path('business/<int:business_id>/hr/<int:hr_id>/offer_jobs/<int:offer_id>/', offer_jobs_id_one, name='read_offer_jobs_one'),
    path('cv/user/experience/', my_cv_experience_view, name='my_cv_experience_view'),
    path('cv/user/hobby/', my_cv_hobby_view, name='my_cv_hobby_view'),
    path('cv/user/education/', my_cv_education_view, name='my_cv_education_view'),
    path('cv/user/skill/', my_cv_skills_view, name='my_cv_skills_view'),
    path('cv/<int:cv_id>/experience/', cv_id_view, name='cv_id_view'),
    path('cv/<int:cv_id>/hobby/', cv_hobby_view, name='cv_hobby_view'),
    path('cv/<int:cv_id>/education/', cv_education_view, name='cv_education_view'),
    path('cv/<int:cv_id>/skill/', cv_skills_view, name='cv_skills_view'),
    path('portfolio/<int:portfolio_id>/project/', portfolio_projects_view, name='portfolio_projects_view'),
    path('portfolio/user/projects/', my_portfolio_projects_view, name='my_portfolio_projects_view'),
    path('portfolio/user/links/', my_portfolio_links_view, name='my_portfolio_links_view'),
    path('portfolio/<int:portfolio_id>/link/', portfolio_links_view, name='portfolio_links_view'),
    path('transmition/', AddTransmitionView.as_view(), name='add_transmition'),
    path('transmition/<int:transmition_id>/update', UpdateTransmitionView.as_view(), name='update_transmition'),
    path('transmition/<int:transmition_id>/delete', DeleteTransmitionView.as_view(), name='delete_transmition'),
    path('transmition/<int:transmition_id>/comment', comments_transmition_view, name='comments_transmition'),
    path('transmition/<int:transmition_id>/comment/create', AddCommentView.as_view(), name='add_comment'),
    path('transmition/<int:transmition_id>/comment/<int:comment_id>/update', UpdateCommentView.as_view(), name='update_comment'),
    path('transmition/<int:transmition_id>/comment/<int:comment_id>/delete', DeleteCommentView.as_view(), name='delete_comment'),
 ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
