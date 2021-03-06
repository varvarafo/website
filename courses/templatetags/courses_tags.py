import datetime
from dateutil.relativedelta import relativedelta
def minus_one_week():
    return datetime.date.today() - relativedelta(weeks = 1)


from django import template
from courses.wagtail_hooks import SskStudentAttendeeMA
from courses.models import CourseAttendee



register = template.Library()

@register.inclusion_tag(
    'tags/next_dates.html'
)
def render_next_dates( page ):
    children = page.get_upcoming_courses()
    return {
        'page' : page,
        'children' : children
    }

@register.simple_tag()
def get_n_attendees( at, course ):
    return get_attendees_by_type(at, course).count()

@register.simple_tag()
def get_n_attendees_waitlist( at, course ):
    return get_waitlist_by_type(at, course).filter(is_validated = True).count()

@register.simple_tag()
def get_n_waitlist( course ):
    return CourseAttendee.objects.filter(
        waitlist_course = course,
        is_validated = True
    ).count()

@register.simple_tag()
def get_n_confirmed_attendees( at, course, payed = None ):
    qs = get_attendees_by_type(at, course).filter(is_validated = True)
    if payed is None:
        return qs.count()
    if payed is True:
        if at.price:
            return (
                qs.filter(amount__isnull = True).count() 
                + qs.filter(amount = 0).count() 
                + qs.filter(amount__gt = 0, payed = True).count()
            )
        else:
            return qs.count()
    if payed is False:
        if at.price:
            return qs.filter(amount__gt = 0, payed = False).count()
        else:
            return 0


@register.simple_tag()
def get_n_recent_unconfirmed_attendees_waitlist(at, course ):
    return (
        get_waitlist_by_type(at, course).filter(
            is_validated = False,
            add2course_mail_sent = True,
            add2course_mail_sent_at__gte = minus_one_week()
        ).count()
    )
    # TODO!


@register.simple_tag()
def get_n_recent_unconfirmed_attendees( at, course ):
    return (
        get_attendees_by_type(at, course).
        filter(
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__gte = minus_one_week()
        ).count()
    )

@register.simple_tag()
def get_n_total_recent_unconfirmed( course ):
    return (
        CourseAttendee.objects.
        filter(
            related_course = course,
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__gte = minus_one_week()
        ).count()
    )

@register.simple_tag()
def get_n_total_confirmed( course, payed = None ):
    n = 0
    for at in course.get_attendee_types().all():
        n = n + get_n_confirmed_attendees( at, course, payed )
    return n


@register.simple_tag()
def get_n_expired_unconfirmed_attendees( at, course ):
    return (
        get_attendees_by_type(at, course).
        filter(
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__lt = minus_one_week()
        ).count()
    )
@register.simple_tag()
def get_n_expired_unconfirmed( course ):
    return (
        CourseAttendee.objects.
        filter(
            related_course = course,
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__lt = minus_one_week()
        ).count()
    )

@register.simple_tag()
def get_attendees_by_type( at, course ):
    Kls = at.get_attendee_class()
    return Kls.objects.filter( related_course = course )

def get_waitlist_by_type( at, course ):
    Kls = at.get_attendee_class()
    return Kls.objects.filter( waitlist_course = course )

@register.simple_tag()
def get_value(obj, field):
    return getattr(obj,field)

@register.inclusion_tag(
    'tags/courses/specific_attendee_list.html',
    takes_context = True
)
def specific_attendee_list( context, at, instance ):
    additional_fields = []
    additional_fields_title = []
    if hasattr(at.get_attendee_class(), 'additional_admin_fields'):
        for f in at.get_attendee_class().additional_admin_fields:
            additional_fields.append(f[0])
            additional_fields_title.append(f[1])
            print('f is {}'.format(f[1]))

    context.update({
        'has_attendees' : get_n_attendees(at, instance) > 0,
        'attendees' : get_attendees_by_type(at, instance),
        'has_waitlist' : at.waitlist,
        'waitlist' : get_waitlist_by_type( at ,instance),
        'additional_fields' : additional_fields,
        'additional_fields_title' : additional_fields_title,
    })
    return context

@register.inclusion_tag(
    'tags/courses/attendee_in_list.html',
    takes_context = True
)
def attendee_in_list( context, course, Attendee ):
    print (Attendee)
    return {
        'available' : course.get_free_slots(Attendee.get_attendee_class()) > 0,
        'type' : Attendee,
        'page' : course,
        'request' : context['request']
    }

@register.inclusion_tag(
    'tags/courses/attendee_buttons.html',
    takes_context = True
)
def attendee_buttons( context, attendee ):
    ma = SskStudentAttendeeMA()
    BH = ma.get_button_helper_class()
    bh = BH(context['view'] , context['request'], modeladmin = ma )
    if attendee.related_course == context['instance'] :
        btns = bh.get_buttons_for_obj(
            attendee, 
            classnames_add=['button-small button-secondary'],
            exclude = ['delete_from_waitlist', 'add_to_course']
        )
    else:
        if attendee.add2course_mail_sent:
            exclude = ['delete', 'add_to_course']
        else:
            exclude = ['delete']
        btns = bh.get_buttons_for_obj(
            attendee, 
            classnames_add=['button-small button-secondary'],
            exclude = exclude
        )
#    print (context['view'].model)
#    buttonhelper = ButtonHelper( context['view'], context['request']) 
    context.update({'buttons' : btns })   
    return context
# @register.inclusion_tag(
#     'tags/registration_overview.html'
# )
# def render_registration_overview( page ):
#     context = { 'page' : page }
#     if page.start_date < date.today():
#         context['in_past'] = True
#         context['available'] = False
#         return context
    
#     plist = []
#     is_full = page.is_full()
    
#     for pt in PARTICIPANT_TYPES:
#         if not page.can_register( pt[0] ):
#             continue
#         dat = {
#             'ptype'   : pt[0],
#             'full'    : page.is_full_for( pt[0] ),
#             'waitlist': page.allows_waitlist_for( pt[0] ),
#             'price'   : page.get_prize ( pt[0] )
#         }
#         plist += [ dat ]
#     context['registration_list'] = plist

#     return context

# @register.filter
# def long_ptype( ptype ):
#     d = dict(PARTICIPANT_TYPES)
#     return d[ptype]

# @register.inclusion_tag(
#     'courses/rub_login_form.html'
# )
# def rub_login_form( form ):
#     return { 'form' : form }
# @register.inclusion_tag(
#     'courses/personal_data_form.html'
# )
# def personal_data_form( form ):
#     return { 'form' : form }
# @register.inclusion_tag(
#     'courses/student_data_form.html'
# )
# def student_data_form( form ):
#     return { 'form' : form }

# @register.inclusion_tag(
#     'courses/extended_personal_data_form.html'
# )
# def extended_personal_data_form( form ):
#     return { 'form' : form }

# @register.filter 
# def is_container( page ):
#     if issubclass( type(page), AbstractParticipantsContainer ):
#         return True
#     return False
