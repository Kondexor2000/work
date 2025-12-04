# AI Coding Agent Instructions

This is a Django 4.2 professional profile and job marketplace web application built with class-based views, designed for managing user CVs, course education, job offers, and portfolio projects.

## Architecture Overview

**Tech Stack**: Django 4.2 + PostgreSQL/SQLite + Gunicorn + WhiteNoise

**Key Components**:
- **workapp/models.py**: 20+ domain models organized in 5 functional areas (authentication, HR/jobs, courses/education, tests/assessments, CV/portfolio)
- **workapp/views.py** (~1900 lines): Class-based views with `LoginRequiredMixin` for access control; pattern-driven CRUD operations
- **workapp/forms.py** (~350 lines): ModelForms + 8 modelformsets for inline multi-object editing (Questions, Subjects, Projects, Links, Experience, Skills, Hobbies, Education)
- **work/settings.py**: Environment-aware configuration (local PostgreSQL vs. cloud DATABASE_URL via dj_database_url)
- **workapp/signals.py**: Post-login IP logging via Django signals

## Critical Data Model Patterns

**1. User Extension Pattern** (across multiple models):
```python
# OneToOne relationships - each user can have ONE instance
CV(user: OneToOneField)
HR(user: OneToOneField)
```
⚠️ Creating duplicate CV/HR records will fail - validate `objects.filter(user=request.user).exists()` before creation.

**2. Nested Resource Hierarchy** (deep URL nesting):
- Course → Subject → Test → Questions → Answers
- Business → HR → OffersJob
- Portfolio → Projects/Links
- CV → Experience/Education/Skills/Hobbies

URL patterns use nested kwargs (e.g., `course_id`, `subject_id`, `test_id`). Always validate parent resource ownership in `dispatch()` or via model relationships.

**3. Many-to-Many Tag System** (Business, Course, Job, Portfolio):
- `TagBusiness`, `TagCourse`, `TagPortfolio` are reusable across multiple models
- Forms like `OfferJobsForm` support both selecting existing tags AND creating new ones via textarea input with validation

## Common Conventions

**View Pattern - LoginRequiredMixin + Template Check**:
```python
class AddSomethingView(LoginRequiredMixin, CreateView):
    form_class = SomethingForm
    template_name = 'add_something.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
```
Templates are validated at request time via `check_template()` utility. Always include this in new views that render templates.

**Form Validation Pattern - Tag Input Validation**:
- Check for duplicate tags with case-insensitive comparison: `TagBusiness.objects.filter(name__iexact=name).exists()`
- Raise `ValidationError` with list of strings for multiple errors
- Process M2M relationships in `save(commit=False)` pattern

**Formset Usage** (`modelformset_factory`):
Applied to enable "edit multiple related items inline". Common formsets: Questions, Projects, Links, Experience, Skills, Hobbies, Education.

## Deployment & Database Configuration

**Environment Variable Control**:
- `USE_LOCAL_DB=true` → PostgreSQL on localhost (development)
- `DATABASE_URL` (production) → Auto-parsed by `dj_database_url.config()`
- Defaults to SQLite if neither is set (shows console WARNING)

**SSL/HTTPS** (Local PostgreSQL mode):
```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True  # Enforced in local mode
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```
These are enabled only in local PostgreSQL mode. Cloud deployment may handle SSL upstream.

**Static Files**:
- WhiteNoise + CompressedManifestStaticFilesStorage (no separate S3 needed)
- Run `python manage.py collectstatic` before deployment

**Logging**:
- Console (DEBUG level) and file `django_app.log` (WARNING+)
- Loggers configured for 'django' and 'blogserviceapp'

## Key Files for Reference

| File | Purpose |
|------|---------|
| `workapp/models.py` | Full domain model definitions with relationships |
| `workapp/views.py` | All CRUD views and custom view logic |
| `workapp/forms.py` | ModelForms and formsets for bulk operations |
| `work/urls.py` | Deep nested URL patterns - study for adding new endpoints |
| `workapp/signals.py` | Login tracking via IP logging |
| `workapp/admin.py` | Admin registration for tag/category management |

## Polish (PL) Content Notes

- Model names and some comments in Polish (pl-PL conventions)
- Templates expect Polish placeholders (e.g., "Wybierz uczestników" - Choose participants)
- Custom messages use Polish: "Brak pliku .html" = "Missing .html file"

## Workflow for Adding New Features

1. **Add Model** in `models.py` - follow OneToOne/FK/M2M patterns established
2. **Create Form** in `forms.py` - use `ModelForm` + custom validation for tags
3. **Add CRUD Views** in `views.py` - extend `LoginRequiredMixin` + `CreateView`/`UpdateView`/`DeleteView` with template check
4. **Register Admin** in `admin.py` - minimal: `list_display` and `search_fields`
5. **Add URL Patterns** in `work/urls.py` - use nested syntax for parent-child relationships
6. **Create Templates** in `templates/` - Django template language (no framework required)

When modifying existing views: Always update parent resource access checks and formset handling if applicable.
