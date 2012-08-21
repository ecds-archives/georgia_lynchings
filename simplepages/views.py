from django.shortcuts import render, get_object_or_404

from georgia_lynchings.simplepages.models import Page

def view_page(request, slug):
    """
    Returns a page object.
    """
    page = get_object_or_404(Page, slug=slug)
    return render(request, 'simplepages/page.html', {
        'page': page,
    } )