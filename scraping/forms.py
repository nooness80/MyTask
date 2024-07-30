from django import forms

class ImageScrapeForm(forms.Form):
    search_term = forms.CharField(max_length=100, label='Search Term')
    number_of_images = forms.IntegerField(min_value=1, max_value=100, label='Number of Images')
