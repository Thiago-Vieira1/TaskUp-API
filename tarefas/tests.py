from datetime import timedelta

from django.urls import reverse
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Categoria, HistoricoTarefa, Notificacao, Subtarefa, Tarefa, Usuario
from .serializers import UsuarioSerializer


class TaskupModelTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="thiago",
            email="thiago@example.com",
            password="senha-segura",
            nome="Thiago",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)
        self.categoria = Categoria.objects.create(
            nome="Trabalho",
            cor="#123456",
            usuario=self.usuario,
        )
        self.tarefa = Tarefa.objects.create(
            titulo="Revisar entrega",
            descricao="Revisar a entrega do projeto.",
            status="pendente",
            usuario=self.usuario,
            categoria=self.categoria,
        )
        self.tarefa.prioridade = Tarefa.Prioridade.ALTA
        self.tarefa.prazo = timezone.now() + timedelta(days=3)
        self.tarefa.save()

    def test_usuario_uses_hashed_password(self):
        self.assertTrue(self.usuario.check_password("senha-segura"))
        self.assertEqual(self.usuario.nome, "Thiago")

    def test_usuario_serializer_hashes_password_and_does_not_return_it(self):
        serializer = UsuarioSerializer(
            data={
                "username": "novo-usuario",
                "password": "outra-senha-segura",
                "nome": "Novo usuário",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        usuario = serializer.save()

        self.assertTrue(usuario.check_password("outra-senha-segura"))
        self.assertNotIn("password", serializer.data)

    def test_tarefa_relations_and_subtask_defaults(self):
        subtarefa = Subtarefa.objects.create(
            tarefa=self.tarefa,
            descricao="Conferir os testes",
        )

        self.assertEqual(self.tarefa.usuario, self.usuario)
        self.assertEqual(self.tarefa.categoria, self.categoria)
        self.assertEqual(self.tarefa.prioridade, Tarefa.Prioridade.ALTA)
        self.assertIsNotNone(self.tarefa.prazo)
        self.assertFalse(subtarefa.concluida)
        self.assertEqual(subtarefa.ordem, 0)

    def test_tarefa_filters_by_priority_and_category(self):
        Tarefa.objects.create(
            titulo="Comprar café",
            descricao="",
            status="pendente",
            usuario=self.usuario,
            categoria=self.categoria,
            prioridade=Tarefa.Prioridade.BAIXA,
        )

        response = self.client.get(
            reverse("tarefa-list"),
            {"prioridade": "alta", "categoria": self.categoria.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.tarefa.pk])

    def test_tarefa_can_search_and_order_by_deadline(self):
        mais_tarde = Tarefa.objects.create(
            titulo="Revisar apresentação",
            descricao="",
            status="pendente",
            usuario=self.usuario,
            categoria=self.categoria,
            prazo=timezone.now() + timedelta(days=5),
        )

        response = self.client.get(
            reverse("tarefa-list"),
            {"search": "Revisar", "ordering": "prazo"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data],
            [self.tarefa.pk, mais_tarde.pk],
        )

    def test_tarefa_filters_by_deadline_range_and_overdue(self):
        atrasada = Tarefa.objects.create(
            titulo="Enviar relatório",
            descricao="",
            status="pendente",
            usuario=self.usuario,
            categoria=self.categoria,
            prazo=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(
            reverse("tarefa-list"),
            {
                "prazo_de": (timezone.now() - timedelta(days=2)).date().isoformat(),
                "prazo_ate": timezone.now().date().isoformat(),
                "atrasada": "true",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [atrasada.pk])

    def test_tarefa_rejects_invalid_filter_values(self):
        response = self.client.get(
            reverse("tarefa-list"),
            {"prazo_de": "data-invalida"},
        )

        self.assertEqual(response.status_code, 400)

    def test_tarefa_rejects_invalid_priority(self):
        response = self.client.get(
            reverse("tarefa-list"),
            {"prioridade": "urgente"},
        )

        self.assertEqual(response.status_code, 400)

    def test_notification_and_task_history(self):
        notificacao = Notificacao.objects.create(
            tarefa=self.tarefa,
            data_execucao=timezone.now(),
        )
        historico = HistoricoTarefa.objects.create(
            tarefa=self.tarefa,
            usuario=self.usuario,
            campo_alterado="status",
            valor_antigo="pendente",
            valor_novo="concluida",
        )

        self.assertFalse(notificacao.enviada)
        self.assertEqual(self.tarefa.notificacoes.get(), notificacao)
        self.assertEqual(self.tarefa.historico.get(), historico)


class ApiDocumentationTests(TestCase):
    def test_openapi_schema_documents_task_filters(self):
        response = self.client.get(reverse("schema"))

        self.assertEqual(response.status_code, 200)
        task_parameters = response.data["paths"]["/api/tarefas/"]["get"]["parameters"]
        documented_parameters = {parameter["name"] for parameter in task_parameters}
        self.assertTrue(
            {
                "status",
                "prioridade",
                "categoria",
                "prazo_de",
                "prazo_ate",
                "atrasada",
                "search",
                "ordering",
            }.issubset(documented_parameters)
        )

    def test_swagger_and_redoc_pages_are_available(self):
        swagger_response = self.client.get(reverse("swagger-ui"))
        redoc_response = self.client.get(reverse("redoc"))

        self.assertEqual(swagger_response.status_code, 200)
        self.assertEqual(redoc_response.status_code, 200)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="thiago",
            email="thiago@example.com",
            password="senha-segura",
            nome="Thiago",
        )
        self.login_url = reverse("login")

    def test_login_returns_token_and_user_details(self):
        response = self.client.post(
            self.login_url,
            {"username": "thiago", "password": "senha-segura"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nome"], "Thiago")
        self.assertEqual(response.data["email"], "thiago@example.com")
        self.assertEqual(
            response.data["token"],
            Token.objects.get(user=self.usuario).key,
        )

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {"username": "thiago", "password": "senha-incorreta"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn("token", response.data)

    def test_api_routes_require_authentication(self):
        response = self.client.get(reverse("tarefa-list"))

        self.assertEqual(response.status_code, 401)

    def test_token_authentication_grants_access_to_api(self):
        token = Token.objects.create(user=self.usuario)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = client.get(reverse("tarefa-list"))

        self.assertEqual(response.status_code, 200)
