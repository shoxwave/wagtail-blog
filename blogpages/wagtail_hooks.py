# add some setting for that snippet viewset
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail import hooks
from wagtail.admin.ui.components import Component
from django.utils.safestring import mark_safe
from django.core.cache import cache
from wagtail.coreutils import make_wagtail_template_fragment_key
from django.utils.html import format_html
from django.templatetags.static import static
from wagtail.admin.site_summary import SummaryItem
from wagtail.models import Page

from taggit.models import Tag

from blogpages.models import Author


@register_snippet
class TagSnippetViewSet(SnippetViewSet):
    model = Tag
    icon = "tag"
    add_to_admin_menu = True
    menu_label = "Tags"
    menu_order = 200
    list_display = ["name", "slug"]
    search_fields = ("name",)
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
    ]

@register_snippet
class AuthorSnippet(SnippetViewSet):
    model = Author
    add_to_admin_menu = False

@hooks.register('after_publish_page')
def delete_all_cache(request,page):
    # Email the author when their page is published.
    # Delete all your cache when a page is published.
    # Do whatever you want
    cache.clear()
    # print("Page is", page, page.id)
    # print("This is running after the page is published")

@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/admin_theme.css'))

class WelcomePanel(Component):
    order = 10
    template_name = "panels/welcome_panel.html"

# This is the second way if you do not us a template for admin panel customization
    # def render_html(self, parent_context):
    #     return mark_safe("""
            # <div style='background-color: black; color: white; padding:10px'>
            #     <h2 style='color:white'>Welcome to the admin!</h2>
            #     <p style='color: white'>This is a custom panel.</p>
            # </div>
    #      """)
    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context ['request'] = parent_context['request']
        # context ['username'] = parent_context['request'].user.username <- another way to pass it to the HTML page.
        return context

    class Media:
        css = {
            'all': ('css/welcome_panel.css', )
        }
        js = ('js/welcome_panel.js', )
    
@hooks.register('construct_homepage_panels')
def any_function_name_here(request, panels):
    panels.append(WelcomePanel())

class NewSummaryItem(SummaryItem):
    order = 200
    template_name = "panels/new_summary_item.html"

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context['purchases'] = 1000
        return context
    
class UnpublishedPages(SummaryItem):
    order = 400
    template_name = "panels/unpublished_pages.html"

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context['total'] = Page.objects.all().filter(live=False).count()
        return context

@hooks.register('construct_homepage_summary_items')
def summary_items(request, items):
    items.append(
        NewSummaryItem(request)
    )
    items.append(
        UnpublishedPages(request)
    )