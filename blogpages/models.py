from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation
from django.http import JsonResponse

from wagtail.models import Page, DraftStateMixin, RevisionMixin, LockableMixin, PreviewableMixin, TranslatableMixin, BootstrapTranslatableMixin
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, PublishingPanel
from wagtail.images import get_image_model
from wagtail import blocks #<- Wagtail blocks
from blocks import blocks as custom_blocks #<-Custom version of Wagtail Blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.search import index
from wagtail.contrib.routable_page.models import RoutablePageMixin, path, re_path
from wagtail.api import APIField
from rest_framework.fields import Field
from wagtail.templatetags.wagtailcore_tags import richtext

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

class BlogIndex(RoutablePageMixin,Page):
    # A listing page of all child pages

    template = 'blogpages/blog_index_page.html'
    max_count = 1
    parent_page_types = ['home.HomePage']
    subpage_types = ['blogpages.BlogDetail']

    subtitle = models.CharField(max_length=100, blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('body'),
    ]

    # @path('')
    # def default_blog_page(self, request):
    #     course_name = "The Ultimate Wagtail Developers Course"

    #     return self.render(
    #         request,
    #         context_overrides={
    #             'course_name' : course_name
    #         }
    #     )

    def get_sitemap_urls(self, request=None):
        sitemap = super().get_sitemap_urls(request)
        last_mod =BlogDetail.objects.live().order_by('-first_published_at').first()
        sitemap.append({
            'location': self.get_full_url(request) + self.reverse_subpage("all"),
            'lastmod': (last_mod.last_published_at or last_mod.latest_revision_created_at),
        })
        sitemap.append({
            'location': self.get_full_url(request) + self.reverse_subpage("tag", args=["wagtail"]),
            # 'lastmod': (last_mod.last_published_at or last_mod.latest_revision_created_at),
        })
        sitemap.append({
            'location': self.get_full_url(request) + self.reverse_subpage("api", args=["2024"]),
            # 'lastmod': (last_mod.last_published_at or last_mod.latest_revision_created_at),
        })
        return sitemap

    @path('all/', name='all')
    def all_blog_posts(self,request):
        posts = BlogDetail.objects.live().public()

        return self.render(
            request,
            context_overrides={
                'posts': posts
            },
            template='blogpages/blog_all_page.html'
        )
    
    # /blog/tag/{tagName}/
    @path('tag/<str:tag>/', name='tags')
    @path('tags/<str:tag>/', name='tag')
    def blog_posts_by_tag(self, request, tag = None):
        posts = BlogDetail.objects.live().public().filter(tags__name=tag)

        if not tag:
            ... # redirect in here

        return self.render(
            request,
            context_overrides={
                'posts': posts,
                'tag': tag,
            },
            template='blogpages/blog_tag_page.html'
        )
    
    #/blog/api/2024/
    # re_path, return a jsonresponse
    @re_path(r'^api/(\d+)/$', name='api')
    def api_response(self, request, year):
        posts = BlogDetail.objects.live().public().filter(first_published_at__year=year)
        return JsonResponse({
            'year': year,
            'posts': list(posts.values('title', 'first_published_at'))
        })


    def get_context(self, request):
        context = super().get_context(request)
        context['blogpages'] = BlogDetail.objects.live().public()
        return context
    
class BlogPageTags(TaggedItemBase):
    content_object = ParentalKey(
        'blogpages.BlogDetail',
        related_name='tagged_items',
        on_delete=models.CASCADE,
        )

class AuthorSerializer(Field):
    def to_representation(self, value):
        return {
            'name': value.name,
            'bio': value.bio,
            'anything': 'anything more in here'
        }
    
class ImageSerializer(Field):
    def to_representation(self, value):
        return {
            "original":{
                'url': value.file.url,
                'width': value.width,
                'height': value.height,
            },
            "thumbnail": {
                'url': value.get_rendition('max-165x165').url,
                'width': value.get_rendition('max-165x165').width,
                'height': value.get_rendition('max-165x165').height,
            },
            "small": {
                'url': value.get_rendition('max-300x300').url,
                'width': value.get_rendition('max-300x300').width,
                'height': value.get_rendition('max-300x300').height,
            },
            "medium": {
                'url': value.get_rendition('max-700x700').url,
                'width': value.get_rendition('max-700x700').width,
                'height': value.get_rendition('max-700x700').height,
            }
        }

