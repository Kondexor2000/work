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
    path('thanks/', thanking_view, name='thanks'),
    path('portfolio/<int:portfolio_id>/link/create/', AddLinkView.as_view(), name='add_link'),
    path('portfolio/', AddPortfolioView.as_view(), name='add_portfolio'),
    path('portfolio/<int:portfolio_id>/update/', UpdatePortfolioView.as_view(), name='update_portfolio'),
    path('portfolio/<int:portfolio_id>/delete/', DeletePortfolioView.as_view(), name='delete_portfolio'),
    path('test/create/', AddTestView.as_view(), name='add_test'),
    path('test/', test_to_user_view, name='test_read'),
    path('test/<int:test_id>/', test_score_view, name='test_score'),
    path('test/<int:test_id>/question/', test_questions_view, name='question_read'),
    path('test/<int:test_id>/update/', UpdateTestView.as_view(), name='update_test'),
    path('test/<int:test_id>/delete/', DeleteTestView.as_view(), name='delete_test'),
    path('test/<int:test_id>/question/create/', AddQuestionView.as_view(), name='add_question'),
    path('test/<int:test_id>/question/<int:question_id>/update/', UpdateQuestionView.as_view(), name='update_question'),
    path('test/<int:test_id>/question/<int:question_id>/delete/', DeleteQuestionView.as_view(), name='delete_question'),
    path('test/<int:test_id>/question/<int:question_id>/answer/', AddAnswerView.as_view(), name='add_answer'),
    path('recruter/', AddOfferJobsUserView.as_view(), name='add_apply_job'),
    path('portfolio/<int:portfolio_id>/link/<int:link_id>/delete/', DeleteLinkView.as_view(), name='update_link'),
    path('index/', accepted_offers_job_user, name='index'),
    path('index/job', recruter_to_user_view, name='recruter_to_user_view'),
    path('search/portfolio/', search_portfolio, name='search_portfolio'),
    path('portfolio/user/', portfolio_to_user_view, name='portfolio_to_user_view'),
    path('portfolio/user/links/', my_portfolio_links_view, name='my_portfolio_links_view'),
    path('portfolio/<int:portfolio_id>', portfolio_to_id_view, name='portfolio_id_view'),
    path('portfolio/<int:portfolio_id>/link/', portfolio_links_view, name='portfolio_links_view'),
    path('transmition/', AddTransmitionView.as_view(), name='add_transmition'),
    path('transmition/<int:transmition_id>/update', UpdateTransmitionView.as_view(), name='update_transmition'),
    path('transmition/<int:transmition_id>/delete', DeleteTransmitionView.as_view(), name='delete_transmition'),
    path('transmition/<int:transmition_id>/comment', comments_transmition_view, name='comments_transmition'),
    path('transmition/<int:transmition_id>/comment/create', AddCommentView.as_view(), name='add_comment'),
    path('transmition/<int:transmition_id>/comment/<int:comment_id>/update', UpdateCommentView.as_view(), name='update_comment'),
    path('transmition/<int:transmition_id>/comment/<int:comment_id>/delete', DeleteCommentView.as_view(), name='delete_comment'),
 ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
