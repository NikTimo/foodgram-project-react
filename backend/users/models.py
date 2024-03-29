from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint, CheckConstraint, Q, F

User = get_user_model()


class Subscribe(models.Model):
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Подписчик', related_name='follower'

    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор', related_name='following', unique=False
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['subscriber', 'author'],
                name='Follower-author Unique'
            ),
            CheckConstraint(
                check=~Q(subscriber=F('author')),
                name='No self subscriptions'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.subscriber} подписался на {self.author}'