class RichTextFieldSerializer(Field):
    def to_representation(self,value):
        return richtext(value)


class BlogDetail(Page):
    # A listing page of all child pages

    # password_required_template = 'blogpages/password_in_here_file.html' <-If you want to now use the default template we created in base.py
    template = 'blogpages/blog_detail_page.html'
    parent_page_types = ['blogpages.BlogIndex']
    subpage_types = []

    subtitle = models.CharField(max_length=100, blank=True)
    tags = ClusterTaggableManager(through=BlogPageTags, blank=True);
    author = models.ForeignKey(
        'blogpages.Author',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    intro = RichTextField(blank=True)

    body = StreamField(
        [   
            # ('doc', DocumentChooserBlock(
            #     template="blocks/doc_block.html"
            # )), <- example if you want to use a template
            ('info', custom_blocks.InfoBlock()),
            ('faq', custom_blocks.FAQListBlock()),
            ('text', custom_blocks.TextBlock()),
            ('carousel', custom_blocks.CarouselBlock()),
            ('image', custom_blocks.ImageBlock()),
            ('doc', DocumentChooserBlock(
                group = "Standalone blocks"
            )),
            ('page', custom_blocks.CustomPageChooserBlock(
                # group = "Standalone blocks"
            )),
            ('author', SnippetChooserBlock('blogpages.Author')),
            ('call_to_action_1', custom_blocks.CallToAction1())
        ],
        block_counts={
            # 'page': {'min_num': 1},
            # 'text': {'min_num': 1},
            # 'image': {'min_num': 1, 'max_num': 1},
        },
        # use_json_field=True, #<- No longer required in 6.0 upgrade. I am on 6.2.
        blank=True,
        null=True,
    )

    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    def custom_content(self):
        return"This is custom content"

    content_panels = Page.content_panels + [
        FieldPanel('author'),
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('subtitle'),
        FieldPanel('tags'),
        FieldPanel('image'),
    ]

    api_fields = [
        APIField('intro', serializer=RichTextFieldSerializer()),
        APIField('subtitle'),
        APIField('author', serializer=AuthorSerializer()),
        APIField('image', serializer=ImageSerializer()),
        APIField('body'),
        APIField('custom_content'),
        APIField('tags'),
    ]

    def clean(self):
        super().clean()

        errors = {}

        if 'blog' in self.title.lower():
            errors['title'] = "Title cannot have the word 'Blog'"

        if 'blog' in self.subtitle.lower():
            errors['subtitle'] = "Subtitle cannot have the word 'Blog'"

        if 'blog' in self.slug.lower():
            errors['slug'] = "Slug cannot have the word 'Blog'"

        if errors:
            raise ValidationError(errors)

# Author model for SnippetChooserBlock and ForeignKey's to the Author model.
# Panels go in the SnippetViewSEt in wagtail_hooks.py

  
class Author(
    TranslatableMixin,
    PreviewableMixin,
    LockableMixin,
    DraftStateMixin,
    RevisionMixin,
    index.Indexed,
    models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    revisions = GenericRelation("wagtailcore.Revision", related_query_name="author")

    panels = [
        FieldPanel("name"),
        FieldPanel("bio"),
        PublishingPanel(),
    ]

    search_fields = [
        index.FilterField('name'),
        index.SearchField('name'),
        index.AutocompleteField('name'),
    ]

    def __str__(self):
        return self.name
    
    @property
    def preview_modes(self):
        return PreviewableMixin.DEFAULT_PREVIEW_MODES + [
            ("dark_mode", "Dark Mode")
        ]
    
    def get_preview_template(self, request, mode_name):
        templates = {
            "": "includes/author.html", # Default
            "dark_mode": "includes/author_dark_mode.html"
        }
        return templates.get(mode_name, templates[""])
    
    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        context['warning'] = "This is a preview"
        return context
    
    class Meta(TranslatableMixin.Meta):
        permissions = [
            ("can_edit_autor_name", "Can edit author name")
        ]