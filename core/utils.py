from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    """Return the requested page of objects_list.

    Invalid ?page= values fall back to defaults: a non-integer gives the first
    page, a number out of range gives the first (below 1) or the last page.
    The page gets an `elided_range` attribute for the paginator template.
    """
    try:
        per_page = int(per_page)
    except (TypeError, ValueError):
        per_page = 10
    if per_page < 1:
        per_page = 10

    paginator = Paginator(objects_list, per_page)
    number = request.GET.get('page', 1)
    try:
        page = paginator.page(number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        try:
            below_first = int(number) < 1
        except (TypeError, ValueError):
            below_first = True
        page = paginator.page(1 if below_first else paginator.num_pages)

    page.elided_range = list(
        paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)
    )
    return page
