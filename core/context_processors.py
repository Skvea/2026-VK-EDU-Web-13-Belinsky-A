from core.models import Profile
from questions.models import Tag


def sidebar(request):
    try:
        popular_tags = list(Tag.objects.popular()[:8])
    except Exception:
        popular_tags = []

    try:
        best_members = list(Profile.objects.select_related('user').order_by('-id')[:5])
    except Exception:
        best_members = []

    return {
        'popular_tags': popular_tags,
        'best_members': best_members,
    }
