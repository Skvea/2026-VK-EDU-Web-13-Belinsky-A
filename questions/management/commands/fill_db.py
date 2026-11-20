import random
import time
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag


class Command(BaseCommand):
    help = 'Fill database with realistic test data using ratio factor'

    def add_arguments(self, parser):
        parser.add_argument(
            'ratio',
            type=int,
            nargs='?',
            default=10,
            help='Scale ratio',
        )

    def handle(self, *args, **options):
        ratio = options['ratio']
        if ratio < 1:
            self.stdout.write(self.style.ERROR('Ratio must be >= 1'))
            return

        num_users = ratio
        num_questions = ratio * 10
        num_answers = ratio * 100
        num_tags = ratio
        num_likes = ratio * 200
        num_qlikes = num_likes // 2
        num_alikes = num_likes - num_qlikes

        self.stdout.write(self.style.SUCCESS(
            f'Starting database population with ratio = {ratio}\n'
            f'Users: {num_users}, Questions: {num_questions}, Answers: {num_answers}, '
            f'Tags: {num_tags}, Likes: {num_likes}'
        ))

        start_time = time.time()
        fake = Faker('en_US')
        run_id = int(time.time())

        titles_pool = [fake.sentence(nb_words=random.randint(5, 9)).rstrip('.') + '?' for _ in range(500)]
        texts_pool = [fake.paragraph(nb_sentences=random.randint(3, 6)) for _ in range(500)]
        answer_pool = [fake.paragraph(nb_sentences=random.randint(2, 5)) for _ in range(500)]
        names_pool = [fake.first_name() for _ in range(300)]

        hashed_pwd = make_password('testpass123')
        batch_size = 5000

        existing_user_count = User.objects.count()
        users_to_create = []
        for i in range(num_users):
            username = f'user_{run_id}_{existing_user_count + i}'
            email = f'{username}@example.com'
            first_name = random.choice(names_pool)
            users_to_create.append(User(
                username=username,
                email=email,
                first_name=first_name,
                password=hashed_pwd,
            ))
            if len(users_to_create) >= batch_size:
                User.objects.bulk_create(users_to_create, batch_size=batch_size)
                users_to_create = []
        if users_to_create:
            User.objects.bulk_create(users_to_create, batch_size=batch_size)

        new_users = list(User.objects.filter(username__startswith=f'user_{run_id}_').values_list('id', flat=True))
        all_user_ids = new_users if new_users else list(User.objects.values_list('id', flat=True))

        profiles_to_create = [
            Profile(user_id=uid, nickname=f'{random.choice(names_pool)}_{uid}')
            for uid in new_users
        ]
        Profile.objects.bulk_create(profiles_to_create, batch_size=batch_size, ignore_conflicts=True)

        tags_to_create = []
        for i in range(num_tags):
            word = fake.word().lower()
            tag_name = f'{word}_{i}' if num_tags > 500 else word
            tags_to_create.append(Tag(name=tag_name[:50]))
            if len(tags_to_create) >= batch_size:
                Tag.objects.bulk_create(tags_to_create, batch_size=batch_size, ignore_conflicts=True)
                tags_to_create = []
        if tags_to_create:
            Tag.objects.bulk_create(tags_to_create, batch_size=batch_size, ignore_conflicts=True)

        all_tag_ids = list(Tag.objects.values_list('id', flat=True))

        max_q_id_before = Question.objects.order_by('-id').values_list('id', flat=True).first() or 0
        questions_to_create = []
        for i in range(num_questions):
            questions_to_create.append(Question(
                title=random.choice(titles_pool),
                text=random.choice(texts_pool),
                author_id=random.choice(all_user_ids),
                rating=0,
                answers_count=0,
            ))
            if len(questions_to_create) >= batch_size:
                Question.objects.bulk_create(questions_to_create, batch_size=batch_size)
                questions_to_create = []
        if questions_to_create:
            Question.objects.bulk_create(questions_to_create, batch_size=batch_size)

        new_question_ids = list(Question.objects.filter(id__gt=max_q_id_before).values_list('id', flat=True))

        QuestionTagThrough = Question.tags.through
        through_batch = []
        for qid in new_question_ids:
            num_q_tags = min(random.randint(1, 4), len(all_tag_ids))
            selected_tag_ids = random.sample(all_tag_ids, num_q_tags)
            for tid in selected_tag_ids:
                through_batch.append(QuestionTagThrough(question_id=qid, tag_id=tid))
                if len(through_batch) >= 10000:
                    QuestionTagThrough.objects.bulk_create(through_batch, batch_size=10000, ignore_conflicts=True)
                    through_batch = []
        if through_batch:
            QuestionTagThrough.objects.bulk_create(through_batch, batch_size=10000, ignore_conflicts=True)

        max_a_id_before = Answer.objects.order_by('-id').values_list('id', flat=True).first() or 0
        answers_to_create = []
        for i in range(num_answers):
            answers_to_create.append(Answer(
                question_id=random.choice(new_question_ids),
                author_id=random.choice(all_user_ids),
                text=random.choice(answer_pool),
                is_correct=(random.random() < 0.1),
                rating=0,
            ))
            if len(answers_to_create) >= batch_size:
                Answer.objects.bulk_create(answers_to_create, batch_size=batch_size)
                answers_to_create = []
        if answers_to_create:
            Answer.objects.bulk_create(answers_to_create, batch_size=batch_size)

        new_answer_ids = list(Answer.objects.filter(id__gt=max_a_id_before).values_list('id', flat=True))

        max_possible_qlikes = len(all_user_ids) * len(new_question_ids)
        target_qlikes = min(num_qlikes, max_possible_qlikes)
        qlikes_created = 0
        seen_qlikes = set()
        qlikes_batch = []

        while qlikes_created < target_qlikes:
            u = random.choice(all_user_ids)
            q = random.choice(new_question_ids)
            pair = (u, q)
            if pair in seen_qlikes:
                continue
            seen_qlikes.add(pair)
            qlikes_batch.append(QuestionLike(
                user_id=u,
                question_id=q,
                value=random.choice([1, 1, 1, -1]),
            ))
            qlikes_created += 1
            if len(qlikes_batch) >= 10000:
                QuestionLike.objects.bulk_create(qlikes_batch, batch_size=10000, ignore_conflicts=True)
                qlikes_batch = []
        if qlikes_batch:
            QuestionLike.objects.bulk_create(qlikes_batch, batch_size=10000, ignore_conflicts=True)
        del seen_qlikes

        max_possible_alikes = len(all_user_ids) * len(new_answer_ids)
        target_alikes = min(num_alikes, max_possible_alikes)
        alikes_created = 0
        seen_alikes = set()
        alikes_batch = []

        while alikes_created < target_alikes:
            u = random.choice(all_user_ids)
            a = random.choice(new_answer_ids)
            pair = (u, a)
            if pair in seen_alikes:
                continue
            seen_alikes.add(pair)
            alikes_batch.append(AnswerLike(
                user_id=u,
                answer_id=a,
                value=random.choice([1, 1, 1, -1]),
            ))
            alikes_created += 1
            if len(alikes_batch) >= 10000:
                AnswerLike.objects.bulk_create(alikes_batch, batch_size=10000, ignore_conflicts=True)
                alikes_batch = []
        if alikes_batch:
            AnswerLike.objects.bulk_create(alikes_batch, batch_size=10000, ignore_conflicts=True)
        del seen_alikes

        with connection.cursor() as cursor:
            db_vendor = connection.vendor
            if db_vendor == 'postgresql':
                cursor.execute("""
                    UPDATE questions_question q
                    SET answers_count = COALESCE(sub.cnt, 0)
                    FROM (
                        SELECT question_id, COUNT(*) AS cnt
                        FROM questions_answer
                        GROUP BY question_id
                    ) sub
                    WHERE q.id = sub.question_id;
                """)
                cursor.execute("""
                    UPDATE questions_question q
                    SET rating = COALESCE(sub.total, 0)
                    FROM (
                        SELECT question_id, SUM(value) AS total
                        FROM questions_questionlike
                        GROUP BY question_id
                    ) sub
                    WHERE q.id = sub.question_id;
                """)
                cursor.execute("""
                    UPDATE questions_answer a
                    SET rating = COALESCE(sub.total, 0)
                    FROM (
                        SELECT answer_id, SUM(value) AS total
                        FROM questions_answerlike
                        GROUP BY answer_id
                    ) sub
                    WHERE a.id = sub.answer_id;
                """)
            elif db_vendor == 'mysql':
                cursor.execute("""
                    UPDATE questions_question q
                    JOIN (
                        SELECT question_id, COUNT(*) AS cnt
                        FROM questions_answer
                        GROUP BY question_id
                    ) sub ON q.id = sub.question_id
                    SET q.answers_count = sub.cnt;
                """)
                cursor.execute("""
                    UPDATE questions_question q
                    JOIN (
                        SELECT question_id, SUM(value) AS total
                        FROM questions_questionlike
                        GROUP BY question_id
                    ) sub ON q.id = sub.question_id
                    SET q.rating = sub.total;
                """)
                cursor.execute("""
                    UPDATE questions_answer a
                    JOIN (
                        SELECT answer_id, SUM(value) AS total
                        FROM questions_answerlike
                        GROUP BY answer_id
                    ) sub ON a.id = sub.answer_id
                    SET a.rating = sub.total;
                """)
            else:
                cursor.execute("""
                    UPDATE questions_question
                    SET answers_count = COALESCE(
                        (SELECT COUNT(*) FROM questions_answer WHERE questions_answer.question_id = questions_question.id),
                        0
                    ),
                    rating = COALESCE(
                        (SELECT SUM(value) FROM questions_questionlike WHERE questions_questionlike.question_id = questions_question.id),
                        0
                    );
                """)
                cursor.execute("""
                    UPDATE questions_answer
                    SET rating = COALESCE(
                        (SELECT SUM(value) FROM questions_answerlike WHERE questions_answerlike.answer_id = questions_answer.id),
                        0
                    );
                """)

        total_time = round(time.time() - start_time, 2)
        self.stdout.write(self.style.SUCCESS(
            f'Database population finished in {total_time}s'
        ))
