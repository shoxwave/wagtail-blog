from django.db import models
from django.core.exceptions import ValidationError

from wagtail.models import Page, Orderable
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel, FieldRowPanel, HelpPanel, MultipleChooserPanel, TitleFieldPanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model
from wagtail.documents import get_document_model

from modelcluster.fields import ParentalKey

class HomePageGalleryImage(Orderable):
    page = ParentalKey('home.HomePage', related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ForeignKey(
        get_image_model(), #'wagtailimages.Image' <- can be used instead with the default wagtail images.
        blank=False,
        null=True,
        on_delete=models.CASCADE,
        related_name='+',
    )

    # TODO: Create an API connection with the Orderable
    # api_fields = [
    #     #APIField('')
    # ]


    # caption = models.CharField(max_length=100, blank=True, null=True)

    # panels = [
    #     FieldPanel('caption'),
    #     ImageChooserPanel('image'),
    # ]

class HomePage(Page):
    # add in here the template name and count
    template = "home/home_page.html"
    max_count=1

    subtitle = models.CharField(max_length=100, blank=True, null=True)
    body = RichTextField(blank=True)

    image = models.ForeignKey(
        get_image_model(), #'wagtailimages.Image' <- can be used instead with the default wagtail images.
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    custom_document = models.ForeignKey(
        get_document_model(), # 'wagtaildocs.Document' can be used instead with the default wagtail
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    cta_url = models.ForeignKey(
        'wagtailcore.Page',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    cta_external_url = models.URLField(blank=True, null=True)

    content_panels = Page.content_panels + [

        # PageChooserPanel(
        #     'cta_url',
        #     'blogpages.BlogDetail',
        #     help_text='Select the appropriate blog page.',
        #     heading='Blog Page Selection' 
        # ),

    # The MultipleChooserPanel uses InlinePanel within it but this is an example of an InlinePanel
        # InlinePanel(
        #     'gallery_images',
        #     label="Gallery images",
        #     min_num=2,
        #     max_num=4,
        # )

        MultiFieldPanel(
            [
                HelpPanel(
                    heading="Note:",
                    content="<strong>Help Panel</strong><p>Help text goes here</p>",
                ),
                TitleFieldPanel(
                    'subtitle', 
                    help_text = 'The subtitle will appear below the title.',
                    placeholder='Enter your subtitle here'
                ),
                MultipleChooserPanel(
                    'gallery_images',
                    label="Gallery Images",
                    min_num=2,
                    max_num=4,
                    chooser_field_name="image",
                    # icon='code', #<- This is just an example of changing the dropdown icon
                ),
                FieldRowPanel(
                    [
                        PageChooserPanel(
                            'cta_url',
                            'blogpages.BlogDetail',
                            help_text='Select the appropriate blog page.',
                            heading='Blog Page Selection',
                            classname='col6',
                        ),
                        FieldPanel(
                            'cta_external_url',
                            help_text='Enter the external URL',
                            heading='External URL',
                            classname='col6',
                        ),
                    ],
                    help_text='Select a page or enter a URL',
                    heading = "Call to action URLs",
                ),
            ],
            heading = "MultiFieldPanel Demo",
            classname = "collapsed",
            help_text='Random help text',
        )
        # FieldPanel('subtitle'), #,read_only= True if you want to make a panel read only.
        # FieldPanel('cta_url'),
        # FieldPanel('cta_external_url'),
        # FieldPanel('body'),
        # FieldPanel('image'),
        # FieldPanel('custom_document'),
    ]

    def get_cta_url(self):
        if self.cta_url:
            return self.cta_url.url
        elif self.cta_external_url:
            return self.cta_external_url
        else:
            return None

    def clean(self):
        super().clean()

        if self.cta_url and self.cta_external_url:
            raise ValidationError( {
                'cta_url': 'You can only have one CTA URL',
                'cta_external_url': 'You can only have one CTA URL',
            })