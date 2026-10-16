from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categoria, HistoricoTarefa, Notificacao, Subtarefa, Tarefa, Usuario
from .serializers import (
    CategoriaSerializer,
    HistoricoTarefaSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    NotificacaoSerializer,
    SubtarefaSerializer,
    TarefaSerializer,
    UsuarioSerializer,
)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        description="Autentica o usuário e retorna um token de acesso.",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if usuario is None:
            return Response(
                {"detail": "Usuário ou senha inválidos."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=usuario)
        return Response(
            {
                "token": token.key,
                "nome": usuario.nome,
                "email": usuario.email,
            }
        )


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


@extend_schema_view(
    list=extend_schema(
        description="Lista tarefas com filtros opcionais por status, prioridade, "
        "categoria, intervalo de prazo e atraso.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtra pelo status da tarefa.",
            ),
            OpenApiParameter(
                name="prioridade",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[value for value, _ in Tarefa.Prioridade.choices],
                description="Filtra pela prioridade da tarefa.",
            ),
            OpenApiParameter(
                name="categoria",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtra pelo ID da categoria.",
            ),
            OpenApiParameter(
                name="prazo_de",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Inclui tarefas com prazo nesta data ou posterior (YYYY-MM-DD).",
            ),
            OpenApiParameter(
                name="prazo_ate",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Inclui tarefas com prazo nesta data ou anterior (YYYY-MM-DD).",
            ),
            OpenApiParameter(
                name="atrasada",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtra tarefas atrasadas (true) ou não atrasadas (false).",
            ),
        ],
    )
)
class TarefaViewSet(viewsets.ModelViewSet):
    queryset = Tarefa.objects.all()
    serializer_class = TarefaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "descricao"]
    ordering_fields = ["titulo", "status", "prioridade", "prazo", "data_criacao"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        for field in ("status", "prioridade"):
            value = params.get(field)
            if value is not None:
                if field == "prioridade":
                    value = serializers.ChoiceField(
                        choices=Tarefa.Prioridade.choices
                    ).run_validation(value)
                queryset = queryset.filter(**{field: value})

        categoria = params.get("categoria")
        if categoria is not None:
            categoria_id = serializers.IntegerField().run_validation(categoria)
            queryset = queryset.filter(categoria_id=categoria_id)

        for param, lookup in (
            ("prazo_de", "prazo__date__gte"),
            ("prazo_ate", "prazo__date__lte"),
        ):
            value = params.get(param)
            if value is not None:
                date = serializers.DateField().run_validation(value)
                queryset = queryset.filter(**{lookup: date})

        atrasada = params.get("atrasada")
        if atrasada is not None:
            is_overdue = serializers.BooleanField().run_validation(atrasada)
            if is_overdue:
                queryset = queryset.filter(prazo__lt=timezone.now())
            else:
                queryset = queryset.filter(
                    Q(prazo__isnull=True) | Q(prazo__gte=timezone.now())
                )

        return queryset

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class SubtarefaViewSet(viewsets.ModelViewSet):
    queryset = Subtarefa.objects.all()
    serializer_class = SubtarefaSerializer


class NotificacaoViewSet(viewsets.ModelViewSet):
    queryset = Notificacao.objects.all()
    serializer_class = NotificacaoSerializer


class HistoricoTarefaViewSet(viewsets.ModelViewSet):
    queryset = HistoricoTarefa.objects.all()
    serializer_class = HistoricoTarefaSerializer
