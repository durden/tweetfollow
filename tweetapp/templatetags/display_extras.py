from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='full_name')
def full_name(user):
    return '%s (%s)' % (user.screen_name, user.name)


@register.filter(name='twitter_link')
def twitter_link(user):
    link = '<a href="http://www.twitter.com/%s">%s</a>' % \
            (user.screen_name, user.screen_name)
    return mark_safe(link)
