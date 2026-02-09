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
    path('thanks/', thanking_view, name='thanks'),
    path('portfolio/<int:portfolio_id>/link/create/', AddLinkView.as_view(), name='add_link'),
    path('course/<int:course_id>/subject/<int:subject_id>/', subject_to_course_id_view, name='subject_id'),
    path('course/<int:course_id>/subject/<int:subject_id>/update/', UpdateSubjectView.as_view(), name='update_subject'),
    path('course/<int:course_id>/subject/<int:subject_id>/delete/', DeleteSubjectView.as_view(), name='delete_subject'),
    path('course/', AddCourseView.as_view(), name='add_course'),
    path('course/<int:course_id>/update/', UpdateCourseView.as_view(), name='update_course'),
    path('course/<int:course_id>/delete/', DeleteCourseView.as_view(), name='delete_course'),
    path('portfolio/', AddPortfolioView.as_view(), name='add_portfolio'),
    path('portfolio/<int:portfolio_id>/update/', UpdatePortfolioView.as_view(), name='update_portfolio'),
    path('portfolio/<int:portfolio_id>/delete/', DeletePortfolioView.as_view(), name='delete_portfolio'),
    path('portfolio/<int:portfolio_id>/link/<int:link_id>/update/', UpdateLinkView.as_view(), name='update_link'),
    path('index/', accepted_offers_job_user, name='index'),
    path('course/user/', course_user, name='course_user'),
    path('search/courses/', search_course_view, name='search_course_view'),
    path('course/<int:course_id>/subject/', subject_to_course_view, name='subject_to_course_view'),
    path('search/portfolio/', search_portfolio, name='search_portfolio'),
    path('portfolio/user/', portfolio_to_user_view, name='portfolio_to_user_view'),
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
