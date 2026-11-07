POPULAR_TAGS = ['perl', 'python', 'TechnoPark', 'MySQL', 'django', 'Mail.Ru', 'Voloshin', 'FireFox']
BEST_MEMBERS = ['Mr.Freeman', 'Dr.House', 'Bender', 'Queen Victoria', 'V.Pupkin']


def sidebar(request):
    return {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS,
    }
