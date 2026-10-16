from django.contrib.auth.models import AbstractUser
from django.db import models


class TaskupModel(models.Model):
    timestamp_create = models.DateTimeField(auto_now_add=True)
    timestamp_update = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Usuario(AbstractUser, TaskupModel):
    nome = models.CharField(max_length=150)
    criado_em = models.DateTimeField(auto_now_add=True)


class Categoria(TaskupModel):
    nome = models.CharField(max_length=100)
    cor = models.CharField(max_length=30)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="categorias",
    )


class Tarefa(TaskupModel):
    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Média"
        ALTA = "alta", "Alta"

    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    status = models.CharField(max_length=30)
    data_criacao = models.DateTimeField(auto_now_add=True)
    prazo = models.DateTimeField(blank=True, null=True)
    prioridade = models.CharField(
        max_length=5,
        choices=Prioridade.choices,
        default=Prioridade.MEDIA,
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="tarefas",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="tarefas",
        blank=True, null=True
    )


class Subtarefa(TaskupModel):
    tarefa = models.ForeignKey(
        Tarefa,
        on_delete=models.CASCADE,
        related_name="subtarefas",
    )
    descricao = models.CharField(max_length=255)
    concluida = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(default=0)


class Notificacao(TaskupModel):
    tarefa = models.ForeignKey(
        Tarefa,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    data_execucao = models.DateTimeField()
    enviada = models.BooleanField(default=False)


class HistoricoTarefa(TaskupModel):
    tarefa = models.ForeignKey(
        Tarefa,
        on_delete=models.CASCADE,
        related_name="historico",
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="historico_tarefas",
    )
    campo_alterado = models.CharField(max_length=100)
    valor_antigo = models.TextField(blank=True)
    valor_novo = models.TextField(blank=True)
    alterado_em = models.DateTimeField(auto_now_add=True)
